import random
import time
from real_car_env import RealCarEnv

def main():
    print("AI Sürücü Başlatılıyor...")
    print("Lütfen Raspberry Pi köprüsünü çalıştırın ve bağlanmasını bekleyin.")
    
    # Ortamı başlat (Server'ı açar ve RPi gelene kadar bekler)
    env = RealCarEnv(port=5000)
    
    try:
        episodes = 5
        for e in range(episodes):
            state = env.reset()
            done = False
            total_reward = 0
            steps = 0
            
            print(f"Bölüm {e+1} Başlıyor...")
            
            while not done and steps < 100:
                # --- BASİT MANTIK (Rule-Based / Kurallı) ---
                # Burası ileride Yapay Zeka (Neural Network) olacak.
                # Şimdilik: Önünde engel yoksa git, varsa dön.
                
                front_dist = state[1] # Ön Orta Sensör
                min_front = min(state[0], state[1], state[2]) # Ön 3'lü
                
                action = 0
                if min_front > 40:
                    action = 1 # İleri (Engel uzakta)
                elif state[0] > state[2]: 
                    action = 3 # Sol daha boş -> Sola Dön
                else:
                    action = 4 # Sağ daha boş -> Sağa dön
                
                # Rastgelelik (Keşif)
                if random.random() < 0.1:
                    action = random.randint(0, 4)
                
                # Eylemi Gerçekleştir
                next_state, reward, done, _ = env.step(action)
                
                state = next_state
                total_reward += reward
                steps += 1
                
                print(f"Adım: {steps}, Sensör Ön: {front_dist:.1f}cm, Eylem: {action}, Ödül: {reward}")
            
            print(f"Bölüm Bitti. Toplam Ödül: {total_reward}")
            env.send_action(0) # Dur
            time.sleep(2)
            
    except KeyboardInterrupt:
        print("Durduruluyor...")
    finally:
        env.close()

if __name__ == '__main__':
    main()
