/*
  Otonom Araba - Base Station (Verici/İstasyon)
  
  Bu kod, PC'ye USB ile bağlı Arduino Uno (veya Nano) içindir.
  PC'den gelen veriyi (Serial) NRF24L01 ile arabaya (Mega) gönderir.
  Arabadan gelen veriyi NRF24L01 ile alıp PC'ye (Serial) gönderir.
  
  Bağlantılar (Uno):
  - CE   -> 9
  - CSN  -> 10
  - MOSI -> 11
  - MISO -> 12
  - SCK  -> 13
  - VCC  -> 3.3V (Önemli! 5V yakabilir)
  - GND  -> GND
  
  Gerekli Kütüphane: RF24 by TMRh20
*/

#include <SPI.h>
#include <nRF24L01.h>
#include <RF24.h>

RF24 radio(9, 10); // CE, CSN

const byte address[6] = "00001"; // İletişim adresi (Mega ile aynı olmalı)

void setup() {
  Serial.begin(9600);
  
  if (!radio.begin()) {
    Serial.println("LOG:NRF24L01 Baslatilamadi! Baglantilari kontrol edin.");
    while (1) {}
  }
  
  radio.openWritingPipe(address); // Gönderme Kanalı (Base -> Car)
  radio.openReadingPipe(1, address); // Okuma Kanalı (Car -> Base)
  
  radio.setPALevel(RF24_PA_MIN); // Mesafe sorunu olursa RF24_PA_MAX yapın (Harici güç gerekebilir)
  radio.startListening();
  
  Serial.println("LOG:Base Station Hazir.");
}

void loop() {
  // 1. Arabadan Veri Geldi mi? (Dinleme Modu)
  if (radio.available()) {
    char text[32] = ""; // NRF24L01 standart paket boyutu max 32 byte'tır
    radio.read(&text, sizeof(text));
    
    // PC'ye ilet
    Serial.println(text);
  }
  
  // 2. PC'den Veri Geldi mi? (Serial)
  if (Serial.available() > 0) {
    String input = Serial.readStringUntil('\n');
    input.trim();
    
    if (input.length() > 0) {
      radio.stopListening(); // Göndermek için dinlemeyi durdur
      
      // String'i char array'e çevir
      char cmd[32]; 
      input.toCharArray(cmd, 32);
      
      bool sent = radio.write(&cmd, sizeof(cmd));
      
      if (sent) {
        // Serial.println("LOG:Gonderildi -> " + input); // Debug için açılabilir
      } else {
        Serial.println("LOG:Gonderim Basarisiz!");
      }
      
      radio.startListening(); // Tekrar dinlemeye geç
    }
  }
}
