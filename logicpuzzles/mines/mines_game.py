import pygame
import random
from typing import List, Set, Tuple
from .minesweeper import MineBoard
from .minesweeper_solver import MinesweeperSolver

class Minesweeper:
    # Colors
    GRAY = (192, 192, 192)
    DARK_GRAY = (128, 128, 128)
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    RED = (255, 0, 0)
    BLUE = (0, 0, 255)
    GREEN = (0, 128, 0)
    
    # Number colors
    NUMBER_COLORS = [
        None,  # 0 has no color
        (0, 0, 255),      # 1: Blue
        (0, 128, 0),      # 2: Green
        (255, 0, 0),      # 3: Red
        (0, 0, 128),      # 4: Dark Blue
        (128, 0, 0),      # 5: Dark Red
        (0, 128, 128),    # 6: Cyan
        (0, 0, 0),        # 7: Black
        (128, 128, 128)   # 8: Gray
    ]
    
    def __init__(self, width: int, height: int, mines: int):
        pygame.init()
        
        # Store initial parameters for restart
        self.initial_width = width
        self.initial_height = height
        self.initial_mines = mines
        
        self.CELL_SIZE = 30
        self.BORDER = 2
        self.HEADER_HEIGHT = 50
        self.PANEL_WIDTH = 150
        
        self.width = width
        self.height = height
        self.mines = mines
        self.mines_left = mines
        
        # Window setup
        self.grid_width = width * self.CELL_SIZE
        self.grid_height = height * self.CELL_SIZE + self.HEADER_HEIGHT
        self.screen_width = self.grid_width + self.PANEL_WIDTH
        self.screen_height = self.grid_height
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Minesweeper")
        
        # Font setup
        self.font = pygame.font.Font(None, 24)
        self.header_font = pygame.font.Font(None, 36)
        
        # Game state
        self.solution = MineBoard(height, width)
        self.revealed: Set[Tuple[int, int]] = set()
        self.flagged: Set[Tuple[int, int]] = set()
        self.won = False
        self.game_over = False
        self.first_click = True
        self.fatal_mine = None
        
        # Solver state
        self.solver = None
        self.hint_cells = None
        self.solving = False
        self.finding_hints = False
        self.solve_timer = 0
        self.cells_to_solve = None

    def place_mines(self, safe_cell: Tuple[int, int]):
        """Place mines randomly on the board, ensuring safe_cell is not a mine"""
        positions = [(i, j) for i in range(self.height) for j in range(self.width)]
        positions.remove(safe_cell)  # Remove the clicked cell from possible mine positions
        mine_positions = set(random.sample(positions, self.mines))
        
        # Reset all cells first
        for r, c in positions:
            self.solution.f[(r, c)].is_mine = False
        
        # Set mine positions
        for r, c in mine_positions:
            self.solution.f[(r, c)].is_mine = True

    def calculate_numbers(self):
        """Calculate numbers for non-mine squares"""
        for r in range(self.height):
            for c in range(self.width):
                if not self.solution.f[(r, c)].is_mine:
                    count = self.count_adjacent_mines(r, c)
                    self.solution.f[(r, c)].adjacent_mines = count
    
    def count_adjacent_mines(self, row: int, col: int) -> int:
        """Count adjacent mines for a given position"""
        count = 0
        for face in self.solution.face_to_faces((row, col), include_diagonals=True):
            if face.is_mine:
                count += 1
        return count
    
    def reveal(self, row: int, col: int):
        """Reveal a square and its adjacent squares if it's empty"""
        if (row, col) in self.revealed or (row, col) in self.flagged:
            return
        
        self.revealed.add((row, col))
        cell = self.solution.f[(row, col)]
        
        if cell.adjacent_mines == 0 and not cell.is_mine:
            for face in self.solution.face_to_faces((row, col), include_diagonals=True):
                if (face.r, face.c) not in self.revealed:
                    self.reveal(face.r, face.c)
    
    def check_win(self) -> bool:
        """Check if the player has won"""
        if len(self.revealed) == (self.width * self.height - self.mines):
            # Flag all remaining mines when winning
            for r in range(self.height):
                for c in range(self.width):
                    if self.solution.f[(r, c)].is_mine and (r, c) not in self.flagged:
                        self.flagged.add((r, c))
            return True
        return False
    
    def handle_click(self, pos: Tuple[int, int], right_click: bool = False):
        """Handle mouse clicks"""
        # Don't process clicks during hint generation or solving
        if self.finding_hints or self.solving:
            return
            
        # Check for panel button clicks
        if pos[0] >= self.grid_width:
            if self.solver_rect.collidepoint(pos):
                self.start_solver()
                return
            elif self.hint_rect.collidepoint(pos):
                self.show_hints()
                return
            elif self.restart_rect.collidepoint(pos):
                self.restart_game()
                return
        
        # Don't process grid clicks if game is over
        if self.game_over or self.won:
            return
            
        # Handle grid clicks
        if pos[1] < self.HEADER_HEIGHT:
            return
            
        # Adjust click position to account for header
        pos = (pos[0], pos[1] - self.HEADER_HEIGHT)
        
        col = pos[0] // self.CELL_SIZE
        row = pos[1] // self.CELL_SIZE
        
        # Check if click is in the grid area
        if not (0 <= row < self.height and 0 <= col < self.width):
            return
            
        if right_click:
            if (row, col) not in self.revealed:
                if (row, col) in self.flagged:
                    self.flagged.remove((row, col))
                    self.mines_left += 1
                else:
                    self.flagged.add((row, col))
                    self.mines_left -= 1
                # Remove this cell from hints if it exists
                if self.hint_cells is not None and (row, col) in self.hint_cells:
                    del self.hint_cells[(row, col)]
        else:
            if (row, col) not in self.flagged:
                if self.first_click:
                    self.first_click = False
                    self.place_mines((row, col))
                    self.calculate_numbers()
                
                cell = self.solution.f[(row, col)]
                if cell.is_mine:
                    self.game_over = True
                    self.fatal_mine = (row, col)
                    self.reveal_all_mines()
                else:
                    self.reveal(row, col)
                    if self.check_win():
                        self.won = True
                        self.mines_left = 0
                    # Remove this cell from hints if it exists
                    if self.hint_cells is not None and (row, col) in self.hint_cells:
                        del self.hint_cells[(row, col)]
    
    def reveal_all_mines(self):
        """Reveal all mines when game is over"""
        for r in range(self.height):
            for c in range(self.width):
                if self.solution.f[(r, c)].is_mine:
                    self.revealed.add((r, c))
    
    def draw_cell(self, row: int, col: int):
        """Draw a single cell"""
        x = col * self.CELL_SIZE
        y = row * self.CELL_SIZE + self.HEADER_HEIGHT
        
        # Draw cell background
        if (row, col) in self.revealed:
            pygame.draw.rect(self.screen, self.WHITE, (x, y, self.CELL_SIZE, self.CELL_SIZE))
        else:
            # Highlight determinable cells if showing hints
            if self.hint_cells is not None and (row, col) in self.hint_cells:
                pygame.draw.rect(self.screen, self.GREEN, (x, y, self.CELL_SIZE, self.CELL_SIZE))
            else:
                pygame.draw.rect(self.screen, self.GRAY, (x, y, self.CELL_SIZE, self.CELL_SIZE))
            # Draw 3D effect for unrevealed cells
            pygame.draw.line(self.screen, self.WHITE, (x, y), (x + self.CELL_SIZE, y), self.BORDER)
            pygame.draw.line(self.screen, self.WHITE, (x, y), (x, y + self.CELL_SIZE), self.BORDER)
            pygame.draw.line(self.screen, self.DARK_GRAY, (x + self.CELL_SIZE - self.BORDER, y),
                           (x + self.CELL_SIZE - self.BORDER, y + self.CELL_SIZE - self.BORDER), self.BORDER)
            pygame.draw.line(self.screen, self.DARK_GRAY, (x, y + self.CELL_SIZE - self.BORDER),
                           (x + self.CELL_SIZE - self.BORDER, y + self.CELL_SIZE - self.BORDER), self.BORDER)
        
        # Draw cell content
        cell = self.solution.f[(row, col)]
        if (row, col) in self.revealed:
            if cell.is_mine:
                if (row, col) == self.fatal_mine:
                    # Draw red background for fatal mine
                    pygame.draw.rect(self.screen, self.RED, (x, y, self.CELL_SIZE, self.CELL_SIZE))
                    text = self.font.render('X', True, self.BLACK)
                else:
                    text = self.font.render('X', True, self.RED)
            elif cell.adjacent_mines > 0:
                text = self.font.render(str(cell.adjacent_mines), True, self.NUMBER_COLORS[cell.adjacent_mines])
            else:
                return
            text_rect = text.get_rect(center=(x + self.CELL_SIZE // 2, y + self.CELL_SIZE // 2))
            self.screen.blit(text, text_rect)
        elif (row, col) in self.flagged:
            text = self.font.render('X', True, self.RED)  # Changed from 'F' to 'X'
            text_rect = text.get_rect(center=(x + self.CELL_SIZE // 2, y + self.CELL_SIZE // 2))
            self.screen.blit(text, text_rect)
    
    def draw_header(self):
        """Draw the header area with mines counter"""
        # Draw header background
        pygame.draw.rect(self.screen, self.DARK_GRAY, 
                        (0, 0, self.grid_width, self.HEADER_HEIGHT))
        
        # Draw mines left counter centered above grid
        mines_text = self.header_font.render(f"Mines: {self.mines_left}", True, self.WHITE)
        mines_rect = mines_text.get_rect(center=(self.grid_width // 2, self.HEADER_HEIGHT // 2))
        self.screen.blit(mines_text, mines_rect)
        
        # Draw separator line
        pygame.draw.line(self.screen, self.WHITE, 
                        (0, self.HEADER_HEIGHT - 1),
                        (self.grid_width, self.HEADER_HEIGHT - 1), 2)

    def draw_panel(self):
        """Draw the right side panel with buttons"""
        # Draw panel background
        panel_rect = pygame.Rect(self.grid_width, 0, self.PANEL_WIDTH, self.screen_height)
        pygame.draw.rect(self.screen, self.DARK_GRAY, panel_rect)
        
        # Draw vertical separator line
        pygame.draw.line(self.screen, self.WHITE,
                        (self.grid_width, 0),
                        (self.grid_width, self.screen_height), 2)
        
        # Button dimensions
        BUTTON_WIDTH = 120
        BUTTON_HEIGHT = 40
        BUTTON_SPACING = 20
        button_x = self.grid_width + (self.PANEL_WIDTH - BUTTON_WIDTH) // 2
        
        # Draw solver button
        solver_y = 20
        self.solver_rect = pygame.Rect(button_x, solver_y, BUTTON_WIDTH, BUTTON_HEIGHT)
        
        # Draw button in pressed state while solving
        if self.solving:
            pygame.draw.rect(self.screen, self.DARK_GRAY, self.solver_rect)
            # Draw pressed 3D effect
            pygame.draw.line(self.screen, self.DARK_GRAY,
                           (button_x, solver_y),
                           (button_x + BUTTON_WIDTH, solver_y), self.BORDER)
            pygame.draw.line(self.screen, self.DARK_GRAY,
                           (button_x, solver_y),
                           (button_x, solver_y + BUTTON_HEIGHT), self.BORDER)
            pygame.draw.line(self.screen, self.WHITE,
                           (button_x + BUTTON_WIDTH - self.BORDER, solver_y),
                           (button_x + BUTTON_WIDTH - self.BORDER, solver_y + BUTTON_HEIGHT - self.BORDER), self.BORDER)
            pygame.draw.line(self.screen, self.WHITE,
                           (button_x, solver_y + BUTTON_HEIGHT - self.BORDER),
                           (button_x + BUTTON_WIDTH - self.BORDER, solver_y + BUTTON_HEIGHT - self.BORDER), self.BORDER)
        else:
            # Normal unpressed state
            pygame.draw.rect(self.screen, self.GRAY, self.solver_rect)
            # Draw normal 3D effect
            pygame.draw.line(self.screen, self.WHITE,
                           (button_x, solver_y),
                           (button_x + BUTTON_WIDTH, solver_y), self.BORDER)
            pygame.draw.line(self.screen, self.WHITE,
                           (button_x, solver_y),
                           (button_x, solver_y + BUTTON_HEIGHT), self.BORDER)
            pygame.draw.line(self.screen, self.DARK_GRAY,
                           (button_x + BUTTON_WIDTH - self.BORDER, solver_y),
                           (button_x + BUTTON_WIDTH - self.BORDER, solver_y + BUTTON_HEIGHT - self.BORDER), self.BORDER)
            pygame.draw.line(self.screen, self.DARK_GRAY,
                           (button_x, solver_y + BUTTON_HEIGHT - self.BORDER),
                           (button_x + BUTTON_WIDTH - self.BORDER, solver_y + BUTTON_HEIGHT - self.BORDER), self.BORDER)
        
        # Draw solver text
        solver_text = self.header_font.render("Solve", True, self.BLACK)
        text_rect = solver_text.get_rect(center=self.solver_rect.center)
        self.screen.blit(solver_text, text_rect)
        
        # Draw hint button
        hint_y = solver_y + BUTTON_HEIGHT + BUTTON_SPACING
        self.hint_rect = pygame.Rect(button_x, hint_y, BUTTON_WIDTH, BUTTON_HEIGHT)
        
        # Draw button in pressed state while finding hints
        if self.finding_hints:
            pygame.draw.rect(self.screen, self.DARK_GRAY, self.hint_rect)
            # Draw pressed 3D effect
            pygame.draw.line(self.screen, self.DARK_GRAY,
                           (button_x, hint_y),
                           (button_x + BUTTON_WIDTH, hint_y), self.BORDER)
            pygame.draw.line(self.screen, self.DARK_GRAY,
                           (button_x, hint_y),
                           (button_x, hint_y + BUTTON_HEIGHT), self.BORDER)
            pygame.draw.line(self.screen, self.WHITE,
                           (button_x + BUTTON_WIDTH - self.BORDER, hint_y),
                           (button_x + BUTTON_WIDTH - self.BORDER, hint_y + BUTTON_HEIGHT - self.BORDER), self.BORDER)
            pygame.draw.line(self.screen, self.WHITE,
                           (button_x, hint_y + BUTTON_HEIGHT - self.BORDER),
                           (button_x + BUTTON_WIDTH - self.BORDER, hint_y + BUTTON_HEIGHT - self.BORDER), self.BORDER)
        else:
            # Normal unpressed state
            pygame.draw.rect(self.screen, self.GRAY, self.hint_rect)
            # Draw normal 3D effect
            pygame.draw.line(self.screen, self.WHITE,
                           (button_x, hint_y),
                           (button_x + BUTTON_WIDTH, hint_y), self.BORDER)
            pygame.draw.line(self.screen, self.WHITE,
                           (button_x, hint_y),
                           (button_x, hint_y + BUTTON_HEIGHT), self.BORDER)
            pygame.draw.line(self.screen, self.DARK_GRAY,
                           (button_x + BUTTON_WIDTH - self.BORDER, hint_y),
                           (button_x + BUTTON_WIDTH - self.BORDER, hint_y + BUTTON_HEIGHT - self.BORDER), self.BORDER)
            pygame.draw.line(self.screen, self.DARK_GRAY,
                           (button_x, hint_y + BUTTON_HEIGHT - self.BORDER),
                           (button_x + BUTTON_WIDTH - self.BORDER, hint_y + BUTTON_HEIGHT - self.BORDER), self.BORDER)
        
        # Draw hint text
        hint_text = self.header_font.render("Hint", True, self.BLACK)
        text_rect = hint_text.get_rect(center=self.hint_rect.center)
        self.screen.blit(hint_text, text_rect)
        
        # Draw restart button
        restart_y = hint_y + BUTTON_HEIGHT + BUTTON_SPACING
        self.restart_rect = pygame.Rect(button_x, restart_y, BUTTON_WIDTH, BUTTON_HEIGHT)
        pygame.draw.rect(self.screen, self.GRAY, self.restart_rect)
        # Draw 3D effect
        pygame.draw.line(self.screen, self.WHITE,
                        (button_x, restart_y),
                        (button_x + BUTTON_WIDTH, restart_y), self.BORDER)
        pygame.draw.line(self.screen, self.WHITE,
                        (button_x, restart_y),
                        (button_x, restart_y + BUTTON_HEIGHT), self.BORDER)
        pygame.draw.line(self.screen, self.DARK_GRAY,
                        (button_x + BUTTON_WIDTH - self.BORDER, restart_y),
                        (button_x + BUTTON_WIDTH - self.BORDER, restart_y + BUTTON_HEIGHT - self.BORDER), self.BORDER)
        pygame.draw.line(self.screen, self.DARK_GRAY,
                        (button_x, restart_y + BUTTON_HEIGHT - self.BORDER),
                        (button_x + BUTTON_WIDTH - self.BORDER, restart_y + BUTTON_HEIGHT - self.BORDER), self.BORDER)
        
        # Draw restart text
        restart_text = self.header_font.render("Restart", True, self.BLACK)
        text_rect = restart_text.get_rect(center=self.restart_rect.center)
        self.screen.blit(restart_text, text_rect)

    def draw(self):
        """Draw the entire game board"""
        self.screen.fill(self.GRAY)
        
        # Draw header first
        self.draw_header()
        
        # Draw cells
        for row in range(self.height):
            for col in range(self.width):
                self.draw_cell(row, col)
        
        # Draw right panel
        self.draw_panel()
        
        # Draw game over or win message
        if self.game_over:
            self.draw_message("Game Over!", self.RED)
        elif self.won:
            self.draw_message("You Won!", self.GREEN)
        
        pygame.display.flip()
    
    def draw_message(self, message: str, color: Tuple[int, int, int]):
        """Draw a centered message on the screen"""
        text = pygame.font.Font(None, 48).render(message, True, color)
        text_rect = text.get_rect(center=(self.screen_width // 2, 
                                        (self.screen_height + self.HEADER_HEIGHT) // 2))
        
        # Draw semi-transparent background
        s = pygame.Surface((self.screen_width, 60))
        s.set_alpha(128)
        s.fill(self.WHITE)
        self.screen.blit(s, (0, text_rect.y - 10))
        
        # Draw message
        self.screen.blit(text, text_rect)
    
    def run(self):
        """Main game loop"""
        running = True
        clock = pygame.time.Clock()
        
        while running:
            clock.tick(30)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.handle_click(event.pos, event.button == 3)
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
            
            self.update()  # Add update call
            self.draw()
        
        pygame.quit()

    def init_solver(self):
        """Initialize the solver for the current game state"""
        solver = MinesweeperSolver(self, verbose=False)
        print("\nInitializing Solver...")
        print(solver)
        return solver

    def restart_game(self):
        """Reset the game with the same parameters but new random board"""
        self.mines = self.initial_mines
        self.mines_left = self.initial_mines
        self.solution = MineBoard(self.height, self.width)
        self.revealed = set()
        self.flagged = set()
        self.won = False
        self.game_over = False
        self.first_click = True
        self.fatal_mine = None
        # Reset solver state
        self.solver = None
        self.hint_cells = None
        self.solving = False
        self.finding_hints = False
        self.solve_timer = 0
        self.cells_to_solve = None

    def show_hints(self):
        """Show/hide determinable cells"""
        if self.first_click or self.game_over or self.won:
            return
            
        # Toggle hints off if they're currently shown
        if self.hint_cells is not None:
            self.hint_cells = None
            self.finding_hints = False
            self.solving = False  # Ensure solving is stopped
            self.cells_to_solve = None
            return
            
        # Always create a new solver with current game state
        self.solver = MinesweeperSolver(self, verbose=False)
        
        # Initialize hint cells
        self.hint_cells = {}
        self.finding_hints = True
        self.solving = False  # Ensure solving is stopped
        self.cells_to_solve = None
        self.hint_finder = self.solver.find_determinable_cells()

    def start_solver(self):
        """Start automatic solving process"""
        if self.first_click or self.game_over or self.won:
            return
            
        # Choose solve path based on whether hints exist
        if self.hint_cells is not None:
            self.solve_known_hints()
        else:
            self.solve_with_new_hints()

    def solve_known_hints(self):
        """Solve using pre-existing hints with delay between moves"""
        self.solving = True
        self.finding_hints = False  # Ensure we're not in hint-finding mode
        self.solve_timer = pygame.time.get_ticks()
        self.cells_to_solve = list(self.hint_cells.items())
        self.hint_finder = None  # Clear any existing hint finder

    def solve_with_new_hints(self):
        """Find and solve with new hints, applying moves as they're found"""
        self.solver = MinesweeperSolver(self, verbose=False)
        self.hint_cells = {}
        self.finding_hints = True
        self.solving = True
        self.solve_timer = pygame.time.get_ticks()
        self.hint_finder = self.solver.find_determinable_cells()

    def update(self):
        """Update game state"""
        if self.solving and self.finding_hints:
            self.update_solve_with_hints()
        elif self.solving:
            self.update_solve_known_hints()
        elif self.finding_hints:
            self.update_finding_hints()

    def update_finding_hints(self):
        """Process finding hints without solving"""
        end_time = pygame.time.get_ticks() + 16
        while pygame.time.get_ticks() < end_time:
            try:
                (r, c), is_mine = next(self.hint_finder)
                if (r, c) not in self.revealed and (r, c) not in self.flagged:
                    self.hint_cells[(r, c)] = is_mine
            except StopIteration:
                self.finding_hints = False
                break

    def update_solve_with_hints(self):
        """Process finding and applying hints with delay"""
        current_time = pygame.time.get_ticks()
        if current_time >= self.solve_timer:
            # Try to find next determinable cell
            try:
                (r, c), is_mine = next(self.hint_finder)
                if (r, c) not in self.revealed and (r, c) not in self.flagged:
                    # Add to hints and apply move immediately
                    self.hint_cells[(r, c)] = is_mine
                    if is_mine:
                        self.flagged.add((r, c))
                        self.mines_left -= 1
                    else:
                        self.reveal(r, c)
                        if self.check_win():
                            self.won = True
                            self.mines_left = 0
                            self.solving = False
                            self.finding_hints = False
                            self.hint_cells = None
                            return
                    # Set timer for next move
                    self.solve_timer = current_time + 500
            except StopIteration:
                # Done finding all hints
                self.solving = False
                self.finding_hints = False
                self.hint_cells = None

    def update_solve_known_hints(self):
        """Process solving pre-existing hints with delay"""
        if not self.cells_to_solve:
            self.solving = False
            self.hint_cells = None
            return
            
        current_time = pygame.time.get_ticks()
        if current_time >= self.solve_timer:
            (r, c), is_mine = self.cells_to_solve.pop(0)
            if (is_mine and (r, c) not in self.flagged) or (not is_mine and (r, c) not in self.revealed):
                if is_mine:
                    self.flagged.add((r, c))
                    self.mines_left -= 1
                else:
                    self.reveal(r, c)
                    if self.check_win():
                        self.won = True
                        self.mines_left = 0
                        self.solving = False
                        self.hint_cells = None
                        return
                self.solve_timer = current_time + 500
            
            # If no more moves, clean up immediately
            if not self.cells_to_solve:
                self.solving = False
                self.hint_cells = None
