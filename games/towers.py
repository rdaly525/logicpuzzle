import sys
from logicpuzzles.towers.towers_game import TowersGame

def main():
    # Default size is 4
    size = 4
    
    # Check for command line argument
    if len(sys.argv) > 1:
        try:
            size = int(sys.argv[1])
            # Validate size is reasonable
            if size < 3 or size > 9:
                print("Board size must be between 3 and 9")
                sys.exit(1)
        except ValueError:
            print("Board size must be a number")
            sys.exit(1)
    
    game = TowersGame(size)
    game.run()

if __name__ == "__main__":
    main() 