import pygame
import typing as tp
from .towers import TowersBoard
from .towers_solver import TowersSolver

class TowersGame:
    # Colors
    GRAY = (192, 192, 192)
    DARK_GRAY = (128, 128, 128)
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    RED = (255, 0, 0)
    GREEN = (0, 128, 0)
    BLUE = (0, 0, 255)

    def __init__(self, N: int = 4):
        pygame.init()
        
        # Store initial parameter for restart
        self.N = N
        
        # Display settings
        self.CELL_SIZE = 60
        self.CLUE_SIZE = 30
        self.BORDER = 2
        self.PANEL_WIDTH = 150
        
        # Calculate grid dimensions including clues
        self.grid_size = N * self.CELL_SIZE
        self.total_size = self.grid_size + 2 * self.CLUE_SIZE
        
        # Window setup
        self.screen_width = self.total_size + self.PANEL_WIDTH
        self.screen_height = self.total_size
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Towers Puzzle")
        
        # Font setup
        self.font = pygame.font.Font(None, 36)
        
        # Game state
        self.board = TowersBoard(N)
        self.selected_cell = None
        self.won = False
        self.solving = False
        
        # Create button rectangles
        button_x = self.total_size + 15
        self.solve_rect = pygame.Rect(button_x, 20, self.PANEL_WIDTH - 30, 40)
        self.restart_rect = pygame.Rect(button_x, 80, self.PANEL_WIDTH - 30, 40)
        
        # Add error state with timer
        self.error_message = None
        self.error_timer = 0
        self.ERROR_DISPLAY_TIME = 1000  # Display error for 1 second (in milliseconds)

    def handle_click(self, pos: tp.Tuple[int, int]):
        """Handle mouse clicks"""
        # Check for panel button clicks
        if pos[0] >= self.total_size:
            if self.solve_rect.collidepoint(pos):
                self.solve_game()
                return
            elif self.restart_rect.collidepoint(pos):
                self.restart_game()
                return
            return

        # Convert click position to grid coordinates
        grid_x = pos[0] - self.CLUE_SIZE
        grid_y = pos[1] - self.CLUE_SIZE
        
        # Check if click is within grid bounds
        if 0 <= grid_x < self.grid_size and 0 <= grid_y < self.grid_size:
            row = grid_y // self.CELL_SIZE
            col = grid_x // self.CELL_SIZE
            self.selected_cell = (row, col)

    def handle_key(self, key: int):
        """Handle keyboard input for selected cell"""
        if self.selected_cell is None or self.won:
            return
            
        row, col = self.selected_cell
        
        # Handle number keys 1-9
        if pygame.K_1 <= key <= pygame.K_9:
            value = key - pygame.K_0  # Convert key to number
            if value <= self.N:
                self.board.f[(row, col)].val = value
                self.check_win()
        # Handle backspace/delete to clear cell
        elif key in (pygame.K_BACKSPACE, pygame.K_DELETE):
            self.board.f[(row, col)].val = None

    def check_win(self) -> bool:
        """Check if the current board state is a winning state"""
        # Check if all cells are filled
        for r in range(self.N):
            for c in range(self.N):
                if self.board.f[(r, c)].val is None:
                    return False

        # Create solver to verify solution
        solver = TowersSolver(self.board)
        
        # Add constraints for current values
        for r in range(self.N):
            for c in range(self.N):
                val = self.board.f[(r, c)].val
                if val is not None:
                    solver.add_constraint(solver.f[(r, c)].var == val)

        # If solution exists with current values, it must match current board
        # (since all cells are filled)
        try:
            next(solver.solve())
            self.won = True
            return True
        except StopIteration:
            return False

    def solve_game(self):
        """Use solver to complete the puzzle"""
        if self.won:
            return
            
        self.solving = True
        self.error_message = None  # Clear any previous error
        solver = TowersSolver(self.board)
        
        # Add constraints for current values
        for r in range(self.N):
            for c in range(self.N):
                val = self.board.f[(r, c)].val
                if val is not None:
                    solver.add_constraint(solver.f[(r, c)].var == val)
        
        try:
            solution = next(solver.solve())
            # Copy solution to game board
            for r in range(self.N):
                for c in range(self.N):
                    self.board.f[(r, c)].val = solution.f[(r, c)].val
            self.won = True
        except StopIteration:
            # No solution exists - show error message with timer
            self.error_message = "No solution exists!"
            self.error_timer = pygame.time.get_ticks()
        
        self.solving = False

    def restart_game(self):
        """Reset the game with a new random board"""
        self.board = TowersBoard(self.N)
        self.selected_cell = None
        self.won = False
        self.solving = False
        self.error_message = None  # Clear any error message

    def draw_cell(self, row: int, col: int):
        """Draw a single cell"""
        x = col * self.CELL_SIZE + self.CLUE_SIZE
        y = row * self.CELL_SIZE + self.CLUE_SIZE
        
        # Draw cell background
        cell_color = self.WHITE
        if (row, col) == self.selected_cell:
            cell_color = (220, 220, 255)  # Light blue for selected cell
        pygame.draw.rect(self.screen, cell_color, 
                        (x, y, self.CELL_SIZE, self.CELL_SIZE))
        
        # Draw cell border
        pygame.draw.rect(self.screen, self.BLACK,
                        (x, y, self.CELL_SIZE, self.CELL_SIZE), 1)
        
        # Draw cell value
        val = self.board.f[(row, col)].val
        if val is not None:
            text = self.font.render(str(val), True, self.BLACK)
            text_rect = text.get_rect(center=(x + self.CELL_SIZE // 2,
                                            y + self.CELL_SIZE // 2))
            self.screen.blit(text, text_rect)

    def draw_clues(self):
        """Draw the clue numbers around the grid"""
        # Helper to draw centered text
        def draw_centered_text(text: str, x: int, y: int):
            text_surface = self.font.render(text, True, self.BLACK)
            text_rect = text_surface.get_rect(center=(x, y))
            self.screen.blit(text_surface, text_rect)
        
        # Draw top clues
        for i, clue in enumerate(self.board.clues['T']):
            x = self.CLUE_SIZE + i * self.CELL_SIZE + self.CELL_SIZE // 2
            y = self.CLUE_SIZE // 2
            draw_centered_text(str(clue), x, y)
        
        # Draw bottom clues
        for i, clue in enumerate(self.board.clues['B']):
            x = self.CLUE_SIZE + i * self.CELL_SIZE + self.CELL_SIZE // 2
            y = self.total_size - self.CLUE_SIZE // 2
            draw_centered_text(str(clue), x, y)
        
        # Draw left clues
        for i, clue in enumerate(self.board.clues['L']):
            x = self.CLUE_SIZE // 2
            y = self.CLUE_SIZE + i * self.CELL_SIZE + self.CELL_SIZE // 2
            draw_centered_text(str(clue), x, y)
        
        # Draw right clues
        for i, clue in enumerate(self.board.clues['R']):
            x = self.total_size - self.CLUE_SIZE // 2
            y = self.CLUE_SIZE + i * self.CELL_SIZE + self.CELL_SIZE // 2
            draw_centered_text(str(clue), x, y)

    def draw_panel(self):
        """Draw the right side panel with buttons"""
        # Draw panel background
        panel_rect = pygame.Rect(self.total_size, 0, self.PANEL_WIDTH, self.screen_height)
        pygame.draw.rect(self.screen, self.GRAY, panel_rect)
        
        # Draw solve button
        button_color = self.DARK_GRAY if self.solving else self.WHITE
        pygame.draw.rect(self.screen, button_color, self.solve_rect)
        text = self.font.render("Solve", True, self.BLACK)
        text_rect = text.get_rect(center=self.solve_rect.center)
        self.screen.blit(text, text_rect)
        
        # Draw restart button
        pygame.draw.rect(self.screen, self.WHITE, self.restart_rect)
        text = self.font.render("Restart", True, self.BLACK)
        text_rect = text.get_rect(center=self.restart_rect.center)
        self.screen.blit(text, text_rect)
        
        # Draw status text below buttons
        status_y = self.restart_rect.bottom + 20
        if self.error_message:
            # Show error message in red
            status_text = self.font.render(self.error_message, True, self.RED)
        elif self.won:
            status_text = self.font.render("Solved!", True, self.GREEN)
        else:
            status_text = self.font.render("Playing...", True, self.BLACK)
        status_rect = status_text.get_rect(centerx=panel_rect.centerx, top=status_y)
        self.screen.blit(status_text, status_rect)

    def draw(self):
        """Draw the entire game board"""
        self.screen.fill(self.WHITE)
        
        # Draw grid cells
        for row in range(self.N):
            for col in range(self.N):
                self.draw_cell(row, col)
        
        # Draw clues
        self.draw_clues()
        
        # Draw panel
        self.draw_panel()
        
        pygame.display.flip()

    def update(self):
        """Update game state"""
        # Clear error message after timer expires
        if self.error_message and pygame.time.get_ticks() - self.error_timer > self.ERROR_DISPLAY_TIME:
            self.error_message = None

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
                    self.handle_click(event.pos)
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    else:
                        self.handle_key(event.key)
            
            self.update()  # Add update call
            self.draw()
        
        pygame.quit()

