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
        
        # Hedef Ayarları
        self.goal_x = 700
        self.goal_y = 500
        self.goal_radius = 20
        
        # Sensör Ayarları (6 Sensör)
        self.sensor_angles = [-45, 0, 45, -90, 90, 180] 
        self.sensor_range = 200 
        
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
        
        # Pygame Başlat
        if self.render_mode:
            import pygame
            pygame.init()
            pygame.display.set_caption("AI Training Simulation")
            self.screen = pygame.display.set_mode((self.width, self.height))
            self.clock = pygame.time.Clock()

    def reset(self):
        # Aracı ve Hedefi Rastgele Yerleştir (Engelle çakışmayacak şekilde)
        self.car_x = 100
        self.car_y = 100
        self.car_angle = random.randint(0, 360)
        
        # Rastgele Hedef (Basitlik için sabit veya yarı-rastgele olabilir)
        self.goal_x = random.randint(100, 700)
        self.goal_y = random.randint(100, 500)
        
        return self.get_state()

    def step(self, action):
        # Action: 0:Dur, 1:İleri, 2:Geri, 3:Sol, 4:Sağ
        
        prev_dist_to_goal = math.hypot(self.goal_x - self.car_x, self.goal_y - self.car_y)
        
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
            
        self.car_angle %= 360
        
        # Sensörleri Oku
        state = self.get_state()
        min_sensor_dist = min(state[:6]) # İlk 6 değer sensör
        
        # Hedef Hesaplamaları
        dist_to_goal = math.hypot(self.goal_x - self.car_x, self.goal_y - self.car_y)
        
        done = False
        reward = 0
        
        # 1. Hedefe Ulaşma
        if dist_to_goal < self.goal_radius + self.radius:
            done = True
            reward = 100 # Büyük Ödül!
            print("Hedefe Ulaşıldı! 🏆")
            
        # 2. Çarpışma
        elif min_sensor_dist < 10:
            done = True
            reward = -100 # Ceza
            
        # 3. Adım Ödülü (Shaping)
        else:
            # Hedefe yaklaştı mı?
            diff = prev_dist_to_goal - dist_to_goal
            reward += diff * 0.5 # Yaklaştıysa pozitif, uzaklaştıysa negatif
            
            # Zaman cezası (Hızlı gitmesi için)
            reward -= 0.1
            
        if self.render_mode:
            self.render(state)
            
        return state, reward, done, {}

    def get_state(self):
        # Sensörler
        readings = []
        for angle_offset in self.sensor_angles:
            angle = math.radians(self.car_angle + angle_offset)
            dist = self.cast_ray(self.car_x, self.car_y, angle)
            readings.append(dist)
            
        # Hedef Bilgisi (Polar Koordinat: Mesafe ve Açı Farkı)
        dist_to_goal = math.hypot(self.goal_x - self.car_x, self.goal_y - self.car_y)
        
        target_angle = math.degrees(math.atan2(self.goal_y - self.car_y, self.goal_x - self.car_x))
        angle_diff = target_angle - self.car_angle
        angle_diff = (angle_diff + 180) % 360 - 180 # -180 ile 180 arasına çek
        
        # State Vektörü: [S1, S2, ..., S6, Hedef_Mesafe, Hedef_Açı_Farkı]
        state = np.array(readings + [dist_to_goal, angle_diff])
        return state

    def cast_ray(self, start_x, start_y, angle):
        for dist in range(1, self.sensor_range, 5): 
            x = start_x + dist * math.cos(angle)
            y = start_y + dist * math.sin(angle)
            
            if x < 0 or x > self.width or y < 0 or y > self.height:
                return dist
            
            for obs in self.obstacles:
                if obs[0] < x < obs[0] + obs[2] and obs[1] < y < obs[1] + obs[3]:
                    return dist
        return self.sensor_range

    def render(self, state):
        import pygame
        self.screen.fill((0, 0, 0)) 
        
        # Engeller
        for obs in self.obstacles:
            pygame.draw.rect(self.screen, (100, 100, 255), obs)
            
        # Hedef
        pygame.draw.circle(self.screen, (0, 255, 0), (int(self.goal_x), int(self.goal_y)), self.goal_radius)
            
        # Araba
        pygame.draw.circle(self.screen, (255, 255, 0), (int(self.car_x), int(self.car_y)), self.radius)
        # Yön çizgisi
        front_x = self.car_x + 20 * math.cos(math.radians(self.car_angle))
        front_y = self.car_y + 20 * math.sin(math.radians(self.car_angle))
        pygame.draw.line(self.screen, (255, 255, 255), (self.car_x, self.car_y), (front_x, front_y), 2)
        
        pygame.display.flip()
        self.clock.tick(60) 
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pass
