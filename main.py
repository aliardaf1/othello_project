# main.py
from board import Board, BLACK, WHITE

def get_user_input(board, current_player):
    """
    Kullanıcıdan hamle alır, doğrular ve (satır, sütun) olarak döndürür.
    Kullanıcı 'q' girerse None döndürür (çıkış için).
    """
    print(f"Sıra '{current_player}' oyuncusunda.")
    
    while True:
        move_str = input("Hamle girin (örn: d3) veya çıkış için 'q': ").strip().lower()

        # Çıkış
        if move_str == 'q':
            print("Oyun sonlandırılıyor...")
            return None

        # format kontrolü
        if len(move_str) != 2:
            print("Hatalı format! Lütfen geçerli format girin (örn: e4).")
            continue

        col_char = move_str[0]
        row_char = move_str[1]

        # Harf ve sayı dönüştür. Sütun (a-h) -> (0-7), Satır (1-8) -> (0-7)
        if 'a' <= col_char <= 'h':
            col = ord(col_char) - ord('a') # ASCII değerini kullanarak çeviri
        else:
            print("Geçersiz sütun! Harfler a-h arasında olmalı.")
            continue
        #----------------------------------------------------------------------
        if '1' <= row_char <= '8':
            row = int(row_char) - 1
        else:
            print("Geçersiz satır! Sayılar 1-8 arasında olmalı.")
            continue

        # kural kontrolü
        if board.is_valid_move(row, col, current_player):
            return (row, col)
        else:
            print(f"Geçersiz hamle!")

def play_game():
    game_board = Board()
    current_player = BLACK # Siyah başlıyor
    
    print("--- OTHELLO (REVERSI) ---")
    
    while True:
        # anlık durum
        print("="*30)
        game_board.display()
        
        # skor
        black_score, white_score = game_board.get_score()
        print(f"\nSKOR -> Siyah (X): {black_score} | Beyaz (O): {white_score}")
        
        # oyun bitiş kontrolü
        if not game_board.has_valid_move(BLACK) and not game_board.has_valid_move(WHITE):
            print("\nOYUN BİTTİ!")
            if black_score > white_score:
                print("Kazanan: SİYAH (X)")
            elif white_score > black_score:
                print("Kazanan: BEYAZ (O)")
            else:
                print("Sonuç: BERABERE")
            break 
            
        # Sıradaki oyuncunun hamlesi yoksa pas geçecek
        if not game_board.has_valid_move(current_player):
            print(f"\n{current_player} oyuncusunun geçerli hamlesi yok. Pas geçiliyor...")
            
            current_player = WHITE if current_player == BLACK else BLACK
            continue
            
        # Hamle iste
        move = get_user_input(game_board, current_player)
        
        if move is None: # Kullanıcı 'q' ile çıkmak isterse
            break
            
        # move[0] -> satır, move[1] -> sütun
        game_board.apply_move(move[0], move[1], current_player)
        
        # sıradaki oyuncuya geç
        current_player = WHITE if current_player == BLACK else BLACK

if __name__ == "__main__":
    play_game()
