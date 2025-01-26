import sys
from logicpuzzles.mines.mines_game import Minesweeper

def main():
    if len(sys.argv) != 4:
        print("Usage: python -m games.mines <width> <height> <mines>")
        sys.exit(1)
    
    width = int(sys.argv[1])
    height = int(sys.argv[2])
    mines = int(sys.argv[3])
    
    if mines >= width * height:
        print("Too many mines for the given dimensions!")
        sys.exit(1)
    
    game = Minesweeper(width, height, mines)
    game.run()

if __name__ == "__main__":
    main()
