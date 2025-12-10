# main.py
import time
from board import Board, BLACK, WHITE
import ai


def get_user_input(board, current_player):
    print(f"\nSıra SİZDE ({current_player}).")
    while True:
        move_str = input("Hamle girin (örn: d3) veya 'q' çıkış: ").strip().lower()
        if move_str == 'q': return None

        if len(move_str) != 2:
            print("Hatalı format. Örnek: e3")
            continue

        col_char, row_char = move_str[0], move_str[1]
        
        if not ('a' <= col_char <= 'h' and '1' <= row_char <= '8'):
            print("Koordinatlar tahta dışında.")
            continue
            
        col = ord(col_char) - ord('a')
        row = int(row_char) - 1

        if board.is_valid_move(row, col, current_player):
            return (row, col)
        else:
            print("Geçersiz hamle! (Kurallara uymuyor)")

def get_ai_move(board, current_player, depth, heuristic_func):
    print(f"\nBilgisayar ({current_player}) düşünüyor... (Derinlik: {depth})")
    start_time = time.time()
    
    # ai.py içindeki fonksiyonu çağır
    move = ai.get_best_move(board, depth, current_player, heuristic_func)
    
    end_time = time.time()
    print(f"AI Hamlesi: {chr(move[1]+97)}{move[0]+1} (Süre: {end_time - start_time:.4f} sn)")
    return move

# --- ANA OYUN ---

def play_game():
    print("--- Othello ---")
    
    # 1. Oyun Modu Seçimi 
    print("Mod Seçin:")
    print("1. İnsan vs İnsan")
    print("2. İnsan vs AI")
    print("3. AI vs AI")
    mode = input("Seçim (1-3): ").strip()
    
    # AI Ayarları
    ai_depth = 3
    ai_heuristic = ai.evaluate_h1
    
    if mode in ['2', '3']:
        # Derinlik Seçimi
        d_input = input("AI Derinliği (Ply) (Örn: 3, 4, 5): ").strip()
        if d_input.isdigit(): ai_depth = int(d_input)
        
        # Heuristic Seçimi
        print("AI Stratejisi Seçin:")
        print("1. h1: Taş Farkı")
        print("2. h2: Temas Stratejisi")
        print("3. h3: Hamle Sayısı")
        h_choice = input("Seçim (1-3): ").strip()
        
        if h_choice == '2': ai_heuristic = ai.evaluate_h2
        elif h_choice == '3': ai_heuristic = ai.evaluate_h3
        else: ai_heuristic = ai.evaluate_h1

    if mode == '1':
        p1_type, p2_type = 'human', 'human'
    elif mode == '2':
        p1_type, p2_type = 'human', 'ai' 
    else:
        p1_type, p2_type = 'ai', 'ai'

    # Tahtayı Başlat
    board = Board()
    current_player = BLACK
    player_types = {BLACK: p1_type, WHITE: p2_type}

    # --- OYUN DÖNGÜSÜ ---
    while True:
        print("\n" + "="*30)
        board.display()
        b_score, w_score = board.get_score()
        print(f"SKOR: Siyah (X): {b_score} | Beyaz (O): {w_score}")
        
        # Bitiş Kontrolü
        if not board.has_valid_move(BLACK) and not board.has_valid_move(WHITE):
            print("\nOYUN BİTTİ!")
            if b_score > w_score: print("KAZANAN: SİYAH (X)")
            elif w_score > b_score: print("KAZANAN: BEYAZ (O)")
            else: print("BERABERE")
            break
            
        # Pas Kontrolü
        if not board.has_valid_move(current_player):
            print(f"{current_player} pas geçiyor!")
            current_player = WHITE if current_player == BLACK else BLACK
            continue
            
        # Hamle Al
        if player_types[current_player] == 'human':
            move = get_user_input(board, current_player)
            if move is None: break # Çıkış
        else:
            # AI Hamlesi
            move = get_ai_move(board, current_player, ai_depth, ai_heuristic)
            
        # Hamleyi Uygula
        board.apply_move(move[0], move[1], current_player)
        
        # Sıra Değiştir
        current_player = WHITE if current_player == BLACK else BLACK

if __name__ == "__main__":
    play_game()