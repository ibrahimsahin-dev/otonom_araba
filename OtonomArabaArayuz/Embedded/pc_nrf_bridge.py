import serial
import socket
import time
import threading
import sys

# Ayarlar
SERIAL_PORT = 'COM3' # Arduino Uno'nun takılı olduğu COM portunu buraya yazın!
BAUD_RATE = 9600
SERVER_IP = '127.0.0.1' # Localhost (Aynı PC)
SERVER_PORT = 5000

ser = None
sock = None
running = True

def serial_listener():
    """Arduino Base Station'dan gelen veriyi (Telemetri) TCP'ye gönderir"""
    global ser, sock, running
    print("Serial dinleyici başlatıldı.")
    while running:
        try:
            if ser and ser.in_waiting > 0:
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                if line:
                    print(f"Araba -> PC: {line}")
                    if sock:
                        try:
                            # Gelen paketler kısa (NRF limiti), bunları birleştirmemiz gerekebilir
                            # Ama şimdilik olduğu gibi atalım, C# parser parçalı veriyi yönetebilir mi bakalım.
                            # Format Dönüşümü Gerekebilir:
                            # Gelen: "SPD:10;ANG:45"
                            # Beklenen: "SPEED:10;ANGLE:45"
                            
                            # Basit bir mapping yapalım
                            line = line.replace("SPD:", "SPEED:").replace("ANG:", "ANGLE:").replace("SNS:", "SENS:")
                            
                            sock.sendall((line + "\n").encode('utf-8'))
                        except Exception as e:
                            print(f"Soket hatası: {e}")
                            running = False
        except Exception as e:
            print(f"Serial okuma hatası: {e}")
            time.sleep(1)

def socket_listener():
    """TCP'den gelen veriyi (Komut) Arduino Base Station'a gönderir"""
    global ser, sock, running
    print("Socket dinleyici başlatıldı.")
    while running:
        try:
            if sock:
                data = sock.recv(1024)
                if not data: break
                
                cmd = data.decode('utf-8').strip()
                print(f"PC -> Araba: {cmd}")
                
                if ser:
                    ser.write((cmd + "\n").encode('utf-8'))
        except Exception as e:
            print(f"Socket okuma hatası: {e}")
            break

def main():
    global ser, sock, running
    
    print("--- NRF Base Station Köprüsü ---")
    port_input = input(f"Arduino COM Portu [{SERIAL_PORT}]: ")
    serial_port = port_input if port_input else SERIAL_PORT
    
    # 1. Serial Bağlan
    try:
        ser = serial.Serial(serial_port, BAUD_RATE, timeout=1)
        print(f"Arduino bağlandı: {serial_port}")
    except Exception as e:
        print(f"HATA: Arduino bulunamadı! {e}")
        return

    # 2. TCP Bağlan (Windows Uygulamasına)
    print("Windows uygulamasına bağlanılıyor...")
    while True:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((SERVER_IP, SERVER_PORT))
            print(f"Sunucuya bağlanıldı: {SERVER_IP}:{SERVER_PORT}")
            break
        except:
            print("Sunucu bekleniyor... (Uygulamada 'Server Başlat' dediniz mi?)")
            time.sleep(2)
            
    # 3. Threadleri Başlat
    t1 = threading.Thread(target=serial_listener)
    t2 = threading.Thread(target=socket_listener)
    t1.daemon = True
    t2.daemon = True
    t1.start()
    t2.start()
    
    try:
        while running:
            time.sleep(1)
    except KeyboardInterrupt:
        running = False
        print("Kapatılıyor...")
    finally:
        if ser: ser.close()
        if sock: sock.close()

if __name__ == '__main__':
    main()
