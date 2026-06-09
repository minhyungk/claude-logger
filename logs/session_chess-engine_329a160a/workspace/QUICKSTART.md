# Quick Start Guide - Chess Engine

## Installation

No installation required! Just Python 3.7+

## Run the Game

```bash
python3 chess_engine.py
```

## Quick Example

```
Chess Engine - Minimax with Alpha-Beta Pruning
==================================================
Choose your color (w/b): w
Choose AI difficulty (1-5, higher is harder): 3
```

## Your First Moves

### Opening Move Example
```
WHITE's turn
Enter piece position (e.g., e2) or 'quit': e2
Legal moves: e3, e4
Enter destination (e.g., e4) or 'back': e4
Moved P from e2 to e4
```

### Popular Chess Openings to Try

1. **King's Pawn Opening (e4)**
   - `e2` → `e4`

2. **Queen's Pawn Opening (d4)**
   - `d2` → `d4`

3. **English Opening (c4)**
   - `c2` → `c4`

4. **Italian Game**
   - Move 1: `e2` → `e4`
   - Move 2: `g1` → `f3`
   - Move 3: `f1` → `c4`

## Game Controls

- **Enter piece position**: Type column + row (e.g., `e2`)
- **See legal moves**: After selecting a piece
- **Change selection**: Type `back`
- **Exit game**: Type `quit`

## Tips for Playing

1. **Start with center control**: Move pawns e2 or d2
2. **Develop knights early**: They can jump over pieces
3. **Protect your king**: Castle when possible (not yet implemented)
4. **Watch for checks**: The game will alert you
5. **Think ahead**: The AI looks 3-5 moves ahead at higher difficulties

## Difficulty Recommendations

- **Beginner**: Level 1-2 (instant moves)
- **Intermediate**: Level 3 (recommended, ~0.1s per move)
- **Advanced**: Level 4 (slower, ~1s per move)
- **Expert**: Level 5 (very slow, ~10s per move)

## Understanding the Board

```
   a  b  c  d  e  f  g  h
  ------------------------
8 |r  n  b  q  k  b  n  r  | 8    ← Black pieces (lowercase)
7 |p  p  p  p  p  p  p  p  | 7
6 |.  .  .  .  .  .  .  .  | 6
5 |.  .  .  .  .  .  .  .  | 5
4 |.  .  .  .  .  .  .  .  | 4
3 |.  .  .  .  .  .  .  .  | 3
2 |P  P  P  P  P  P  P  P  | 2
1 |R  N  B  Q  K  B  N  R  | 1    ← White pieces (uppercase)
  ------------------------
   a  b  c  d  e  f  g  h
```

### Piece Symbols
- **P/p**: Pawn
- **N/n**: Knight
- **B/b**: Bishop
- **R/r**: Rook
- **Q/q**: Queen
- **K/k**: King

## Running Tests

```bash
python3 test_chess.py
```

This will:
- Run unit tests
- Show AI vs AI demo game
- Benchmark performance at different depths

## Common Issues

### "Invalid position"
- Make sure to use lowercase letters (a-h) and numbers (1-8)
- Example: `e2`, not `E2` or `e 2`

### "That's not your piece"
- You selected an opponent's piece (lowercase vs uppercase)
- White plays uppercase pieces, Black plays lowercase

### "That piece has no legal moves"
- The piece is blocked or pinned
- Try selecting a different piece

### "Illegal move"
- The destination isn't in the legal moves list
- Would put your king in check

## Example Full Turn

```
   a  b  c  d  e  f  g  h
  ------------------------
8 |r  n  b  q  k  b  n  r  | 8
7 |p  p  p  p  p  p  p  p  | 7
6 |.  .  .  .  .  .  .  .  | 6
5 |.  .  .  .  .  .  .  .  | 5
4 |.  .  .  .  .  .  .  .  | 4
3 |.  .  .  .  .  .  .  .  | 3
2 |P  P  P  P  P  P  P  P  | 2
1 |R  N  B  Q  K  B  N  R  | 1
  ------------------------
   a  b  c  d  e  f  g  h

WHITE's turn
Enter piece position (e.g., e2) or 'quit': e2
Legal moves: e3, e4
Enter destination (e.g., e4) or 'back': e4
Moved P from e2 to e4

BLACK's turn (AI thinking...)
Nodes evaluated: 1246
AI moved P from e7 to e5

>>> Both players control the center! <<<
```

## Have Fun!

Try different strategies, learn from the AI, and enjoy the game of chess! 🎉♟️
