"""
Test and demo script for the chess engine
"""

from chess_engine import Board, ChessAI, Color, PieceType
import time

def test_board_setup():
    """Test that the board is set up correctly."""
    print("Testing board setup...")
    board = Board()
    
    # Check white pieces
    assert board.board[7][0].piece_type == PieceType.ROOK
    assert board.board[7][4].piece_type == PieceType.KING
    assert board.board[6][0].piece_type == PieceType.PAWN
    
    # Check black pieces
    assert board.board[0][0].piece_type == PieceType.ROOK
    assert board.board[0][4].piece_type == PieceType.KING
    assert board.board[1][0].piece_type == PieceType.PAWN
    
    print("✓ Board setup test passed!")

def test_piece_moves():
    """Test basic piece movement."""
    print("\nTesting piece movements...")
    board = Board()
    
    # Test pawn moves
    pawn_moves = board.get_possible_moves(6, 4)  # e2 pawn
    assert (5, 4) in pawn_moves  # e3
    assert (4, 4) in pawn_moves  # e4
    
    # Test knight moves
    knight_moves = board.get_possible_moves(7, 1)  # b1 knight
    assert (5, 0) in knight_moves  # a3
    assert (5, 2) in knight_moves  # c3
    
    print("✓ Piece movement test passed!")

def test_check_detection():
    """Test check detection."""
    print("\nTesting check detection...")
    board = Board()
    
    # Set up a simple check scenario
    # Clear some pieces
    board.board[6][4] = None  # Remove e2 pawn
    board.board[6][5] = None  # Remove f2 pawn
    board.board[1][4] = None  # Remove e7 pawn
    
    # Move black queen to check white king
    board.board[3][4] = board.board[0][3]  # Queen to e5
    board.board[0][3] = None
    
    # This should detect check
    assert board.is_in_check(Color.WHITE)
    assert not board.is_in_check(Color.BLACK)
    
    print("✓ Check detection test passed!")

def test_ai_evaluation():
    """Test AI board evaluation."""
    print("\nTesting AI evaluation...")
    board = Board()
    ai = ChessAI(depth=2)
    
    # Initial position should be balanced
    score = ai.evaluate_board(board, Color.WHITE)
    assert abs(score) < 200  # Should be close to 0 (balanced)
    
    # Remove a black piece
    board.board[0][0] = None  # Remove black rook
    score = ai.evaluate_board(board, Color.WHITE)
    assert score > 400  # White should be significantly ahead
    
    print(f"✓ AI evaluation test passed! (Initial score: {ai.evaluate_board(Board(), Color.WHITE)})")

def test_ai_move_selection():
    """Test that AI can select a move."""
    print("\nTesting AI move selection...")
    board = Board()
    ai = ChessAI(depth=2)
    
    move = ai.get_best_move(board, Color.WHITE)
    assert move is not None
    assert len(move) == 2
    from_pos, to_pos = move
    assert len(from_pos) == 2
    assert len(to_pos) == 2
    
    print(f"✓ AI move selection test passed! Best opening move: {from_pos} -> {to_pos}")
    print(f"  Nodes evaluated: {ai.nodes_evaluated}")

def demo_ai_game():
    """Demonstrate AI vs AI game for a few moves."""
    print("\n" + "="*60)
    print("DEMO: AI vs AI - First 3 moves")
    print("="*60)
    
    board = Board()
    ai_white = ChessAI(depth=2)
    ai_black = ChessAI(depth=2)
    
    board.display()
    
    for move_num in range(1, 4):
        # White move
        print(f"\nMove {move_num} - White's turn:")
        start_time = time.time()
        move = ai_white.get_best_move(board, Color.WHITE)
        elapsed = time.time() - start_time
        
        if move:
            from_pos, to_pos = move
            piece = board.board[from_pos[0]][from_pos[1]]
            board.make_move(from_pos, to_pos)
            
            from_notation = f"{chr(ord('a') + from_pos[1])}{8 - from_pos[0]}"
            to_notation = f"{chr(ord('a') + to_pos[1])}{8 - to_pos[0]}"
            print(f"White plays: {piece.piece_type.value} {from_notation} -> {to_notation}")
            print(f"Time: {elapsed:.2f}s, Nodes: {ai_white.nodes_evaluated}")
            
            board.display()
        
        # Black move
        print(f"\nMove {move_num} - Black's turn:")
        start_time = time.time()
        move = ai_black.get_best_move(board, Color.BLACK)
        elapsed = time.time() - start_time
        
        if move:
            from_pos, to_pos = move
            piece = board.board[from_pos[0]][from_pos[1]]
            board.make_move(from_pos, to_pos)
            
            from_notation = f"{chr(ord('a') + from_pos[1])}{8 - from_pos[0]}"
            to_notation = f"{chr(ord('a') + to_pos[1])}{8 - to_pos[0]}"
            print(f"Black plays: {piece.piece_type.value} {from_notation} -> {to_notation}")
            print(f"Time: {elapsed:.2f}s, Nodes: {ai_black.nodes_evaluated}")
            
            board.display()

def benchmark_ai():
    """Benchmark AI performance at different depths."""
    print("\n" + "="*60)
    print("AI Performance Benchmark")
    print("="*60)
    
    board = Board()
    
    for depth in range(1, 5):
        ai = ChessAI(depth=depth)
        print(f"\nDepth {depth}:")
        
        start_time = time.time()
        move = ai.get_best_move(board, Color.WHITE)
        elapsed = time.time() - start_time
        
        print(f"  Time: {elapsed:.3f}s")
        print(f"  Nodes evaluated: {ai.nodes_evaluated:,}")
        print(f"  Nodes/second: {int(ai.nodes_evaluated / elapsed):,}")
        
        if elapsed > 5:  # Stop if it takes too long
            print(f"  (Stopping benchmark - depth {depth} is too slow)")
            break

def run_all_tests():
    """Run all tests."""
    print("="*60)
    print("Running Chess Engine Tests")
    print("="*60 + "\n")
    
    test_board_setup()
    test_piece_moves()
    test_check_detection()
    test_ai_evaluation()
    test_ai_move_selection()
    
    print("\n" + "="*60)
    print("All tests passed! ✓")
    print("="*60)
    
    # Run demos
    demo_ai_game()
    benchmark_ai()
    
    print("\n" + "="*60)
    print("Testing and benchmarking complete!")
    print("="*60)

if __name__ == "__main__":
    run_all_tests()
