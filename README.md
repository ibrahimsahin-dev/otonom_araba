# Otonom Araba Telemetri ve Simülasyon Sistemi 🚗💨

Bu proje, otonom bir oyuncak arabanın encoder ve IMU verilerini okuyarak, kablosuz (Wi-Fi) bağlantı ile Windows tabanlı bir kontrol paneline aktaran ve harita üzerinde simüle eden tam kapsamlı bir sistemdir.

## 🌟 Özellikler

*   **Canlı Telemetri:** Anlık Hız (cm/s) ve Toplam Mesafe (cm) takibi.
*   **Harita Simülasyonu:** 2D Grid üzerinde aracın konumu ve rotasının canlı çizimi.
*   **IMU Desteği:** Gyro/Pusula verisi ile aracın dönüş hareketlerinin haritaya yansıması.
*   **Kablosuz Bağlantı:** Raspberry Pi ve TCP/IP üzerinden veri aktarımı.

## 📂 Proje Yapısı

*   **`OtonomArabaArayuz/`**: Windows (WPF) arayüz uygulaması.
*   **`OtonomArabaArayuz/Embedded/`**: Arduino ve Raspberry Pi kodları.
    *   `arduino_encoder.ino`: Sensör okuma yazılımı.
    *   `rpi_bridge.py`: Veri köprü yazılımı.
    *   `simulate_data.py`: Donanım olmadan test etmek için simülasyon aracı.

## 🚀 Hızlı Kurulum

Detaylı kurulum adımları, bağlantı şemaları ve çalıştırma komutları için lütfen **[KURULUM REHBERİ (walkthrough.md)](walkthrough.md)** dosyasına bakınız.

### Gereksinimler
*   **PC:** Windows 10/11, .NET SDK
*   **Araç:** Arduino (Mega/Uno), Raspberry Pi, Motor Encoderlar, MPU6050 Sensör

## 🤖 Yapay Zeka Laboratuvarı (AI Labs)

Aracınızı yapay zeka ile eğitmek ve simülasyon ortamında test etmek için `OtonomArabaArayuz/AI_Labs` klasörünü kullanabilirsiniz.

### Kurulum (PC)
Yapay zeka simülasyonunu çalıştırmak için gerekli kütüphaneleri yükleyin:
```powershell
pip install pygame-ce numpy
```

### Başlatma
Sanal bir araba simülasyonu başlatmak ve yapay zekayı (Q-Learning) eğitmek için:
```powershell
cd OtonomArabaArayuz/AI_Labs
python train_q_learning.py
```
*   Bu komut, sanal bir ortamda arabayı 1000 bölüm boyunca eğitir ve eğitilen modeli `q_table.npy` olarak kaydeder.
*   Eğitim bitince otomatik olarak görsel test sürüşü başlar.

### Dosyalar
*   **`virtual_env.py`**: Sanal simülasyon ortamı (Fizik motoru).
*   **`train_q_learning.py`**: Ajanı eğiten ana script.
*   **`real_car_env.py`**: Gerçek araçla eğitim yapmak için köprü.
