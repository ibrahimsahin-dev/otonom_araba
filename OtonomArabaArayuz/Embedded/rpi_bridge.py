import serial
import socket
import time
import sys

# Ayarlar
SERIAL_PORT = '/dev/ttyUSB0' # Arduino'nun bağlı olduğu port (Linux/RPi)
BAUD_RATE = 9600
SERVER_IP = '192.168.1.100' # Windows Bilgisayarınızın IP Adresini Buraya Yazın
SERVER_PORT = 5000

def connect_serial():
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        print(f"Seri port {SERIAL_PORT} açıldı.")
        return ser
    except Exception as e:
        print(f"Seri port hatası: {e}")
        return None

def connect_socket():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((SERVER_IP, SERVER_PORT))
        print(f"Sunucuya bağlanıldı: {SERVER_IP}:{SERVER_PORT}")
        return s
    except Exception as e:
        print(f"Soket bağlantı hatası: {e}")
        return None

def main():
    print("Otonom Araba Köprü Yazılımı Başlatılıyor...")
    
    ser = connect_serial()
    sock = connect_socket()
    
    if not ser or not sock:
        print("Bağlantı kurulamadı, çıkılıyor.")
        return

    try:
        while True:
            if ser.in_waiting > 0:
                line = ser.readline().decode('utf-8').strip()
                if line:
                    print(f"Arduino'dan gelen: {line}")
                    # Veriyi TCP üzerinden gönder
                    sock.sendall((line + "\n").encode('utf-8'))
            
            time.sleep(0.01)

    except KeyboardInterrupt:
        print("Durduruluyor...")
    finally:
        if ser: ser.close()
        if sock: sock.close()

if __name__ == '__main__':
    main()
