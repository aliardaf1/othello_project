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
    Heuristic 2: Konumsal Ağırlıklar
    Tahtadaki her taş için:
    - Benim taşım ise o karenin ağırlığını ekle,
    - Rakibin taşı ise o karenin ağırlığını çıkar.
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

def evaluate_h3(board, player_tile):
    """
    Heuristic 3: Hareketlilik (Mobility)
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


# extra olarak eklediğimiz bir fonksiyon
# öncekilere göre daha kompleks
# 4 farklı heuristic'in birleşimi olarak çalışıyor
def evaluate_hybrid(board, player_tile):
    """
    Hybrid heuristic:
    - Mobility
    - Corner control
    - Positional weights
    - Coin parity (late game)
    """

    # oyunun hangi fazda olduğunu taş sayısına göre belirliyor
    black, white = board.get_score()
    total_discs = black + white

    # Bileşenler
    parity = coin_parity(board, player_tile)
    mob = mobility(board, player_tile)
    pos = positional_score(board, player_tile)

    my_corners, opp_corners = count_corners(board, player_tile)
    corner_score = 25 * (my_corners - opp_corners)

    # --- Ağırlıklandırma ---
    # Early / Mid game
    if total_discs < 40:
        return (
            1.0 * mob +
            1.0 * corner_score +
            0.5 * pos
        )

    # Late game
    else:
        return (
            2.0 * parity +
            0.5 * mob +
            1.5 * corner_score
        )

def evaluate_ultimate(board, player_tile):
    """
    Ultimate (phase-aware) heuristic adapted to THIS codebase:
    - Mobility (existing move generator)
    - Potential mobility (adjacent empties pressure)
    - Corner control
    - Corner danger (X/C squares when corner is empty)
    - Stability (cheap corner/edge-anchored approximation)
    - Frontier penalty (discs adjacent to empties are weak)
    - Positional weights (early/mid)
    - Coin parity / disc difference (late)

    Uses:
      - board.grid (8x8)
      - EMPTY = '.'
      - BLACK/WHITE constants
      - BOARD_SIZE
    """

    opponent_tile = WHITE if player_tile == BLACK else BLACK
    grid = board.grid
    EMPTY = '.'

    # -------------------- Phase detection --------------------
    black, white = board.get_score()
    total_discs = black + white
    empties = BOARD_SIZE * BOARD_SIZE - total_discs

    # -------------------- Core components --------------------
    # Mobility (normalized -100..100 like your evaluate_h3)
    my_moves = len(board.get_valid_moves(player_tile))
    opp_moves = len(board.get_valid_moves(opponent_tile))
    if my_moves + opp_moves == 0:
        M = 0.0
    else:
        M = 100.0 * (my_moves - opp_moves) / (my_moves + opp_moves)

    # Positional score (reuse your table)
    PS = positional_score(board, player_tile)

    # Corner control
    my_corners, opp_corners = count_corners(board, player_tile)
    C = 25.0 * (my_corners - opp_corners)

    # Coin parity (your existing definition: disc diff normalized)
    D = coin_parity(board, player_tile)

    # -------------------- Extra components (implemented here) --------------------
    directions8 = [(-1,-1), (-1,0), (-1,1),
                   ( 0,-1),         ( 0,1),
                   ( 1,-1), ( 1,0), ( 1,1)]

    def in_bounds(r, c):
        return 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE

    # Potential mobility:
    # We count empty squares adjacent to opponent discs minus empty squares adjacent to my discs,
    # then invert so "higher is better for us".
    def potential_mobility():
        my_adj = 0
        opp_adj = 0

        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if grid[r][c] != EMPTY:
                    continue

                adj_my = False
                adj_opp = False
                for dr, dc in directions8:
                    rr, cc = r + dr, c + dc
                    if not in_bounds(rr, cc):
                        continue
                    if grid[rr][cc] == player_tile:
                        adj_my = True
                    elif grid[rr][cc] == opponent_tile:
                        adj_opp = True

                if adj_my:
                    my_adj += 1
                if adj_opp:
                    opp_adj += 1

        # if opp has many adjacent empties, it's bad (they'll have mobility),
        # so return negative of that difference.
        return float(-(opp_adj - my_adj))

    PM = potential_mobility()

    # Frontier: discs adjacent to empties are frontier (weak).
    # We return (oppFrontier - myFrontier) so higher is better for us.
    def frontier_score():
        def is_frontier(r, c):
            for dr, dc in directions8:
                rr, cc = r + dr, c + dc
                if in_bounds(rr, cc) and grid[rr][cc] == EMPTY:
                    return True
            return False

        my_f = 0
        opp_f = 0
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if grid[r][c] == player_tile and is_frontier(r, c):
                    my_f += 1
                elif grid[r][c] == opponent_tile and is_frontier(r, c):
                    opp_f += 1
        return float(opp_f - my_f)

    F = frontier_score()

    # Corner danger: X-square + C-squares penalties if corner is empty
    def corner_danger():
        score = 0.0
        corner_specs = [
            # corner, X, C-squares
            ((0, 0), (1, 1), [(0, 1), (1, 0)]),
            ((0, 7), (1, 6), [(0, 6), (1, 7)]),
            ((7, 0), (6, 1), [(6, 0), (7, 1)]),
            ((7, 7), (6, 6), [(6, 7), (7, 6)]),
        ]

        for (cr, cc), (xr, xc), cs in corner_specs:
            if grid[cr][cc] != EMPTY:
                continue  # corner taken -> danger mostly gone

            # X-square is very risky while corner is empty
            if grid[xr][xc] == player_tile:
                score -= 12.0
            elif grid[xr][xc] == opponent_tile:
                score += 12.0

            # C-squares are also risky
            for rr, cc2 in cs:
                if grid[rr][cc2] == player_tile:
                    score -= 8.0
                elif grid[rr][cc2] == opponent_tile:
                    score += 8.0

        return score

    CD = corner_danger()

    # Stability (cheap approximation):
    # count discs that are continuous from owned corners along edges.
    # returns normalized-ish [-100..100]
    def stability_approx():
        corners = [(0, 0), (0, 7), (7, 0), (7, 7)]

        def stable_from_corner(cr, cc, who):
            if grid[cr][cc] != who:
                return 0

            cnt = 1  # corner itself
            if (cr, cc) == (0, 0):
                edge_dirs = [(0, 1), (1, 0)]
            elif (cr, cc) == (0, 7):
                edge_dirs = [(0, -1), (1, 0)]
            elif (cr, cc) == (7, 0):
                edge_dirs = [(0, 1), (-1, 0)]
            else:
                edge_dirs = [(0, -1), (-1, 0)]

            for dr, dc in edge_dirs:
                r, c = cr + dr, cc + dc
                while in_bounds(r, c) and grid[r][c] == who:
                    cnt += 1
                    r += dr
                    c += dc
            return cnt

        my_s = 0
        opp_s = 0
        for cr, cc in corners:
            my_s += stable_from_corner(cr, cc, player_tile)
            opp_s += stable_from_corner(cr, cc, opponent_tile)

        denom = my_s + opp_s
        if denom == 0:
            return 0.0
        return 100.0 * (my_s - opp_s) / (denom + 1.0)

    S = stability_approx()

    # -------------------- Phase-aware weights --------------------
    # Opening: empties > 44
    if empties > 44:
        wM, wPM, wC, wCD, wS, wF, wPS, wD = (35.0, 15.0, 20.0, 10.0,  0.0, 10.0, 10.0,  0.0)
    # Midgame: 20..44
    elif empties >= 20:
        wM, wPM, wC, wCD, wS, wF, wPS, wD = (25.0, 10.0, 25.0, 10.0, 15.0, 10.0,  5.0,  0.0)
    # Endgame: empties < 20
    else:
        # Late game: positional table becomes noise; disc difference dominates more
        wM, wPM, wC, wCD, wS, wF, wPS, wD = ( 5.0,  0.0, 25.0,  5.0, 20.0,  0.0,  0.0, 30.0)

    # -------------------- Final score --------------------
    return (
        wM  * M  +
        wPM * PM +
        wC  * C  +
        wCD * CD +
        wS  * S  +
        wF  * F  +
        wPS * PS +
        wD  * D
    )



# -------------- ESKİ HEURİSTİKLER --------------



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



def count_corners(board, player_tile):
    opponent_tile = WHITE if player_tile == BLACK else BLACK
    corners = [(0,0), (0,7), (7,0), (7,7)]

    my_corners = 0
    opp_corners = 0

    for r, c in corners:
        if board.grid[r][c] == player_tile:
            my_corners += 1
        elif board.grid[r][c] == opponent_tile:
            opp_corners += 1

    return my_corners, opp_corners


def coin_parity(board, player_tile):
    black, white = board.get_score()

    if black + white == 0:
        return 0

    if player_tile == BLACK:
        return 100 * (black - white) / (black + white)
    else:
        return 100 * (white - black) / (black + white)


def mobility(board, player_tile):
    opponent_tile = WHITE if player_tile == BLACK else BLACK

    my_moves = len(board.get_valid_moves(player_tile))
    opp_moves = len(board.get_valid_moves(opponent_tile))

    if my_moves + opp_moves == 0:
        return 0

    return 100 * (my_moves - opp_moves) / (my_moves + opp_moves)


def positional_score(board, player_tile):
    opponent_tile = WHITE if player_tile == BLACK else BLACK
    score = 0

    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board.grid[r][c] == player_tile:
                score += POSITION_WEIGHTS[r][c]
            elif board.grid[r][c] == opponent_tile:
                score -= POSITION_WEIGHTS[r][c]

    return score



