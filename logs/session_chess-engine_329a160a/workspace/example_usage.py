"""
Example usage of the chess engine components
Shows how to use the engine programmatically
"""

from chess_engine import Board, ChessAI, Color, ChessGame

def example_1_basic_board():
    """Example 1: Create and display a chess board"""
    print("Example 1: Basic Board Setup")
    print("-" * 40)
    
    board = Board()
    board.display()
    print("✓ Board created and displayed\n")

def example_2_get_moves():
    """Example 2: Get legal moves for a piece"""
    print("Example 2: Get Legal Moves")
    print("-" * 40)
    
    board = Board()
    
    # Get moves for white pawn at e2 (row 6, col 4)
    moves = board.get_possible_moves(6, 4)
    print("Legal moves for pawn at e2:")
    for row, col in moves:
        notation = f"{chr(ord('a') + col)}{8 - row}"
        print(f"  - {notation}")
    
    # Get moves for white knight at b1 (row 7, col 1)
    moves = board.get_possible_moves(7, 1)
    print("\nLegal moves for knight at b1:")
    for row, col in moves:
        notation = f"{chr(ord('a') + col)}{8 - row}"
        print(f"  - {notation}")
    
    print("✓ Legal moves retrieved\n")

def example_3_make_move():
    """Example 3: Make a move on the board"""
    print("Example 3: Make a Move")
    print("-" * 40)
    
    board = Board()
    print("Initial position:")
    board.display()
    
    # Move white pawn from e2 to e4
    board.make_move((6, 4), (4, 4))
    print("After moving pawn e2 to e4:")
    board.display()
    
    print("✓ Move executed\n")

def example_4_ai_suggest_move():
    """Example 4: Ask AI to suggest a move"""
    print("Example 4: AI Move Suggestion")
    print("-" * 40)
    
    board = Board()
    ai = ChessAI(depth=3)
    
    print("Asking AI for best move (depth=3)...")
    move = ai.get_best_move(board, Color.WHITE)
    
    if move:
        from_pos, to_pos = move
        from_notation = f"{chr(ord('a') + from_pos[1])}{8 - from_pos[0]}"
        to_notation = f"{chr(ord('a') + to_pos[1])}{8 - to_pos[0]}"
        
        print(f"AI suggests: {from_notation} → {to_notation}")
        print(f"Nodes evaluated: {ai.nodes_evaluated}")
        
        # Show the position after the move
        board.make_move(from_pos, to_pos)
        board.display()
    
    print("✓ AI move suggestion retrieved\n")

def example_5_check_game_state():
    """Example 5: Check for check, checkmate, or stalemate"""
    print("Example 5: Game State Detection")
    print("-" * 40)
    
    board = Board()
    
    print(f"Is White in check? {board.is_in_check(Color.WHITE)}")
    print(f"Is Black in check? {board.is_in_check(Color.BLACK)}")
    print(f"Is White checkmated? {board.is_checkmate(Color.WHITE)}")
    print(f"Is game stalemate? {board.is_stalemate(Color.WHITE)}")
    
    print("✓ Game state checked\n")

def example_6_ai_vs_ai():
    """Example 6: Watch AI play against itself"""
    print("Example 6: AI vs AI (3 moves)")
    print("-" * 40)
    
    board = Board()
    ai_white = ChessAI(depth=2)
    ai_black = ChessAI(depth=2)
    
    board.display()
    
    for move_num in range(1, 4):
        # White's turn
        print(f"\nMove {move_num} - White")
        move = ai_white.get_best_move(board, Color.WHITE)
        if move:
            from_pos, to_pos = move
            piece = board.board[from_pos[0]][from_pos[1]]
            board.make_move(from_pos, to_pos)
            
            from_notation = f"{chr(ord('a') + from_pos[1])}{8 - from_pos[0]}"
            to_notation = f"{chr(ord('a') + to_pos[1])}{8 - to_pos[0]}"
            print(f"  {piece.piece_type.value}: {from_notation} → {to_notation}")
        
        # Black's turn
        print(f"Move {move_num} - Black")
        move = ai_black.get_best_move(board, Color.BLACK)
        if move:
            from_pos, to_pos = move
            piece = board.board[from_pos[0]][from_pos[1]]
            board.make_move(from_pos, to_pos)
            
            from_notation = f"{chr(ord('a') + from_pos[1])}{8 - from_pos[0]}"
            to_notation = f"{chr(ord('a') + to_pos[1])}{8 - to_pos[0]}"
            print(f"  {piece.piece_type.value}: {from_notation} → {to_notation}")
    
    board.display()
    print("✓ AI vs AI demonstration complete\n")

def example_7_board_evaluation():
    """Example 7: Evaluate board positions"""
    print("Example 7: Board Evaluation")
    print("-" * 40)
    
    board = Board()
    ai = ChessAI()
    
    # Evaluate starting position
    score = ai.evaluate_board(board, Color.WHITE)
    print(f"Starting position evaluation: {score}")
    print("(0 means equal, positive favors white, negative favors black)")
    
    # Make a move and re-evaluate
    board.make_move((6, 4), (4, 4))  # e2 to e4
    score = ai.evaluate_board(board, Color.WHITE)
    print(f"\nAfter e2-e4 evaluation: {score}")
    
    # Remove a piece and evaluate
    board.board[0][0] = None  # Remove black rook
    score = ai.evaluate_board(board, Color.WHITE)
    print(f"After removing black rook: {score}")
    print(f"(White is ahead by ~{score} centipawns)")
    
    print("✓ Board evaluation complete\n")

def example_8_custom_position():
    """Example 8: Set up a custom position"""
    print("Example 8: Custom Position Setup")
    print("-" * 40)
    
    from chess_engine import Piece, PieceType
    
    # Create empty board
    board = Board()
    for row in range(8):
        for col in range(8):
            board.board[row][col] = None
    
    # Set up a simple endgame position
    # King vs King + Queen
    board.board[7][4] = Piece(PieceType.KING, Color.WHITE)  # e1
    board.board[0][4] = Piece(PieceType.KING, Color.BLACK)  # e8
    board.board[2][3] = Piece(PieceType.QUEEN, Color.BLACK)  # d6
    
    # Update king positions
    board.white_king_pos = (7, 4)
    board.black_king_pos = (0, 4)
    
    print("Custom endgame position:")
    board.display()
    
    # Check game state
    print(f"Is White in check? {board.is_in_check(Color.WHITE)}")
    print(f"Is White checkmated? {board.is_checkmate(Color.WHITE)}")
    
    print("✓ Custom position set up\n")

def main():
    """Run all examples"""
    print("\n" + "="*60)
    print("Chess Engine - Example Usage")
    print("="*60 + "\n")
    
    example_1_basic_board()
    example_2_get_moves()
    example_3_make_move()
    example_4_ai_suggest_move()
    example_5_check_game_state()
    example_6_ai_vs_ai()
    example_7_board_evaluation()
    example_8_custom_position()
    
    print("="*60)
    print("All examples completed!")
    print("="*60)
    print("\nTo play a full game, run: python3 chess_engine.py")

if __name__ == "__main__":
    main()
