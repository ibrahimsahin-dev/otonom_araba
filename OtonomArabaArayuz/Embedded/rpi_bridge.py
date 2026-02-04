import serial
import socket
import time
import sys
import threading

# Ayarlar
SERIAL_PORT = '/dev/ttyUSB0' 
BAUD_RATE = 9600
SERVER_IP = '192.168.1.100' # Kendi PC IP'nizi buraya yazın
SERVER_PORT = 5000

ser = None
sock = None
running = True

def serial_listener():
    """Arduino'dan gelen veriyi dinler ve TCP'ye gönderir"""
    global ser, sock, running
    print("Serial dinleyici başlatıldı.")
    while running:
        try:
            if ser and ser.in_waiting > 0:
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                if line and sock:
                    print(f"Arduino -> PC: {line}")
                    try:
                        sock.sendall((line + "\n").encode('utf-8'))
                    except Exception as e:
                        print(f"Soket gönderme hatası: {e}")
                        running = False
            else:
                time.sleep(0.01)
        except Exception as e:
            print(f"Serial okuma hatası: {e}")
            running = False

def socket_listener():
    """PC'den gelen veriyi dinler ve Arduino'ya gönderir"""
    global ser, sock, running
    print("Soket dinleyici başlatıldı.")
    while running:
        try:
            if sock:
                data = sock.recv(1024)
                if not data:
                    print("Sunucu bağlantıyı kesti.")
                    running = False
                    break
                
                message = data.decode('utf-8').strip()
                print(f"PC -> Arduino: {message}")
                
                if ser:
                    ser.write((message + "\n").encode('utf-8'))
        except Exception as e:
            print(f"Soket okuma hatası: {e}")
            running = False

def main():
    global ser, sock, running
    print("Otonom Araba Çift Yönlü Köprü v2.0")
    
    # 1. Serial Bağlantı
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        print(f"Seri port açıldı: {SERIAL_PORT}")
    except Exception as e:
        print(f"Seri port açılamadı! {e}")
        # Test amaçlı devam etmesin
        return

    # 2. Socket Bağlantı
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((SERVER_IP, SERVER_PORT))
        print(f"Sunucuya bağlanıldı: {SERVER_IP}:{SERVER_PORT}")
    except Exception as e:
        print(f"Sunucuya bağlanılamadı! {e}")
        ser.close()
        return

    # 3. Threadleri Başlat
    t1 = threading.Thread(target=serial_listener)
    t2 = threading.Thread(target=socket_listener)
    
    t1.start()
    t2.start()
    
    try:
        # Ana thread beklemede kalsın
        while running:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Durduruluyor...")
        running = False
    finally:
        if ser: ser.close()
        if sock: sock.close()
        print("Kapatıldı.")

if __name__ == '__main__':
    main()
