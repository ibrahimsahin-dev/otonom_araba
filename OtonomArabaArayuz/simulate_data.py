import socket
import time
import math
import random

SERVER_IP = '127.0.0.1'
SERVER_PORT = 5000

def main():
    print(f"Simülasyon başlatılıyor... Hedef: {SERVER_IP}:{SERVER_PORT}")
    
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((SERVER_IP, SERVER_PORT))
        print("Sunucuya bağlanıldı!")
    except Exception as e:
        print(f"Bağlantı hatası: {e}")
        print("Önce Windows uygulamasından 'Server Başlat' butonuna bastığınızdan emin olun.")
        return

    speed = 0.0
    distance = 0.0
    angle = 0.0
    
    # Simülasyon döngüsü
    try:
        while True:
            # Rastgele veya desenli veri değişimi
            
            # Hızlanma ve yavaşlama simülasyonu
            target_speed = 50.0 # cm/s
            if speed < target_speed:
                speed += 1.5
            
            # Mesafe artışı (Hız * zaman) - dt = 0.1s
            delta_dist = speed * 0.1
            distance += delta_dist
            
            # Daire çizmek için açıyı sürekli değiştir
            # Her adımda 2 derece dön
            angle += 2.0
            if angle >= 360: angle -= 360
            
            # Veri paketini oluştur
            # Format: SPEED:12.5;DIST:100.2;ANGLE:45.0
            data = f"SPEED:{speed:.2f};DIST:{distance:.2f};ANGLE:{angle:.2f}\n"
            
            # Gönder
            s.sendall(data.encode('utf-8'))
            print(f"Gönderildi: {data.strip()}")
            
            time.sleep(0.1) # 100ms
            
    except KeyboardInterrupt:
        print("\nSimülasyon durduruldu.")
    except Exception as e:
        print(f"Hata oluştu: {e}")
    finally:
        s.close()

if __name__ == '__main__':
    main()
