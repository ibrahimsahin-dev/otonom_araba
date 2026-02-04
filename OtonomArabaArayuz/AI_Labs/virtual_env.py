import numpy as np
import math
import random

class VirtualCarEnv:
    def __init__(self, render_mode=False):
        # Dünya Ayarları
        self.width = 800
        self.height = 600
        self.render_mode = render_mode
        self.screen = None
        self.clock = None
        
        # Araba Ayarları
        self.car_x = 100
        self.car_y = 100
        self.car_angle = 0 # Derece
        self.speed = 0
        self.radius = 15
        
        # Sensör Ayarları (6 Sensör)
        self.sensor_angles = [-45, 0, 45, -90, 90, 180] # Ön Sol, Ön Orta, Ön Sağ, Yan Sol, Yan Sağ, Arka
        self.sensor_range = 200 # cm (piksel olarak kabul edelim)
        
        # Engeller (x, y, w, h)
        self.obstacles = [
            (300, 100, 50, 400), # Duvar 1
            (500, 300, 200, 50), # Duvar 2
            (100, 500, 600, 50), # Alt Duvar
            (0, 0, 800, 10),     # Çerçeve
            (0, 0, 10, 600),
            (0, 590, 800, 10),
            (790, 0, 10, 600)
        ]
        
        if self.render_mode:
            import pygame
            pygame.init()
            self.screen = pygame.display.set_mode((self.width, self.height))
            self.clock = pygame.time.Clock()

    def reset(self):
        self.car_x = 100
        self.car_y = 100
        self.car_angle = random.randint(0, 360)
        self.speed = 0
        return self.get_state()

    def step(self, action):
        # Action: 0:Dur, 1:İleri, 2:Geri, 3:Sol, 4:Sağ
        
        # Fizik Hareket
        turn_speed = 5
        move_speed = 5
        
        if action == 1: # İleri
            self.car_x += move_speed * math.cos(math.radians(self.car_angle))
            self.car_y += move_speed * math.sin(math.radians(self.car_angle))
        elif action == 2: # Geri
            self.car_x -= move_speed * math.cos(math.radians(self.car_angle))
            self.car_y -= move_speed * math.sin(math.radians(self.car_angle))
        elif action == 3: # Sol
            self.car_angle -= turn_speed
        elif action == 4: # Sağ
            self.car_angle += turn_speed
            
        # Açı Normalizasyonu
        self.car_angle %= 360
        
        # Sensörleri Oku
        state = self.get_state()
        
        # Çarpışma Kontrolü (Basit: En az bir sensör < 10 ise çarptı say)
        # Gerçek fizik çarpışması yerine sensör verisine güvenelim
        done = False
        min_dist = min(state)
        
        reward = 0
        if min_dist < 10:
            done = True
            reward = -100 # Çarpma cezası
        elif action == 1: # İleri gidiyorsa ödül
            reward = 1
            if min_dist < 40: reward = 0.5 # Engele yaklaşınca az ödül
        else:
            reward = -0.1 # Durmak veya dönmek zaman kaybı (Hafif ceza)
            
        if self.render_mode:
            self.render(state)
            
        return state, reward, done, {}

    def get_state(self):
        readings = []
        for angle_offset in self.sensor_angles:
            angle = math.radians(self.car_angle + angle_offset)
            dist = self.cast_ray(self.car_x, self.car_y, angle)
            readings.append(dist)
        return np.array(readings)

    def cast_ray(self, start_x, start_y, angle):
        for dist in range(1, self.sensor_range, 2): # 5 piksel adımla tara
            x = start_x + dist * math.cos(angle)
            y = start_y + dist * math.sin(angle)
            
            # Sınır ve Engel Kontrolü
            if x < 0 or x > self.width or y < 0 or y > self.height:
                return dist
            
            for obs in self.obstacles:
                if obs[0] < x < obs[0] + obs[2] and obs[1] < y < obs[1] + obs[3]:
                    return dist
        return self.sensor_range

    def render(self, state):
        import pygame
        self.screen.fill((0, 0, 0)) # Siyah Arka Plan
        
        # Engelleri Çiz
        for obs in self.obstacles:
            pygame.draw.rect(self.screen, (100, 100, 255), obs)
            
        # Arabayı Çiz
        pygame.draw.circle(self.screen, (255, 255, 0), (int(self.car_x), int(self.car_y)), self.radius)
        
        # Sensörleri Çiz
        for i, dist in enumerate(state):
            angle = math.radians(self.car_angle + self.sensor_angles[i])
            end_x = self.car_x + dist * math.cos(angle)
            end_y = self.car_y + dist * math.sin(angle)
            color = (0, 255, 0) if dist > 40 else (255, 0, 0)
            pygame.draw.line(self.screen, color, (self.car_x, self.car_y), (end_x, end_y), 1)
            
        pygame.display.flip()
        self.clock.tick(60) # 60 FPS sınırla
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pass
