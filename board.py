# board.py

EMPTY = '.'
BLACK = 'X'
WHITE = 'O'
BOARD_SIZE = 8

class Board:
    def __init__(self):
        self.grid = []
        self.reset_board()

    def reset_board(self):
        
        self.grid = [[EMPTY for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        
        # Başlangıç taşları
        self.grid[3][3] = WHITE
        self.grid[3][4] = BLACK
        self.grid[4][3] = BLACK
        self.grid[4][4] = WHITE

    def display(self):
        
        for r in range(BOARD_SIZE):
            # Satır numarası
            print(f"{r+1}", end=" ")
            for c in range(BOARD_SIZE):
                print(self.grid[r][c], end=" ")
            print() # Satır sonu

        print("  a b c d e f g h")

    def is_on_board(self, x, y):
        return 0 <= x < BOARD_SIZE and 0 <= y < BOARD_SIZE
        

    def get_valid_moves(self, tile):
        moves = []
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if self.is_valid_move(r, c, tile):
                    moves.append((r, c))
        return moves

    def is_valid_move(self, start_row, start_col, tile):
        # Eğer kare tahta dışındaysa veya doluysa : FALSE
        if not self.is_on_board(start_row, start_col) or self.grid[start_row][start_col] != EMPTY:
            return False

        other_tile = WHITE if tile == BLACK else BLACK
        
        # Yönler: (x, y değişimi)
        directions = [ (0, 1), (1, 0), (0, -1), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]

        for row_step, col_step in directions:
            # İncelemeye hemen yanındaki kareden başla
            current_row = start_row + row_step
            current_col = start_col + col_step
            
            found_opponent = False
            
            # Bu yönde rakip taş olduğu sürece ilerle (Adım adım git)
            while self.is_on_board(current_row, current_col) and self.grid[current_row][current_col] == other_tile:
                current_row += row_step
                current_col += col_step
                found_opponent = True
            
            # Zincirin sonunda KENDİ taşımızı bulduysak bu yön geçerlidir
            if found_opponent and self.is_on_board(current_row, current_col) and self.grid[current_row][current_col] == tile:
                return True
                
        return False
    
    # Verilen koordinata taşı koyar ve Othello kurallarına göre arada kalan rakip taşlarını çevirir. Hamle geçersizse hiçbir şey yapmaz ve False döner.
    def apply_move(self, start_row, start_col, tile):

        #is_valid_move
        if not self.is_valid_move(start_row, start_col, tile):
            return False
            
        # Geçerliyse yerleştir, güncellemeleri yap.
        self.grid[start_row][start_col] = tile
        
        other_tile = WHITE if tile == BLACK else BLACK
        
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]

        #Taşları dönüştür
        for row_step, col_step in directions:
            current_row = start_row + row_step
            current_col = start_col + col_step
            
            tiles_to_flip = [] # Çevrilebilecek taşlar listesi

            # Rakip taşları gördükçe listeye ekle ve yenisine geç
            while self.is_on_board(current_row, current_col) and self.grid[current_row][current_col] == other_tile:
                tiles_to_flip.append((current_row, current_col))
                current_row += row_step
                current_col += col_step
            
            # Eğer kendi taşımızı bulduysak, listedeki taşları çevir
            if tiles_to_flip and self.is_on_board(current_row, current_col) and self.grid[current_row][current_col] == tile:
                for flip_row, flip_col in tiles_to_flip:
                    self.grid[flip_row][flip_col] = tile
                    
        return True

    def has_valid_move(self, tile):
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if self.is_valid_move(r, c, tile):
                    return True
        return False

    def get_score(self): #Tahtadaki siyah ve beyaz taşları say skoru belirle.
        black_count = 0
        white_count = 0
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if self.grid[r][c] == BLACK:
                    black_count += 1
                elif self.grid[r][c] == WHITE:
                    white_count += 1
        return black_count, white_count

    def is_full(self): # Tahta dolu mu kontrol et.
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if self.grid[r][c] == EMPTY:
                    return False
        return True

if __name__ == "__main__":
    b = Board()
    b.display()