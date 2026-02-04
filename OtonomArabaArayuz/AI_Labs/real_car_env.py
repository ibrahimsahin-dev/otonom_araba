import socket
import time
import numpy as np
import threading

class RealCarEnv:
    def __init__(self, host='0.0.0.0', port=5000):
        self.host = host
        self.port = port
        self.client_socket = None
        self.server_socket = None
        
        # State: 6 Sensör verisi (0-200 cm arası)
        self.state_size = 6 
        self.current_state = np.zeros(self.state_size)
        
        # Actions: 0: Dur, 1: İleri, 2: Geri, 3: Sol, 4: Sağ
        self.action_size = 5
        
        # Server Başlat
        self.setup_server()

    def setup_server(self):
        print(f"AI Server {self.port} portunda başlatılıyor...")
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(1)
        print("Araç bağlantısı bekleniyor...")
        self.client_socket, addr = self.server_socket.accept()
        print(f"Araç bağlandı: {addr}")
    
    def reset(self):
        self.send_command("STOP")
        time.sleep(0.1)
        # İlk veriyi okuyalım
        return self.get_sensor_data()

    def step(self, action):
        # 1. Action Uygula
        self.send_action(action)
        
        # 2. Bekle (Eylem gerçekleşsin)
        time.sleep(0.1) 
        
        # 3. Yeni Durumu Oku
        next_state = self.get_sensor_data()
        
        # 4. Ödül Hesapla
        reward = self.calculate_reward(next_state, action)
        
        # 5. Done durumu (Çarpışma?)
        done = False
        if min(next_state) < 10: # 10 cm'den yakınsa çarptı say
            done = True
            reward = -100
            
        return next_state, reward, done, {}

    def send_action(self, action):
        cmd = "STOP"
        speed = 100
        turn_speed = 120
        
        if action == 0: cmd = "STOP"
        elif action == 1: cmd = f"MOTOR:{speed}:{speed}"   # İleri
        elif action == 2: cmd = f"MOTOR:{-speed}:{-speed}" # Geri
        elif action == 3: cmd = f"MOTOR:{-turn_speed}:{turn_speed}" # Sol (Nokta dönüş)
        elif action == 4: cmd = f"MOTOR:{turn_speed}:{-turn_speed}" # Sağ
        
        self.send_command(cmd)

    def send_command(self, cmd):
        if self.client_socket:
            try:
                self.client_socket.sendall((cmd + "\n").encode('utf-8'))
            except Exception as e:
                print(f"Gönderme hatası: {e}")

    def get_sensor_data(self):
        # Buffer temizle ve en son veriyi al
        # Not: Gerçek uygulamada daha sağlam bir parser gerekir.
        # Burada basitçe son gelen geçerli paketi arayacağız.
        try:
            self.client_socket.settimeout(2.0)
            data = self.client_socket.recv(4096).decode('utf-8')
            lines = data.split('\n')
            
            # Sondan başa doğru geçerli bir SENS paketi ara
            for line in reversed(lines):
                if "SENS:" in line:
                    # Format: ...;SENS:d1,d2,d3,d4,d5,d6
                    parts = line.split('SENS:')
                    if len(parts) > 1:
                        sens_str = parts[1].split(';')[0].strip() # Varsa sonraki noktalı virgülü at
                        vals = sens_str.split(',')
                        if len(vals) == 6:
                            sensors = [float(v) for v in vals]
                            self.current_state = np.array(sensors)
                            return self.current_state
        except Exception as e:
            print(f"Veri okuma hatası: {e}")
        
        return self.current_state # Hata varsa eskisini dön

    def calculate_reward(self, state, action):
        # Basit Ödül Fonksiyonu
        min_dist = min(state)
        
        reward = 0
        if min_dist < 20:
             reward = -10 # Tehlike
        elif action == 1: # İleri gidiyorsa ve çarpma yoksa ödül ver
             reward = 1
        elif action == 0: # Duruyorsa küçük ceza (harekete teşvik)
             reward = -0.1
             
        return reward

    def close(self):
        if self.client_socket: self.client_socket.close()
        if self.server_socket: self.server_socket.close()
