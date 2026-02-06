/*
  Otonom Araba V6 - Ackermann Steering Version
  
  DONANIM YAPILANDIRMASI:
  -----------------------
  1. DIREKSIYON (Step Motor):
     - Pins: 3, 4, 5, 6
     - Sürücü: L298N veya ULN2003
     - Mekanik: Doğrudan Bağlantı (Direct Drive)
  
  2. SÜRÜŞ (Arka DC Motorlar):
     - Sol Motor: ENA=45 (PWM), IN1=22, IN2=23
     - Sağ Motor: ENB=44 (PWM), IN3=24, IN4=25
     - Mantık: İkisi birlikte hareket eder ( Diferansiyel yok )
  
  3. HIZ SENSÖRÜ (Encoder):
     - Pin: 11 (Tek kanal interrupt)
     - Sadece Hız ölçer, yön motor komutundan tahmin edilir.
     
  4. SONAR SENSÖRLERİ (6 Adet):
     - Ön Sağ:  Trig 26, Echo 27
     - Ön Sol:  Trig 28, Echo 29
     - Sol:     Trig 30, Echo 31
     - Arka Sol: Trig 32, Echo 33
     - Arka Sağ: Trig 34, Echo 35
     - Sağ:      Trig 36, Echo 37
     
  5. NRF24L01 (Kablosuz):
     - CE: 9, CSN: 10, MOSI: 51, MISO: 50, SCK: 52
     
  6. IMU (MPU6050):
     - SDA: 20, SCL: 21
*/

#include <Wire.h>
#include <SPI.h>
#include <nRF24L01.h>
#include <RF24.h>
#include <Stepper.h>

// --- AYARLAR ---
// Step Motor Adım Sayısı (Motorunuzun speğine göre değiştirin)
// Örn: 28BYJ-48 için 2048, NEMA17 için 200
const int STEPS_PER_REV = 200; 
// Direksiyon Limitleri (Adım cinsinden, merkezden sağa/sola max kaç adım?)
const int MAX_STEER_STEPS = 50; 

// --- NESNELER ---
RF24 radio(9, 10);
const byte address[6] = "00001";
Stepper steering(STEPS_PER_REV, 3, 5, 4, 6); // Pin sırası 3-5-4-6 (L298N/ULN2003 standart sequence için)
// Eğer motor titrer ama dönmezse: 3, 4, 5, 6 veya 3, 5, 4, 6 deneyin.

// --- PINLER ---
// Sürüş Motorları
const int ENA_L = 45; const int IN1_L = 22; const int IN2_L = 23;
const int ENB_R = 44; const int IN3_R = 24; const int IN4_R = 25;

// Encoder
const int ENC_PIN = 11;

// Sonarlar
const int SONAR_NUM = 6;
// {Trig, Echo}
const int sonarPins[SONAR_NUM][2] = {
  {26, 27}, // Ön Sağ (0)
  {28, 29}, // Ön Sol (1)
  {30, 31}, // Sol (2)
  {32, 33}, // Arka Sol (3)
  {34, 35}, // Arka Sağ (4)
  {36, 37}  // Sağ (5)
};

// IMU
const int MPU_ADDR = 0x68;

// --- DEĞİŞKENLER ---
volatile long encoderTicks = 0;
int currentSteerPosition = 0; // 0: Merkez, +: Sağ, -: Sol
int currentSpeed = 0; // -255 ile 255 arası
unsigned long lastTime = 0;
long distances[SONAR_NUM];
float heading = 0.0;
float gyroZOffset = 0.0;

// Step Motor Kontrolü için (Blocking olmaması için loop içinde minik adımlar atacağız)
int targetSteerPosition = 0; // Hedef adım

void setup() {
  Serial.begin(9600);
  
  // 1. NRF
  if (!radio.begin()) {
    Serial.println("NRF Hata!");
    while(1); 
  }
  radio.openWritingPipe(address);
  radio.openReadingPipe(1, address);
  radio.setPALevel(RF24_PA_MIN);
  radio.startListening();
  
  // 2. Motor Pinleri
  pinMode(ENA_L, OUTPUT); pinMode(IN1_L, OUTPUT); pinMode(IN2_L, OUTPUT);
  pinMode(ENB_R, OUTPUT); pinMode(IN3_R, OUTPUT); pinMode(IN4_R, OUTPUT);
  
  // 3. Encoder
  pinMode(ENC_PIN, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(ENC_PIN), countEncoder, RISING);
  
  // 4. Sonarlar
  for(int i=0; i<SONAR_NUM; i++) {
    pinMode(sonarPins[i][0], OUTPUT); 
    pinMode(sonarPins[i][1], INPUT);
  }
  
  // 5. Step Motor Hızı
  steering.setSpeed(60); // RPM
  
  // 6. IMU
  Wire.begin(); Wire.beginTransmission(MPU_ADDR);
  Wire.write(0x6B); Wire.write(0); Wire.endTransmission(true);
  
  // Gyro Kalibrasyon
  Serial.println("IMU Kalibre ediliyor...");
  float sum = 0; 
  for(int i=0; i<50; i++) { 
    sum += readGyroZ(); 
    delay(10); 
  }
  gyroZOffset = sum / 50.0;
  Serial.println("Hazir.");
}

