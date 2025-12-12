# ai.py
from board import BLACK, WHITE
import copy
from board import BOARD_SIZE

INF = float('inf')

POSITION_WEIGHTS = [
    [100, -20, 10,  5,  5, 10, -20, 100],
    [-20, -50, -2, -2, -2, -2, -50, -20],
    [ 10,  -2,  5,  1,  1,  5,  -2,  10],
    [  5,  -2,  1,  0,  0,  1,  -2,   5],
    [  5,  -2,  1,  0,  0,  1,  -2,   5],
    [ 10,  -2,  5,  1,  1,  5,  -2,  10],
    [-20, -50, -2, -2, -2, -2, -50, -20],
    [100, -20, 10,  5,  5, 10, -20, 100],
]

def evaluate_h1(board, player_tile):
    """Heuristic 1: Oyuncu Taşları - Rakip Taşları"""
    black_count, white_count = board.get_score()
    
    # Kimin açısından
    if player_tile == BLACK:
        my_score = black_count
        opponent_score = white_count
    else:
        my_score = white_count
        opponent_score = black_count
        
    return my_score - opponent_score

def evaluate_h2(board, player_tile):
    """
    Heuristic 2: Hareketlilik (Mobility)
    = (Benim geçerli hamlelerim) - (Rakibin geçerli hamleleri), normalize edilmiş.
    """
    opponent_tile = WHITE if player_tile == BLACK else BLACK

    my_moves = len(board.get_valid_moves(player_tile))
    opponent_moves = len(board.get_valid_moves(opponent_tile))

    # İkimizin de hamlesi yoksa konum mobilite açısından nötr
    if my_moves + opponent_moves == 0:
        return 0

    # -100 .. +100 aralığına normalize et
    return 100 * (my_moves - opponent_moves) / (my_moves + opponent_moves)

def evaluate_h3(board, player_tile):
    """
    Heuristic 3: Konumsal Ağırlıklar
    Tahtadaki her taş için:
    - Benim taşım ise o karenin ağırlığını + ekle,
    - Rakibin taşı ise o karenin ağırlığını - ekle.
    """
    opponent_tile = WHITE if player_tile == BLACK else BLACK

    score = 0
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            tile = board.grid[r][c]
            if tile == player_tile:
                score += POSITION_WEIGHTS[r][c]
            elif tile == opponent_tile:
                score -= POSITION_WEIGHTS[r][c]
            # EMPTY ('.') ise 0 eklenir, yani etkisiz

    return score



# def evaluate_h2(board, player_tile):
#     """
#     Heuristic 2: Benim taşlarımın komşuluğunda ne kadar çok rakip taşı varsa,
#     o kadar fazla etkileşim ve potansiyel çevirme şansı vardır.
#      = (Benim taşlarımın yanındaki rakip sayısı) - (Rakibin taşlarının yanındaki benim sayım)
#     """
#     my_adjacency_score = 0
#     opponent_adjacency_score = 0
#     
#     directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
# 
#     for r in range(BOARD_SIZE):
#         for c in range(BOARD_SIZE):
#             # Kare dolu mu?
#             if board.grid[r][c] != '.':
#                 # O karedeki taşın etrafına bak
#                 neighbor_opponents = 0
#                 
#                 for dr, dc in directions:
#                     nr, nc = r + dr, c + dc
#                     if board.is_on_board(nr, nc):
#                         # Eğer komşu karede rakip varsa say
#                         if board.grid[nr][nc] != '.' and board.grid[nr][nc] != board.grid[r][c]:
#                             neighbor_opponents += 1
#                 
#                 # Puanı ilgili haneye yaz
#                 if board.grid[r][c] == player_tile:
#                     my_adjacency_score += neighbor_opponents
#                 else:
#                     opponent_adjacency_score += neighbor_opponents
#                     
#     # Bizim rakiple temasımız ne kadar çoksa o kadar iyi
#     return my_adjacency_score - opponent_adjacency_score
# 
# def evaluate_h3(board, player_tile):
#     """Heuristic 3: Oyuncunun yapabileceği hamle sayısı - Rakibin yapabileceği hamle sayısı. """
#     
#     opponent_tile = WHITE if player_tile == BLACK else BLACK
#     
#     my_moves = len(board.get_valid_moves(player_tile))
#     opponent_moves = len(board.get_valid_moves(opponent_tile))
#     
#     return my_moves - opponent_moves




def order_moves(board, moves, tile):
    # Basit positional weight ordering
    scored = []
    for r, c in moves:
        score = POSITION_WEIGHTS[r][c]  # köşeler en değerli
        scored.append((score, (r, c)))

    scored.sort(reverse=True)  
    return [move for _, move in scored]




def minimax(board, depth, alpha, beta, maximizing_player, player_tile, heuristic_func):
    
    opponent_tile = WHITE if player_tile == BLACK else BLACK
    current_tile = player_tile if maximizing_player else opponent_tile

    # Oyun bitmişse veya derinlik sıfırsa skor döndür
    if depth == 0 or (not board.has_valid_move(BLACK) and not board.has_valid_move(WHITE)):
        return heuristic_func(board, player_tile), None

    valid_moves = board.get_valid_moves(current_tile)

    # PAS DURUMU → sıra rakibe geçer, depth aynı kalır
    if not valid_moves:
        eval_score, _ = minimax(
            board, depth, alpha, beta,
            not maximizing_player, player_tile, heuristic_func
        )
        return eval_score, None

    best_move = None

    # MAX PLAYER (AI kendi açısından en iyi skoru arıyor)
    if maximizing_player:
        max_eval = -INF

        for r, c in order_moves(board, valid_moves, current_tile):

            # Hamleyi uygula (flip edilenleri geri almak için liste döner)
            flipped = board.apply_move_and_get_flipped(r, c, current_tile)

            # Çocuk düğüm
            eval_score, _ = minimax(
                board, depth - 1, alpha, beta,
                False, player_tile, heuristic_func
            )

            # UNDO
            board.undo_move(r, c, current_tile, flipped)

            # En iyi skoru güncelle
            if eval_score > max_eval:
                max_eval = eval_score
                best_move = (r, c)

            # Alpha güncellenir
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break  # pruning

        return max_eval, best_move

    # MIN PLAYER (rakip en kötü sonucu seçiyor)
    else:
        min_eval = INF

        for r, c in order_moves(board, valid_moves, current_tile):

            flipped = board.apply_move_and_get_flipped(r, c, current_tile)

            eval_score, _ = minimax(
                board, depth - 1, alpha, beta,
                True, player_tile, heuristic_func
            )

            board.undo_move(r, c, current_tile, flipped)

            if eval_score < min_eval:
                min_eval = eval_score
                best_move = (r, c)

            # Beta güncellenir
            beta = min(beta, eval_score)
            if beta <= alpha:
                break  # pruning

        return min_eval, best_move


def get_best_move(board, depth, player_tile, heuristic_func=evaluate_h1):
    # Kök çağrısında maximizing_player her zaman True
    _, best_move = minimax(board, depth, -INF, INF, True, player_tile, heuristic_func)
    return best_move