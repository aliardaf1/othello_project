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
    "Ultimate" hybrid heuristic (phase-aware):
    - Mobility
    - Potential mobility
    - Corner control
    - Corner danger (X/C squares when corner is empty)
    - Stability (approx; corner/edge anchored stable discs)
    - Frontier penalty
    - Parity (late game)
    - Positional weights (early/mid only)
    - Disc difference (late game)

    Assumptions about `board`:
      - board.board is an 8x8 list-of-lists (or similar) containing tile chars or empty marker
      - board.get_score() -> (black, white)
      - board.get_valid_moves(tile) -> list of moves (r,c)
      - board.is_on_board(r,c) -> bool   (optional; we guard anyway)

    If your Board API differs, adjust the few access points noted below.
    """

    # -------------------- Helpers (self-contained) --------------------
    def opp(tile: str) -> str:
        return 'O' if tile == 'X' else 'X'

    def empty_of(b):
        # Detect empty marker used by your board. Common: ' ' or '.' or None.
        # We'll infer from board.board contents if possible.
        # Fallback to ' '.
        for r in range(8):
            for c in range(8):
                v = b[r][c]
                if v not in ('X', 'O'):
                    return v
        return ' '

    def in_bounds(r, c) -> bool:
        return 0 <= r < 8 and 0 <= c < 8

    def get_grid(board_obj):
        # Adjust here if your board uses a different field name.
        return board_obj.board

    def count_discs(grid, tile, empty):
        cnt = 0
        for r in range(8):
            for c in range(8):
                if grid[r][c] == tile:
                    cnt += 1
        return cnt

    def disc_diff_percent(my_discs, opp_discs):
        denom = my_discs + opp_discs
        if denom == 0:
            return 0.0
        return 100.0 * (my_discs - opp_discs) / denom

    def mobility_score(board_obj, tile):
        my_moves = len(board_obj.get_valid_moves(tile))
        op_moves = len(board_obj.get_valid_moves(opp(tile)))
        return 100.0 * (my_moves - op_moves) / (my_moves + op_moves + 1.0)

    def potential_mobility_score(grid, tile, empty):
        # empty squares adjacent to opponent discs minus empty squares adjacent to my discs
        my_adj = 0
        op_adj = 0
        o = opp(tile)
        for r in range(8):
            for c in range(8):
                if grid[r][c] != empty:
                    continue
                # check 8-neighborhood
                adj_my = False
                adj_op = False
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        if dr == 0 and dc == 0:
                            continue
                        rr, cc = r + dr, c + dc
                        if not in_bounds(rr, cc):
                            continue
                        if grid[rr][cc] == tile:
                            adj_my = True
                        elif grid[rr][cc] == o:
                            adj_op = True
                if adj_my:
                    my_adj += 1
                if adj_op:
                    op_adj += 1
        # Positive means better for us (op has more adjacent empties => we penalize that), so invert:
        # We want: (#empties next to opp) - (#empties next to me) as described earlier, but since that is
        # "bad when positive", we return its negative so higher is better for us.
        return float(-(op_adj - my_adj))

    def corner_control_score(grid, tile):
        o = opp(tile)
        corners = [(0, 0), (0, 7), (7, 0), (7, 7)]
        my_c = 0
        op_c = 0
        for r, c in corners:
            if grid[r][c] == tile:
                my_c += 1
            elif grid[r][c] == o:
                op_c += 1
        # strong, unnormalized
        return 25.0 * (my_c - op_c)

    def corner_danger_score(grid, tile, empty):
        """
        Penalize owning X/C squares when corner is empty.
        X-squares: diagonals adjacent to corner
        C-squares: edge-adjacent to corner
        """
        o = opp(tile)

        corner_specs = [
            # corner, X-square, C-squares
            ((0, 0), (1, 1), [(0, 1), (1, 0)]),
            ((0, 7), (1, 6), [(0, 6), (1, 7)]),
            ((7, 0), (6, 1), [(6, 0), (7, 1)]),
            ((7, 7), (6, 6), [(6, 7), (7, 6)]),
        ]

        score = 0.0
        for (cr, cc), (xr, xc), cs in corner_specs:
            if grid[cr][cc] != empty:
                continue  # corner already taken -> danger patterns largely irrelevant

            # If we occupy X-square while corner empty: bad for us
            if grid[xr][xc] == tile:
                score -= 12.0
            elif grid[xr][xc] == o:
                score += 12.0

            # C-squares are also risky but slightly less than X in many positions
            for (rr, cc2) in cs:
                if grid[rr][cc2] == tile:
                    score -= 8.0
                elif grid[rr][cc2] == o:
                    score += 8.0

        return score

    def positional_score_weighted(grid, tile, empty):
        # Classic table; used mainly early/mid.
        W = [
            [120, -20,  20,   5,   5,  20, -20, 120],
            [-20, -40,  -5,  -5,  -5,  -5, -40, -20],
            [ 20,  -5,  15,   3,   3,  15,  -5,  20],
            [  5,  -5,   3,   3,   3,   3,  -5,   5],
            [  5,  -5,   3,   3,   3,   3,  -5,   5],
            [ 20,  -5,  15,   3,   3,  15,  -5,  20],
            [-20, -40,  -5,  -5,  -5,  -5, -40, -20],
            [120, -20,  20,   5,   5,  20, -20, 120],
        ]
        o = opp(tile)
        s = 0.0
        for r in range(8):
            for c in range(8):
                if grid[r][c] == tile:
                    s += W[r][c]
                elif grid[r][c] == o:
                    s -= W[r][c]
        return s

    def frontier_score(grid, tile, empty):
        # We return (oppFrontier - myFrontier) so higher is better (penalize our frontier).
        o = opp(tile)

        def is_frontier(r, c):
            # disc adjacent to at least one empty
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == 0 and dc == 0:
                        continue
                    rr, cc = r + dr, c + dc
                    if not in_bounds(rr, cc):
                        continue
                    if grid[rr][cc] == empty:
                        return True
            return False

        my_f = 0
        op_f = 0
        for r in range(8):
            for c in range(8):
                if grid[r][c] == tile and is_frontier(r, c):
                    my_f += 1
                elif grid[r][c] == o and is_frontier(r, c):
                    op_f += 1

        return float(op_f - my_f)

    def parity_score(board_obj, tile):
        # Standard parity: prefer being the player who moves last.
        # If you already have coin_parity(board, tile), you can replace this.
        grid = get_grid(board_obj)
        empty = empty_of(grid)
        empties = 0
        for r in range(8):
            for c in range(8):
                if grid[r][c] == empty:
                    empties += 1

        # Determine side to move if your board tracks it; otherwise approximate with "tile is to move".
        # If your engine always calls evaluate with the maximizing player perspective, this is ok.
        # Parity: if empties is odd, side to move gets last move; if even, opponent gets last move.
        # So being side-to-move is good when empties is odd.
        return 1.0 if (empties % 2 == 1) else -1.0

    def stability_score_approx(grid, tile, empty):
        """
        Approximate stability:
        - Count discs that are edge-connected to an owned corner along continuous lines.
        - This is not full stability, but is a strong, low-cost proxy.

        Returns a normalized percent-style score in [-100,100].
        """
        o = opp(tile)
        corners = [(0, 0), (0, 7), (7, 0), (7, 7)]

        def stable_from_corner(cr, cc, who):
            # Count stable discs along the two edges from this corner for `who`
            if grid[cr][cc] != who:
                return 0

            cnt = 1  # corner itself
            # directions along edges
            dirs = []
            if (cr, cc) == (0, 0):
                dirs = [(0, 1), (1, 0)]
            elif (cr, cc) == (0, 7):
                dirs = [(0, -1), (1, 0)]
            elif (cr, cc) == (7, 0):
                dirs = [(0, 1), (-1, 0)]
            else:  # (7,7)
                dirs = [(0, -1), (-1, 0)]

            for dr, dc in dirs:
                rr, cc2 = cr + dr, cc + dc
                while in_bounds(rr, cc2) and grid[rr][cc2] == who:
                    cnt += 1
                    rr += dr
                    cc2 += dc
            return cnt

        my_stable = 0
        op_stable = 0
        for cr, cc in corners:
            my_stable += stable_from_corner(cr, cc, tile)
            op_stable += stable_from_corner(cr, cc, o)

        denom = my_stable + op_stable
        if denom == 0:
            return 0.0
        return 100.0 * (my_stable - op_stable) / (denom + 1.0)

    # -------------------- Phase detection --------------------
    grid = get_grid(board)
    empty = empty_of(grid)

    black, white = board.get_score()
    total_discs = black + white
    empties = 64 - total_discs

    # Disc counts from the perspective of player_tile
    my_discs = count_discs(grid, player_tile, empty)
    opp_discs = total_discs - my_discs

    # -------------------- Components --------------------
    M  = mobility_score(board, player_tile)                          # normalized
    PM = potential_mobility_score(grid, player_tile, empty)          # raw-ish
    C  = corner_control_score(grid, player_tile)                     # strong raw
    CD = corner_danger_score(grid, player_tile, empty)               # raw penalties/bonuses
    S  = stability_score_approx(grid, player_tile, empty)            # normalized-ish
    F  = frontier_score(grid, player_tile, empty)                    # raw difference
    P  = parity_score(board, player_tile)                            # +/-1
    PS = positional_score_weighted(grid, player_tile, empty)         # raw table
    D  = disc_diff_percent(my_discs, opp_discs)                      # normalized

    # -------------------- Phase-aware weights --------------------
    # Opening: empties > 44
    if empties > 44:
        wM, wPM, wC, wCD, wS, wF, wP, wPS, wD = (
            35.0, 15.0, 20.0, 10.0,  0.0, 10.0, 0.0, 10.0, 0.0
        )
        # Note: PS is meaningful early; D is not.

    # Midgame: 20..44
    elif empties >= 20:
        wM, wPM, wC, wCD, wS, wF, wP, wPS, wD = (
            25.0, 10.0, 25.0, 10.0, 15.0, 10.0, 0.0,  5.0, 0.0
        )

    # Endgame: empties < 20
    else:
        wM, wPM, wC, wCD, wS, wF, wP, wPS, wD = (
             5.0,  0.0, 25.0,  5.0, 20.0,  0.0, 15.0, 0.0, 30.0
        )

    # -------------------- Final score --------------------
    # All terms are arranged so "higher is better" for player_tile.
    score = (
        wM  * M  +
        wPM * PM +
        wC  * C  +
        wCD * CD +
        wS  * S  +
        wF  * F  +
        wP  * P  +
        wPS * PS +
        wD  * D
    )

    return score



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



