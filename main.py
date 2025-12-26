# main.py
import time
from board import Board, BLACK, WHITE
import ai


def get_user_input(board, current_player):
    print(f"\nSıra SİZDE ({current_player}).")
    while True:
        move_str = input("Hamle girin (örn: d3) veya 'q' çıkış: ").strip().lower()
        if move_str == 'q':
            return None

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

    move = ai.get_best_move(board, depth, current_player, heuristic_func)

    end_time = time.time()
    if move is not None:
        print(f"AI Hamlesi: {chr(move[1] + 97)}{move[0] + 1} (Süre: {end_time - start_time:.4f} sn)")
    else:
        print(f"AI hamle bulamadı (pas). (Süre: {end_time - start_time:.4f} sn)")
    return move


def select_heuristic(prompt_prefix="AI"):
    while True:
        print(f"{prompt_prefix} Stratejisi Seçin:")
        print("1. h1: Taş Farkı")
        print("2. h2: Kare Ağırlıkları")
        print("3. h3: Hareketlilik (Hamle Sayısı)")
        print("4. h4: Hybrid (Mobility + Corner + Position + Parity)")
        print("5. Best")
        h_choice = input("Seçim (1-5): ").strip()

        if h_choice == '1':
            return ai.evaluate_h1
        elif h_choice == '2':
            return ai.evaluate_h2
        elif h_choice == '3':
            return ai.evaluate_h3
        elif h_choice == '4':
            return ai.evaluate_hybrid
        elif h_choice == '5':
            return ai.evaluate_ultimate
        else:
            print("Geçersiz seçim. ")


def select_depth(prompt_prefix="AI"):
    while True:
        d_input = input(f"{prompt_prefix} Derinlik: ").strip()
        if d_input.isdigit() and int(d_input) > 0:
            return int(d_input)
        print("Geçersiz seçim. ")


def select_human_vs_ai_side():
    while True:
        print("\nİnsan vs AI: AI hangi taraf olsun?")
        print("1. Siyah (X)")
        print("2. Beyaz (O)")
        choice = input("Seçim (1-2): ").strip()
        if choice == '1':
            return BLACK  # AI is BLACK
        elif choice == '2':
            return WHITE  # AI is WHITE
        print("Geçersiz seçim. ")


def play_game():
    print("--- Othello ---")

    # Oyun Modu Seçimi
    while True:
        print("Mod: ")
        print("1. İnsan vs İnsan")
        print("2. İnsan vs AI")
        print("3. AI vs AI")
        mode = input("Seçim (1-3): ").strip()
        if mode in ['1', '2', '3']:
            break
        print("Geçersiz seçim, tekrar deneyin.")

    # AI Varsayılan Ayarları
    ai_depth_black = 3
    ai_depth_white = 3
    ai_heuristic_black = ai.evaluate_h1
    ai_heuristic_white = ai.evaluate_h1

    # Oyuncu tipleri (en sonda kesinleştirilecek)
    p1_type, p2_type = 'human', 'human'

    if mode == '2':
        # İnsan vs AI: AI tarafını seçtir
        ai_side = select_human_vs_ai_side()

        if ai_side == BLACK:
            # AI Siyah (X), İnsan Beyaz (O)
            print("\n--- SİYAH AI (X) Ayarları ---")
            ai_depth_black = select_depth("Siyah AI")
            ai_heuristic_black = select_heuristic("Siyah AI")

            p1_type, p2_type = 'ai', 'human'

        else:
            # AI Beyaz (O), İnsan Siyah (X)
            print("\n--- BEYAZ AI (O) Ayarları ---")
            ai_depth_white = select_depth("Beyaz AI")
            ai_heuristic_white = select_heuristic("Beyaz AI")

            p1_type, p2_type = 'human', 'ai'

    elif mode == '3':
        # AI vs AI: Depth ve heuristic ayrı ayrı seçiliyor
        print("\n--- SİYAH AI (X) Ayarları ---")
        ai_depth_black = select_depth("Siyah AI")
        ai_heuristic_black = select_heuristic("Siyah AI")

        print("\n--- BEYAZ AI (O) Ayarları ---")
        ai_depth_white = select_depth("Beyaz AI")
        ai_heuristic_white = select_heuristic("Beyaz AI")

        p1_type, p2_type = 'ai', 'ai'

    else:
        # İnsan vs İnsan
        p1_type, p2_type = 'human', 'human'

    # Tahtayı başlat
    board = Board()
    current_player = BLACK
    player_types = {BLACK: p1_type, WHITE: p2_type}

    # Oyun döngüsü
    while True:
        print("\n" + "=" * 30)
        board.display()
        b_score, w_score = board.get_score()
        print(f"SKOR: Siyah (X): {b_score} | Beyaz (O): {w_score}")

        # Bitiş Kontrolü
        if not board.has_valid_move(BLACK) and not board.has_valid_move(WHITE):
            print("\nOYUN BİTTİ!")
            if b_score > w_score:
                print("KAZANAN: SİYAH (X)")
            elif w_score > b_score:
                print("KAZANAN: BEYAZ (O)")
            else:
                print("BERABERE")
            break

        # Pas Kontrolü
        if not board.has_valid_move(current_player):
            print(f"{current_player} pas geçiyor!")
            current_player = WHITE if current_player == BLACK else BLACK
            continue

        # Hamle Al
        if player_types[current_player] == 'human':
            move = get_user_input(board, current_player)
            if move is None:
                break
        else:
            if current_player == BLACK:
                depth = ai_depth_black
                heuristic_func = ai_heuristic_black
            else:
                depth = ai_depth_white
                heuristic_func = ai_heuristic_white

            move = get_ai_move(board, current_player, depth, heuristic_func)
            if move is None:
                current_player = WHITE if current_player == BLACK else BLACK
                continue

        board.apply_move(move[0], move[1], current_player)
        current_player = WHITE if current_player == BLACK else BLACK


if __name__ == "__main__":
    play_game()
