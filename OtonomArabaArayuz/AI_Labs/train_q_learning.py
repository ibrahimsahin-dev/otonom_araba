import numpy as np
import random
import time
from virtual_env import VirtualCarEnv

# Ayarlar
EPISODES = 1000
MAX_STEPS = 500
LEARNING_RATE = 0.1
DISCOUNT_FACTOR = 0.95
EPSILON = 1.0  # Keşif oranı
EPSILON_DECAY = 0.995
EPSILON_MIN = 0.01

# Q-Table Ayarları
# State: 6 Sensör (3 seviye) + Hedef Açı Farkı (4 Yön: Ön, Sol, Sağ, Arka)
# Mesafe bilgisini şimdilik ihmal edelim, açı daha kritik.
SENSOR_LEVELS = 3 
ANGLE_LEVELS = 4
ACTION_SIZE = 5

q_table = {} 

def discretize_state(state):
    # State formatı: [S1...S6, Hedef_Dist, Hedef_Angle]
    
    # 1. Sensörleri Seviyelendir
    levels = []
    for dist in state[:6]:
        if dist < 50: levels.append(0) # Çok Yakın (Tehlike)
        elif dist < 120: levels.append(1) # Orta
        else: levels.append(2) # Uzak
        
    # 2. Hedef Açısını Seviyelendir (-180, 180)
    angle = state[7] 
    # Ön: -45 ile 45, Sol: -135 ile -45, Sağ: 45 ile 135, Arka: Diğerleri
    
    angle_level = 0
    if -45 <= angle <= 45: angle_level = 0 # Hedef Önde
    elif -135 <= angle < -45: angle_level = 1 # Hedef Solda
    elif 45 < angle <= 135: angle_level = 2 # Hedef Sağda
    else: angle_level = 3 # Hedef Arkada
    
    levels.append(angle_level)
    
    return tuple(levels)

def get_q_value(state):
    if state not in q_table:
        q_table[state] = np.zeros(ACTION_SIZE)
    return q_table[state]

def main():
    global EPSILON
    env = VirtualCarEnv(render_mode=False) # Eğitimde görselleştirme kapalı (Hız için)
    
    print("Eğitim Başlıyor...")
    
    for episode in range(EPISODES):
        raw_state = env.reset()
        state = discretize_state(raw_state)
        total_reward = 0
        done = False
        
        for step in range(MAX_STEPS):
            # Epsilon-Greedy Action Selection
            if random.uniform(0, 1) < EPSILON:
                action = random.randint(0, ACTION_SIZE - 1)
            else:
                action = np.argmax(get_q_value(state))
            
            # Ortamda adım at
            next_raw_state, reward, done, _ = env.step(action)
            next_state = discretize_state(next_raw_state)
            
            # Q-Learning Güncelleme
            # Q_new = Q_old + LR * (Reward + Gamma * max(Q_next) - Q_old)
            old_q = get_q_value(state)[action]
            next_max_q = np.max(get_q_value(next_state))
            new_q = old_q + LEARNING_RATE * (reward + DISCOUNT_FACTOR * next_max_q - old_q)
            q_table[state][action] = new_q
            
            state = next_state
            total_reward += reward
            
            if done:
                break
        
        # Epsilon'u azalt
        if EPSILON > EPSILON_MIN:
            EPSILON *= EPSILON_DECAY
            
        if episode % 100 == 0:
            print(f"Episode: {episode}, Reward: {total_reward:.2f}, Epsilon: {EPSILON:.2f}")

    print("Eğitim Tamamlandı!")
    
    # Modeli Kaydet
    np.save('q_table.npy', q_table)
    print("Model kaydedildi: q_table.npy")

    # TEST AŞAMASI (Görsel)
    print("Test Sürüşü Başlıyor... (Pencere açılacak)")
    env = VirtualCarEnv(render_mode=True)
    raw_state = env.reset()
    state = discretize_state(raw_state)
    
    while True:
        action = np.argmax(get_q_value(state))
        next_raw_state, _, done, _ = env.step(action)
        state = discretize_state(next_raw_state)
        
        if done: 
            env.reset()
        
        # Pygame penceresini kapatma kontrolü virtual_env içinde yapılıyor ama buraya da ekleyelim
        import pygame
        if pygame.event.peek(pygame.QUIT): break

if __name__ == '__main__':
    main()
