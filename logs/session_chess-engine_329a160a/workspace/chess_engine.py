"""
Chess Engine with Minimax Algorithm and Alpha-Beta Pruning
A complete CLI-based chess game where you can play against an AI
"""

import copy
from typing import List, Tuple, Optional, Dict
from enum import Enum

class Color(Enum):
    WHITE = 'white'
    BLACK = 'black'

class PieceType(Enum):
    PAWN = 'P'
    KNIGHT = 'N'
    BISHOP = 'B'
    ROOK = 'R'
    QUEEN = 'Q'
    KING = 'K'

class Piece:
    def __init__(self, piece_type: PieceType, color: Color):
        self.piece_type = piece_type
        self.color = color
        self.has_moved = False
    
    def __repr__(self):
        symbol = self.piece_type.value
        return symbol if self.color == Color.WHITE else symbol.lower()
    
    def copy(self):
        piece = Piece(self.piece_type, self.color)
        piece.has_moved = self.has_moved
        return piece

class Board:
    def __init__(self):
        self.board = [[None for _ in range(8)] for _ in range(8)]
        self.setup_initial_position()
        self.move_history = []
        self.white_king_pos = (7, 4)
        self.black_king_pos = (0, 4)
    
    def setup_initial_position(self):
        # Black pieces
        self.board[0][0] = Piece(PieceType.ROOK, Color.BLACK)
        self.board[0][1] = Piece(PieceType.KNIGHT, Color.BLACK)
        self.board[0][2] = Piece(PieceType.BISHOP, Color.BLACK)
        self.board[0][3] = Piece(PieceType.QUEEN, Color.BLACK)
        self.board[0][4] = Piece(PieceType.KING, Color.BLACK)
        self.board[0][5] = Piece(PieceType.BISHOP, Color.BLACK)
        self.board[0][6] = Piece(PieceType.KNIGHT, Color.BLACK)
        self.board[0][7] = Piece(PieceType.ROOK, Color.BLACK)
        
        for col in range(8):
            self.board[1][col] = Piece(PieceType.PAWN, Color.BLACK)
        
        # White pieces
        self.board[7][0] = Piece(PieceType.ROOK, Color.WHITE)
        self.board[7][1] = Piece(PieceType.KNIGHT, Color.WHITE)
        self.board[7][2] = Piece(PieceType.BISHOP, Color.WHITE)
        self.board[7][3] = Piece(PieceType.QUEEN, Color.WHITE)
        self.board[7][4] = Piece(PieceType.KING, Color.WHITE)
        self.board[7][5] = Piece(PieceType.BISHOP, Color.WHITE)
        self.board[7][6] = Piece(PieceType.KNIGHT, Color.WHITE)
        self.board[7][7] = Piece(PieceType.ROOK, Color.WHITE)
        
        for col in range(8):
            self.board[6][col] = Piece(PieceType.PAWN, Color.WHITE)
    
    def display(self):
        print("\n   a  b  c  d  e  f  g  h")
        print("  ------------------------")
        for row in range(8):
            print(f"{8-row} |", end="")
            for col in range(8):
                piece = self.board[row][col]
                if piece:
                    print(f"{piece!r} ", end=" ")
                else:
                    print(". ", end=" ")
            print(f"| {8-row}")
        print("  ------------------------")
        print("   a  b  c  d  e  f  g  h\n")
    
    def is_valid_position(self, row: int, col: int) -> bool:
        return 0 <= row < 8 and 0 <= col < 8
    
    def get_piece(self, row: int, col: int) -> Optional[Piece]:
        if self.is_valid_position(row, col):
            return self.board[row][col]
        return None
    
    def copy(self):
        new_board = Board.__new__(Board)
        new_board.board = [[None for _ in range(8)] for _ in range(8)]
        for row in range(8):
            for col in range(8):
                if self.board[row][col]:
                    new_board.board[row][col] = self.board[row][col].copy()
        new_board.move_history = self.move_history.copy()
        new_board.white_king_pos = self.white_king_pos
        new_board.black_king_pos = self.black_king_pos
        return new_board
    
    def make_move(self, from_pos: Tuple[int, int], to_pos: Tuple[int, int]) -> bool:
        from_row, from_col = from_pos
        to_row, to_col = to_pos
        
        piece = self.board[from_row][from_col]
        if not piece:
            return False
        
        # Update king position
        if piece.piece_type == PieceType.KING:
            if piece.color == Color.WHITE:
                self.white_king_pos = to_pos
            else:
                self.black_king_pos = to_pos
        
        # Record move
        captured = self.board[to_row][to_col]
        self.move_history.append((from_pos, to_pos, captured))
        
        # Make move
        self.board[to_row][to_col] = piece
        self.board[from_row][from_col] = None
        piece.has_moved = True
        
        return True
    
    def get_possible_moves(self, row: int, col: int) -> List[Tuple[int, int]]:
        piece = self.get_piece(row, col)
        if not piece:
            return []
        
        moves = []
        
        if piece.piece_type == PieceType.PAWN:
            moves = self._get_pawn_moves(row, col, piece)
        elif piece.piece_type == PieceType.KNIGHT:
            moves = self._get_knight_moves(row, col, piece)
        elif piece.piece_type == PieceType.BISHOP:
            moves = self._get_bishop_moves(row, col, piece)
        elif piece.piece_type == PieceType.ROOK:
            moves = self._get_rook_moves(row, col, piece)
        elif piece.piece_type == PieceType.QUEEN:
            moves = self._get_queen_moves(row, col, piece)
        elif piece.piece_type == PieceType.KING:
            moves = self._get_king_moves(row, col, piece)
        
        # Filter out moves that would put own king in check
        legal_moves = []
        for move in moves:
            temp_board = self.copy()
            temp_board.make_move((row, col), move)
            if not temp_board.is_in_check(piece.color):
                legal_moves.append(move)
        
        return legal_moves
    
    def _get_pawn_moves(self, row: int, col: int, piece: Piece) -> List[Tuple[int, int]]:
        moves = []
        direction = -1 if piece.color == Color.WHITE else 1
        start_row = 6 if piece.color == Color.WHITE else 1
        
        # Forward move
        new_row = row + direction
        if self.is_valid_position(new_row, col) and not self.board[new_row][col]:
            moves.append((new_row, col))
            
            # Double move from start
            if row == start_row:
                new_row2 = row + 2 * direction
                if not self.board[new_row2][col]:
                    moves.append((new_row2, col))
        
        # Captures
        for dc in [-1, 1]:
            new_row = row + direction
            new_col = col + dc
            if self.is_valid_position(new_row, new_col):
                target = self.board[new_row][new_col]
                if target and target.color != piece.color:
                    moves.append((new_row, new_col))
        
        return moves
    
    def _get_knight_moves(self, row: int, col: int, piece: Piece) -> List[Tuple[int, int]]:
        moves = []
        knight_moves = [
            (-2, -1), (-2, 1), (-1, -2), (-1, 2),
            (1, -2), (1, 2), (2, -1), (2, 1)
        ]
        
        for dr, dc in knight_moves:
            new_row, new_col = row + dr, col + dc
            if self.is_valid_position(new_row, new_col):
                target = self.board[new_row][new_col]
                if not target or target.color != piece.color:
                    moves.append((new_row, new_col))
        
        return moves
    
    def _get_bishop_moves(self, row: int, col: int, piece: Piece) -> List[Tuple[int, int]]:
        return self._get_sliding_moves(row, col, piece, [(-1, -1), (-1, 1), (1, -1), (1, 1)])
    
    def _get_rook_moves(self, row: int, col: int, piece: Piece) -> List[Tuple[int, int]]:
        return self._get_sliding_moves(row, col, piece, [(-1, 0), (1, 0), (0, -1), (0, 1)])
    
    def _get_queen_moves(self, row: int, col: int, piece: Piece) -> List[Tuple[int, int]]:
        return self._get_sliding_moves(row, col, piece, [
            (-1, -1), (-1, 0), (-1, 1), (0, -1),
            (0, 1), (1, -1), (1, 0), (1, 1)
        ])
    
    def _get_sliding_moves(self, row: int, col: int, piece: Piece, 
                          directions: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
        moves = []
        
        for dr, dc in directions:
            new_row, new_col = row + dr, col + dc
            while self.is_valid_position(new_row, new_col):
                target = self.board[new_row][new_col]
                if not target:
                    moves.append((new_row, new_col))
                elif target.color != piece.color:
                    moves.append((new_row, new_col))
                    break
                else:
                    break
                new_row += dr
                new_col += dc
        
        return moves
    
    def _get_king_moves(self, row: int, col: int, piece: Piece) -> List[Tuple[int, int]]:
        moves = []
        king_moves = [
            (-1, -1), (-1, 0), (-1, 1), (0, -1),
            (0, 1), (1, -1), (1, 0), (1, 1)
        ]
        
        for dr, dc in king_moves:
            new_row, new_col = row + dr, col + dc
            if self.is_valid_position(new_row, new_col):
                target = self.board[new_row][new_col]
                if not target or target.color != piece.color:
                    moves.append((new_row, new_col))
        
        return moves
    
    def is_in_check(self, color: Color) -> bool:
        # Find king position
        king_pos = self.white_king_pos if color == Color.WHITE else self.black_king_pos
        king_row, king_col = king_pos
        
        # Check if any opponent piece can attack the king
        opponent_color = Color.BLACK if color == Color.WHITE else Color.WHITE
        
        for row in range(8):
            for col in range(8):
                piece = self.board[row][col]
                if piece and piece.color == opponent_color:
                    # Get moves without check validation to avoid infinite recursion
                    if piece.piece_type == PieceType.PAWN:
                        moves = self._get_pawn_attacks(row, col, piece)
                    elif piece.piece_type == PieceType.KNIGHT:
                        moves = self._get_knight_moves(row, col, piece)
                    elif piece.piece_type == PieceType.BISHOP:
                        moves = self._get_bishop_moves(row, col, piece)
                    elif piece.piece_type == PieceType.ROOK:
                        moves = self._get_rook_moves(row, col, piece)
                    elif piece.piece_type == PieceType.QUEEN:
                        moves = self._get_queen_moves(row, col, piece)
                    elif piece.piece_type == PieceType.KING:
                        moves = self._get_king_moves(row, col, piece)
                    else:
                        moves = []
                    
                    if king_pos in moves:
                        return True
        
        return False
    
    def _get_pawn_attacks(self, row: int, col: int, piece: Piece) -> List[Tuple[int, int]]:
        moves = []
        direction = -1 if piece.color == Color.WHITE else 1
        
        for dc in [-1, 1]:
            new_row = row + direction
            new_col = col + dc
            if self.is_valid_position(new_row, new_col):
                moves.append((new_row, new_col))
        
        return moves
    
    def is_checkmate(self, color: Color) -> bool:
        if not self.is_in_check(color):
            return False
        
        # Check if any move can get out of check
        for row in range(8):
            for col in range(8):
                piece = self.board[row][col]
                if piece and piece.color == color:
                    moves = self.get_possible_moves(row, col)
                    if moves:
                        return False
        
        return True
    
    def is_stalemate(self, color: Color) -> bool:
        if self.is_in_check(color):
            return False
        
        # Check if any legal move exists
        for row in range(8):
            for col in range(8):
                piece = self.board[row][col]
                if piece and piece.color == color:
                    moves = self.get_possible_moves(row, col)
                    if moves:
                        return False
        
        return True
    
    def get_all_legal_moves(self, color: Color) -> List[Tuple[Tuple[int, int], Tuple[int, int]]]:
        moves = []
        for row in range(8):
            for col in range(8):
                piece = self.board[row][col]
                if piece and piece.color == color:
                    piece_moves = self.get_possible_moves(row, col)
                    for move in piece_moves:
                        moves.append(((row, col), move))
        return moves

class ChessAI:
    # Piece values for evaluation
    PIECE_VALUES = {
        PieceType.PAWN: 100,
        PieceType.KNIGHT: 320,
        PieceType.BISHOP: 330,
        PieceType.ROOK: 500,
        PieceType.QUEEN: 900,
        PieceType.KING: 20000
    }
    
    # Position tables for piece-square evaluation
    PAWN_TABLE = [
        [0,  0,  0,  0,  0,  0,  0,  0],
        [50, 50, 50, 50, 50, 50, 50, 50],
        [10, 10, 20, 30, 30, 20, 10, 10],
        [5,  5, 10, 25, 25, 10,  5,  5],
        [0,  0,  0, 20, 20,  0,  0,  0],
        [5, -5,-10,  0,  0,-10, -5,  5],
        [5, 10, 10,-20,-20, 10, 10,  5],
        [0,  0,  0,  0,  0,  0,  0,  0]
    ]
    
    KNIGHT_TABLE = [
        [-50,-40,-30,-30,-30,-30,-40,-50],
        [-40,-20,  0,  0,  0,  0,-20,-40],
        [-30,  0, 10, 15, 15, 10,  0,-30],
        [-30,  5, 15, 20, 20, 15,  5,-30],
        [-30,  0, 15, 20, 20, 15,  0,-30],
        [-30,  5, 10, 15, 15, 10,  5,-30],
        [-40,-20,  0,  5,  5,  0,-20,-40],
        [-50,-40,-30,-30,-30,-30,-40,-50]
    ]
    
    def __init__(self, depth: int = 3):
        self.depth = depth
        self.nodes_evaluated = 0
    
    def evaluate_board(self, board: Board, color: Color) -> int:
        """
        Evaluate the board position from the perspective of the given color.
        Positive scores are good for the color, negative scores are bad.
        """
        if board.is_checkmate(color):
            return -999999
        if board.is_checkmate(Color.WHITE if color == Color.BLACK else Color.BLACK):
            return 999999
        
        score = 0
        
        for row in range(8):
            for col in range(8):
                piece = board.board[row][col]
                if piece:
                    piece_value = self.PIECE_VALUES[piece.piece_type]
                    
                    # Add position bonus
                    if piece.piece_type == PieceType.PAWN:
                        pos_row = row if piece.color == Color.BLACK else 7 - row
                        piece_value += self.PAWN_TABLE[pos_row][col]
                    elif piece.piece_type == PieceType.KNIGHT:
                        pos_row = row if piece.color == Color.BLACK else 7 - row
                        piece_value += self.KNIGHT_TABLE[pos_row][col]
                    
                    if piece.color == color:
                        score += piece_value
                    else:
                        score -= piece_value
        
        return score
    
    def minimax(self, board: Board, depth: int, alpha: int, beta: int, 
                maximizing: bool, color: Color) -> Tuple[int, Optional[Tuple]]:
        """
        Minimax algorithm with alpha-beta pruning.
        Returns (evaluation, best_move)
        """
        self.nodes_evaluated += 1
        
        if depth == 0:
            return self.evaluate_board(board, color), None
        
        current_color = color if maximizing else (Color.BLACK if color == Color.WHITE else Color.WHITE)
        legal_moves = board.get_all_legal_moves(current_color)
        
        if not legal_moves:
            if board.is_in_check(current_color):
                # Checkmate
                return (-999999 if maximizing else 999999), None
            else:
                # Stalemate
                return 0, None
        
        best_move = None
        
        if maximizing:
            max_eval = float('-inf')
            for from_pos, to_pos in legal_moves:
                temp_board = board.copy()
                temp_board.make_move(from_pos, to_pos)
                
                eval_score, _ = self.minimax(temp_board, depth - 1, alpha, beta, False, color)
                
                if eval_score > max_eval:
                    max_eval = eval_score
                    best_move = (from_pos, to_pos)
                
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break  # Beta cutoff
            
            return max_eval, best_move
        else:
            min_eval = float('inf')
            for from_pos, to_pos in legal_moves:
                temp_board = board.copy()
                temp_board.make_move(from_pos, to_pos)
                
                eval_score, _ = self.minimax(temp_board, depth - 1, alpha, beta, True, color)
                
                if eval_score < min_eval:
                    min_eval = eval_score
                    best_move = (from_pos, to_pos)
                
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break  # Alpha cutoff
            
            return min_eval, best_move
    
    def get_best_move(self, board: Board, color: Color) -> Optional[Tuple]:
        """Get the best move for the given color using minimax with alpha-beta pruning."""
        self.nodes_evaluated = 0
        _, best_move = self.minimax(board, self.depth, float('-inf'), float('inf'), True, color)
        print(f"Nodes evaluated: {self.nodes_evaluated}")
        return best_move

class ChessGame:
    def __init__(self, ai_depth: int = 3):
        self.board = Board()
        self.ai = ChessAI(depth=ai_depth)
        self.current_player = Color.WHITE
        self.game_over = False
    
    def parse_position(self, pos_str: str) -> Optional[Tuple[int, int]]:
        """Convert chess notation (e.g., 'e2') to board coordinates."""
        if len(pos_str) != 2:
            return None
        
        col = ord(pos_str[0].lower()) - ord('a')
        row = 8 - int(pos_str[1])
        
        if self.board.is_valid_position(row, col):
            return (row, col)
        return None
    
    def position_to_notation(self, pos: Tuple[int, int]) -> str:
        """Convert board coordinates to chess notation."""
        row, col = pos
        return f"{chr(ord('a') + col)}{8 - row}"
    
    def play_human_turn(self):
        """Handle human player's turn."""
        print(f"\n{self.current_player.value.upper()}'s turn")
        
        while True:
            from_input = input("Enter piece position (e.g., e2) or 'quit': ").strip()
            if from_input.lower() == 'quit':
                self.game_over = True
                return
            
            from_pos = self.parse_position(from_input)
            if not from_pos:
                print("Invalid position. Try again.")
                continue
            
            piece = self.board.get_piece(*from_pos)
            if not piece:
                print("No piece at that position. Try again.")
                continue
            
            if piece.color != self.current_player:
                print(f"That's not your piece! You are playing {self.current_player.value}.")
                continue
            
            legal_moves = self.board.get_possible_moves(*from_pos)
            if not legal_moves:
                print("That piece has no legal moves. Try another piece.")
                continue
            
            print(f"Legal moves: {', '.join(self.position_to_notation(m) for m in legal_moves)}")
            
            to_input = input("Enter destination (e.g., e4) or 'back': ").strip()
            if to_input.lower() == 'back':
                continue
            
            to_pos = self.parse_position(to_input)
            if not to_pos:
                print("Invalid position. Try again.")
                continue
            
            if to_pos not in legal_moves:
                print("Illegal move. Try again.")
                continue
            
            self.board.make_move(from_pos, to_pos)
            print(f"Moved {piece.piece_type.value} from {from_input} to {to_input}")
            break
    
    def play_ai_turn(self):
        """Handle AI's turn."""
        print(f"\n{self.current_player.value.upper()}'s turn (AI thinking...)")
        
        move = self.ai.get_best_move(self.board, self.current_player)
        if move:
            from_pos, to_pos = move
            piece = self.board.get_piece(*from_pos)
            self.board.make_move(from_pos, to_pos)
            print(f"AI moved {piece.piece_type.value} from {self.position_to_notation(from_pos)} "
                  f"to {self.position_to_notation(to_pos)}")
        else:
            print("AI has no legal moves!")
            self.game_over = True
    
    def check_game_end(self):
        """Check if the game has ended."""
        if self.board.is_checkmate(self.current_player):
            winner = Color.BLACK if self.current_player == Color.WHITE else Color.WHITE
            print(f"\n*** CHECKMATE! {winner.value.upper()} wins! ***")
            self.game_over = True
            return
        
        if self.board.is_stalemate(self.current_player):
            print("\n*** STALEMATE! It's a draw! ***")
            self.game_over = True
            return
        
        if self.board.is_in_check(self.current_player):
            print(f"\n>>> {self.current_player.value.upper()} is in CHECK! <<<")
    
    def switch_player(self):
        """Switch to the other player."""
        self.current_player = Color.BLACK if self.current_player == Color.WHITE else Color.WHITE
    
    def play(self, human_color: Color = Color.WHITE):
        """Main game loop."""
        print("=" * 50)
        print("   CHESS ENGINE with Minimax & Alpha-Beta Pruning")
        print("=" * 50)
        print(f"\nYou are playing as {human_color.value.upper()}")
        print("Enter moves in chess notation (e.g., e2 to e4)")
        print("Type 'quit' to exit the game\n")
        
        while not self.game_over:
            self.board.display()
            self.check_game_end()
            
            if self.game_over:
                break
            
            if self.current_player == human_color:
                self.play_human_turn()
            else:
                self.play_ai_turn()
            
            if not self.game_over:
                self.switch_player()
        
        print("\nThanks for playing!")

def main():
    print("Chess Engine - Minimax with Alpha-Beta Pruning")
    print("=" * 50)
    
    # Choose color
    while True:
        color_choice = input("Choose your color (w/b): ").strip().lower()
        if color_choice == 'w':
            human_color = Color.WHITE
            break
        elif color_choice == 'b':
            human_color = Color.BLACK
            break
        else:
            print("Invalid choice. Enter 'w' for white or 'b' for black.")
    
    # Choose difficulty
    while True:
        try:
            difficulty = input("Choose AI difficulty (1-5, higher is harder): ").strip()
            depth = int(difficulty)
            if 1 <= depth <= 5:
                break
            else:
                print("Please enter a number between 1 and 5.")
        except ValueError:
            print("Invalid input. Please enter a number.")
    
    # Start game
    game = ChessGame(ai_depth=depth)
    game.play(human_color=human_color)

if __name__ == "__main__":
    main()
