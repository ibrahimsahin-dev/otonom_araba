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