void loop() {
  unsigned long currentTime = millis();
  float dt = (currentTime - lastTime) / 1000.0;
  
  // --- 1. KOMUT DİNLEME ---
  if (radio.available()) {
    char text[32] = "";
    radio.read(&text, sizeof(text));
    String cmd = String(text);
    cmd.trim();
    
    // Protokol: "CMD:HIZ:ACI" 
    // Örnek: "M:100:30" (Motor Hız 100, Açı 30 derece değil adım cinsinden map edilmiş)
    // Basitleştirilmiş: "DRV:Speed:Steer"
    
    if (cmd.startsWith("DRV:")) {
       parseDriveCommand(cmd);
    }
    else if (cmd == "STOP") {
      targetSteerPosition = 0; // Tekerleri düzelt
      currentSpeed = 0;
      stopMotors();
    }
  }
  
  // --- 2. SENSÖR GÖNDERİMİ (10Hz) ---
  if (currentTime - lastTime >= 100) {
    // IMU Oku ve Heading Güncelle
    float gz = readGyroZ() - gyroZOffset;
    if (abs(gz) < 2.0) gz = 0; // Gürültü filtresi
    heading += gz * dt;
    if(heading > 360) heading -= 360; 
    if(heading < 0) heading += 360;
    
    // Telemetri Paketi Hazırla
    // Yön bilgisi: Eğer ileri gidiyorsak (+), geri gidiyorsak (-)
    int direction = (currentSpeed >= 0) ? 1 : -1;
    long realTicks = encoderTicks * direction; 
    
    // Veriyi gönder
    radio.stopListening();
    
    // Paket 1: Hız ve Açı
    String p1 = "SPD:" + String(realTicks) + ";ANG:" + String(heading,1);
    char data1[32]; p1.toCharArray(data1, 32);
    radio.write(&data1, sizeof(data1));
    encoderTicks = 0; // Delta tick gönderiyoruz
    
    delay(5);
    
    // Paket 2: Ön Sensörler
    String p2 = "SNS:" + String(distances[1]) + "," + String(distances[0]) + "," + String(distances[5]);
    char data2[32]; p2.toCharArray(data2, 32);
    radio.write(&data2, sizeof(data2));
    
    radio.startListening();
    lastTime = currentTime;
  }
  
  // --- 3. FİZİKSEL EYLEMLER ---
  
  // A. Direksiyon (Non-blocking Step)
  updateSteering();
  
  // B. Sürüş Motorları
  setMotorSpeed(currentSpeed);
  
  // C. Sonar Okuma (Sırayla, sistemi kilitlemeden)
  static int sonarIdx = 0;
  readOneSonar(sonarIdx);
  sonarIdx = (sonarIdx + 1) % SONAR_NUM;
}

// --- FONKSİYONLAR ---

void parseDriveCommand(String cmd) {
  // Format: "DRV:hiz:yon"
  // DRV:150:20 (Hız 150, Direksiyon Sağa 20 adım)
  // DRV:-100:-10 (Geri 100, Direksiyon Sola 10 adım)
  
  int first = cmd.indexOf(':');
  int second = cmd.lastIndexOf(':');
  
  if(first > 0 && second > first) {
    int spd = cmd.substring(first+1, second).toInt();
    int str = cmd.substring(second+1).toInt();
    
    currentSpeed = constrain(spd, -255, 255);
    
    // Direksiyon değerini sınırla
    targetSteerPosition = constrain(str, -MAX_STEER_STEPS, MAX_STEER_STEPS);
  }
}

void updateSteering() {
  // Hedefe ulaşmak için her döngüde 1 adım at
  // Bu sayede 'delay' kullanmadan loop'un akmasını sağlarız
  
  if (currentSteerPosition < targetSteerPosition) {
    steering.step(1);
    currentSteerPosition++;
  } else if (currentSteerPosition > targetSteerPosition) {
    steering.step(-1);
    currentSteerPosition--;
  }
}

void setMotorSpeed(int speed) {
  // Sol ve Sağ motorları eşzamanlı sür
  
  if (speed > 0) {
    // İLERİ
    digitalWrite(IN1_L, HIGH); digitalWrite(IN2_L, LOW);
    digitalWrite(IN3_R, HIGH); digitalWrite(IN4_R, LOW);
  } else if (speed < 0) {
    // GERİ
    digitalWrite(IN1_L, LOW); digitalWrite(IN2_L, HIGH);
    digitalWrite(IN3_R, LOW); digitalWrite(IN4_R, HIGH);
  } else {
    // DUR
    stopMotors();
    return;
  }
  
  int pwm = abs(speed);
  // Düşük hızlarda motorun ötmemesi için minik bir ölü bölge
  if(pwm < 50) pwm = 0;
  
  analogWrite(ENA_L, pwm);
  analogWrite(ENB_R, pwm);
}

void stopMotors() {
  digitalWrite(IN1_L, LOW); digitalWrite(IN2_L, LOW); analogWrite(ENA_L, 0);
  digitalWrite(IN3_R, LOW); digitalWrite(IN4_R, LOW); analogWrite(ENB_R, 0);
}

void countEncoder() {
  encoderTicks++;
}

void readOneSonar(int idx) {
  // Tek bir senörü okur (Bloklamayı azaltmak için timeout 5ms)
  digitalWrite(sonarPins[idx][0], LOW); delayMicroseconds(2);
  digitalWrite(sonarPins[idx][0], HIGH); delayMicroseconds(10);
  digitalWrite(sonarPins[idx][0], LOW);
  
  long duration = pulseIn(sonarPins[idx][1], HIGH, 5800); // Max ~1 metre (zaman kazanmak için kısa tuttum)
  
  if (duration == 0) distances[idx] = 100; // Timeout ise uzak varsay
  else distances[idx] = duration * 0.034 / 2;
}

float readGyroZ() {
  Wire.beginTransmission(MPU_ADDR); Wire.write(0x47); Wire.endTransmission(false);
  Wire.requestFrom(MPU_ADDR, 2, true);
  int16_t GyroZ = Wire.read() << 8 | Wire.read();
  return GyroZ / 131.0;
}
