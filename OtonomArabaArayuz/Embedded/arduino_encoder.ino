/*
  Otonom Araba Encoder ve IMU (MPU6050) Okuma
  
  Bu kod, iki adet motor encoderını ve MPU6050 sensörünü okur.
  Verileri Seri Port üzerinden gönderir.
  Format: SPEED:<hız>;DIST:<mesafe>;ANGLE:<açı>\n
  
  Bağlantılar:
  - Encoder A Pin -> Digital 2 (Interrupt)
  - Encoder B Pin -> Digital 3 (Interrupt)
  - MPU6050 SDA -> A4
  - MPU6050 SCL -> A5
*/

#include <Wire.h>

const int encoderPinA = 2; // Interrupt Pin
const int encoderPinB = 3;
const int MPU_ADDR = 0x68;

volatile long encoderCount = 0;
unsigned long lastTime = 0;
const int interval = 100; // 100ms de bir veri gönder

// Tekerlek parametreleri (Kendi aracınıza göre düzenleyin)
const float whellDiameter = 6.5; // cm
const int countsPerRevolution = 20; // Encoderin bir turdaki adım sayısı

// IMU Değişkenleri
float yaw = 0;
unsigned long lastImuTime = 0;
float gyroZOffset = 0;

void setup() {
  Serial.begin(9600);
  
  // Encoder Setup
  pinMode(encoderPinA, INPUT_PULLUP);
  pinMode(encoderPinB, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(encoderPinA), readEncoder, RISING);
  
  // MPU6050 Setup
  Wire.begin();
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(0x6B); // PWR_MGMT_1 register
  Wire.write(0);    // Uyandır
  Wire.endTransmission(true);
  
  // Basit Kalibrasyon (İlk 2 saniye hareketsiz kalmalı)
  Serial.println("IMU Kalibre ediliyor, lutfen bekleyin...");
  float sum = 0;
  for(int i=0; i<200; i++) {
    sum += readGyroZ();
    delay(10);
  }
  gyroZOffset = sum / 200.0;
  lastImuTime = millis();
}

void loop() {
  unsigned long currentTime = millis();
  
  if (currentTime - lastTime > interval) {
    // 1. Encoder Hesaplamaları
    float distance = (encoderCount / (float)countsPerRevolution) * (whellDiameter * 3.14159);
    float speed = (distance / (currentTime / 1000.0)); // Basit ortalama hız
    
    // 2. IMU Hesaplamaları (Gyro Z Entegrasyonu)
    float gyroZ = readGyroZ() - gyroZOffset;
    
    // Gürültü filtresi (Deadzone)
    if(abs(gyroZ) < 2.0) gyroZ = 0;
    
    // dt hesabı (saniye cinsinden)
    float dt = (currentTime - lastImuTime) / 1000.0;
    lastImuTime = currentTime;
    
    // Açı hesabı (Derece/sn * sn = Derece)
    yaw += gyroZ * dt;
    
    // 0-360 derece arasına normalize et
    if(yaw >= 360) yaw -= 360;
    if(yaw < 0) yaw += 360;
    
    // Veriyi Gönder
    // Format: SPEED:12.5;DIST:100.2;ANGLE:45.5
    Serial.print("SPEED:");
    Serial.print(speed);
    Serial.print(";DIST:");
    Serial.print(distance);
    Serial.print(";ANGLE:");
    Serial.println(yaw);
    
    lastTime = currentTime;
  }
}

void readEncoder() {
  if (digitalRead(encoderPinB) == LOW) {
    encoderCount++;
  } else {
    encoderCount--;
  }
}

float readGyroZ() {
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(0x47); // GYRO_ZOUT_H
  Wire.endTransmission(false);
  Wire.requestFrom(MPU_ADDR, 2, true);
  
  int16_t GyroZ = Wire.read() << 8 | Wire.read();
  // MPU6050 Varsayılan Hassasiyet: +/- 250 deg/s -> 131 LSB/deg/s
  return GyroZ / 131.0;
}
