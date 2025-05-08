# launcher.py
import random
import pygame
import sys
import json
import importlib
import math
import os
from pathlib import Path

# Initialize Pygame
pygame.init()

# Display constants
BASE_WIDTH, BASE_HEIGHT = 1280, 800  # Base resolution for scaling
STORAGE_LIMIT = 10  # MB

# Colors
COLORS = {
    'background': (18, 18, 18),
    'surface': (30, 30, 30),
    'primary': (40, 144, 255),
    'secondary': (255, 105, 180),
    'success': (76, 175, 80),
    'warning': (255, 193, 7),
    'error': (244, 67, 54),
    'text': (245, 245, 245),
    'accent': (156, 39, 176)
}

class DisplayManager:
    def __init__(self):
        self.fullscreen = True
        self.screen = None
        self.scale_factor = 1.0
        self.actual_width, self.actual_height = BASE_WIDTH, BASE_HEIGHT
        self.init_display()
        
    def init_display(self):
        try:
            if self.fullscreen:
                self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
                self.actual_width, self.actual_height = self.screen.get_size()
            else:
                self.screen = pygame.display.set_mode((BASE_WIDTH, BASE_HEIGHT))
                self.actual_width, self.actual_height = BASE_WIDTH, BASE_HEIGHT
            
            # Calculate scale factor based on height to maintain aspect ratio
            self.scale_factor = self.actual_height / BASE_HEIGHT
        except Exception as e:
            print(f"Display initialization error: {e}")
            self.screen = pygame.display.set_mode((BASE_WIDTH, BASE_HEIGHT))
            self.actual_width, self.actual_height = BASE_WIDTH, BASE_HEIGHT
            self.scale_factor = 1.0
            self.fullscreen = False
            
    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        self.init_display()
        
    def get_scaled_value(self, value):
        return int(value * self.scale_factor)

# Initialize display
display = DisplayManager()
screen = display.screen
pygame.display.set_caption("Multigames")
clock = pygame.time.Clock()

# Load fonts with scaling
def load_font(font_path, size, bold=False):
    scaled_size = display.get_scaled_value(size)
    try:
        if bold:
            return pygame.font.Font(font_path, scaled_size)
        return pygame.font.Font(font_path, scaled_size)
    except:
        if bold:
            return pygame.font.SysFont("Arial", scaled_size, bold=True)
        return pygame.font.SysFont("Arial", scaled_size)

title_font = load_font("assets/fonts/Poppins-Bold.ttf", 48, bold=True)
text_font = load_font("assets/fonts/Roboto-Medium.ttf", 24)
small_font = load_font("assets/fonts/Roboto-Medium.ttf", 18)

class GameLauncher:
    def __init__(self):
        self.games = self.load_game_list()
        self.installed = self.load_installed()
        self.notification = None
        self.selected_game = None

    def load_game_list(self):
        games = {}
        game_dir = Path(__file__).parent / 'games'
        for file in game_dir.glob('*.py'):
            if file.name == '__init__.py':
                continue
            game_id = file.stem
            spec = importlib.util.spec_from_file_location(game_id, file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            games[game_id] = {
                'name': getattr(module, 'GAME_NAME', game_id),
                'size': getattr(module, 'GAME_SIZE', 10),
                'image': getattr(module, 'COVER_ART', 'assets/covers/default.png'),
                'module': module
            }
        return games

    def load_installed(self):
        try:
            with open('installed.json') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def save_installed(self):
        with open('installed.json', 'w') as f:
            json.dump(self.installed, f)

    def get_used_space(self):
        return sum(self.games[game]['size'] for game in self.installed)

    def install_game(self, game_id):
        if game_id in self.installed:
            self.show_notification("Game already installed!", 'warning')
            return False
            
        required = self.games[game_id]['size']
        if self.get_used_space() + required > STORAGE_LIMIT:
            needed = required - (STORAGE_LIMIT - self.get_used_space())
            self.show_notification(f"Need {needed}MB more space!", 'error')
            return False
            
        self.installed.append(game_id)
        self.save_installed()
        self.show_notification(f"{self.games[game_id]['name']} installed!", 'success')
        return True

    def uninstall_game(self, game_id):
        if game_id in self.installed:
            self.installed.remove(game_id)
            self.save_installed()
            self.show_notification(f"{self.games[game_id]['name']} removed!", 'success')
            return True
        return False

    def show_notification(self, message, type='info'):
        self.notification = {
            'message': message,
            'type': type,
            'timer': 120
        }

class Particle:
    def __init__(self):
        self.x = random.randint(0, display.actual_width)
        self.y = random.randint(0, display.actual_height)
        self.size = random.randint(1, 3)
        self.speed = random.uniform(0.1, 0.5)
        self.color = (255, 255, 255)  # White stars

    def update(self):
        self.y -= self.speed
        if self.y < 0:
            self.y = display.actual_height
            self.x = random.randint(0, display.actual_width)

class GameCard:
    def __init__(self, game_data, x, y, installed=False):
        self.game_data = game_data
        self.x = x
        self.y = y
        self.width = display.get_scaled_value(300)
        self.height = display.get_scaled_value(160)
        self.installed = installed
        self.hover = False
        self.animation = 0
        
        try:
            self.cover = pygame.image.load(game_data['image']).convert_alpha()
            self.cover = pygame.transform.smoothscale(self.cover, (self.width, self.height))
        except:
            self.cover = pygame.Surface((self.width, self.height))
            self.cover.fill((40, 40, 40))

    def draw(self, surface):
        if self.hover:
            self.animation = min(self.animation + 0.1, 1)
        else:
            self.animation = max(self.animation - 0.1, 0)
        
        surface.blit(self.cover, (self.x, self.y))
        
        overlay = pygame.Surface((self.width, self.height))
        overlay.set_alpha(int(150 * (1 - self.animation)))
        overlay.fill(COLORS['surface'])
        surface.blit(overlay, (self.x, self.y))
        
        title = text_font.render(self.game_data['name'], True, COLORS['text'])
        title_rect = title.get_rect(center=(self.x + self.width//2, self.y + self.height - display.get_scaled_value(30)))
        surface.blit(title, title_rect)
        
        status_color = COLORS['success'] if self.installed else COLORS['secondary']
        pygame.draw.circle(surface, status_color, (self.x + display.get_scaled_value(20), self.y + display.get_scaled_value(20)), display.get_scaled_value(6))

class StorageMeter:
    def __init__(self):
        self.radius = display.get_scaled_value(120)
        self.center = (display.actual_width - display.get_scaled_value(140), display.get_scaled_value(100))

    def draw(self, surface, used, total):
        percentage = used / total
        start_angle = math.pi / 2
        end_angle = start_angle + 2 * math.pi * percentage
        
        for i in range(0, 100):
            angle = start_angle + (end_angle - start_angle) * i/100
            color = (int(40 + 2*i), int(144 - 1.44*i), 255)
            pygame.draw.arc(surface, color, 
                           (self.center[0] - self.radius, self.center[1] - self.radius,
                            self.radius*2, self.radius*2),
                           angle - 0.03, angle, display.get_scaled_value(8))
        
        text = title_font.render(f"{used}/{total}", True, COLORS['text'])
        text_rect = text.get_rect(center=self.center)
        surface.blit(text, text_rect)

class Menu:
    def __init__(self, launcher):
        self.launcher = launcher
        self.particles = [Particle() for _ in range(50)]
        self.storage_meter = StorageMeter()

    def draw_background(self):
        screen.fill(COLORS['background'])
        for p in self.particles:
            p.update()
            pygame.draw.circle(screen, p.color, (int(p.x), int(p.y)), p.size)

    def draw_header(self):
        pygame.draw.rect(screen, (70, 70, 255), (0, 0, display.actual_width, display.get_scaled_value(80)))
        title = title_font.render("MultiGames", True, (255, 255, 255))
        screen.blit(title, (display.get_scaled_value(40), display.get_scaled_value(20)))
        self.storage_meter.draw(screen, self.launcher.get_used_space(), STORAGE_LIMIT)

    def draw_game_grid(self):
        installed_games = [g for g in self.launcher.installed if g in self.launcher.games]
        available_games = [g for g in self.launcher.games if g not in installed_games]
        
        # Installed games
        y = display.get_scaled_value(150)
        screen.blit(text_font.render("Your Library", True, COLORS['text']), (display.get_scaled_value(40), display.get_scaled_value(120)))
        
        card_width = display.get_scaled_value(300)
        card_height = display.get_scaled_value(160)
        horizontal_spacing = display.get_scaled_value(320)
        vertical_spacing = display.get_scaled_value(180)
        
        for i, game_id in enumerate(installed_games):
            card = GameCard(self.launcher.games[game_id], 
                          display.get_scaled_value(40) + (i % 3) * horizontal_spacing, 
                          y + (i // 3) * vertical_spacing, 
                          True)
            card.draw(screen)
        
        # Store section with extra spacing
        store_y = y + ((len(installed_games) + 2) // 3 * vertical_spacing) + display.get_scaled_value(50)
        screen.blit(text_font.render("Store", True, COLORS['text']), (display.get_scaled_value(40), store_y - display.get_scaled_value(30)))
        
        for i, game_id in enumerate(available_games):
            card = GameCard(self.launcher.games[game_id], 
                          display.get_scaled_value(40) + (i % 3) * horizontal_spacing, 
                          store_y + (i // 3) * vertical_spacing)
            card.draw(screen)

    def draw_notification(self):
        if self.launcher.notification:
            text = text_font.render(self.launcher.notification['message'], True, COLORS['text'])
            
            notification_width = display.get_scaled_value(400)
            notification_height = display.get_scaled_value(50)
            bg_rect = pygame.Rect(
                display.actual_width/2 - notification_width/2, 
                display.actual_height - display.get_scaled_value(80), 
                notification_width, 
                notification_height
            )
            pygame.draw.rect(screen, COLORS['surface'], bg_rect, border_radius=display.get_scaled_value(25))
            pygame.draw.rect(screen, COLORS[self.launcher.notification['type']], bg_rect, display.get_scaled_value(2), display.get_scaled_value(25))
            screen.blit(text, text.get_rect(center=bg_rect.center))
            
            self.launcher.notification['timer'] -= 1
            if self.launcher.notification['timer'] <= 0:
                self.launcher.notification = None

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
                
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F11:
                    display.toggle_fullscreen()
                    # Update particles for new screen size
                    self.particles = [Particle() for _ in range(50)]
                
            if event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                installed_games = [g for g in self.launcher.installed if g in self.launcher.games]
                available_games = [g for g in self.launcher.games if g not in installed_games]
                
                # Left click handling
                if event.button == 1:
                    # Check installed games for launching
                    for i, game_id in enumerate(installed_games):
                        x = display.get_scaled_value(40) + (i % 3) * display.get_scaled_value(320)
                        y = display.get_scaled_value(150) + (i // 3) * display.get_scaled_value(180)
                        card_rect = pygame.Rect(x, y, display.get_scaled_value(300), display.get_scaled_value(160))
                        if card_rect.collidepoint(pos):
                            # Launch the game
                            game_module = self.launcher.games[game_id]['module']
                            game_module.run()
                            # Restore launcher display
                            display.init_display()
                            return
                    
                    # Check available games for installation
                    for i, game_id in enumerate(available_games):
                        x = display.get_scaled_value(40) + (i % 3) * display.get_scaled_value(320)
                        y = display.get_scaled_value(150) + (len(installed_games) + 2) // 3 * display.get_scaled_value(180) + display.get_scaled_value(50) + (i // 3) * display.get_scaled_value(180)
                        card_rect = pygame.Rect(x, y, display.get_scaled_value(300), display.get_scaled_value(160))
                        if card_rect.collidepoint(pos):
                            self.launcher.install_game(game_id)
                
                # Right click to uninstall
                elif event.button == 3:
                    for i, game_id in enumerate(installed_games):
                        x = display.get_scaled_value(40) + (i % 3) * display.get_scaled_value(320)
                        y = display.get_scaled_value(150) + (i // 3) * display.get_scaled_value(180)
                        card_rect = pygame.Rect(x, y, display.get_scaled_value(300), display.get_scaled_value(160))
                        if card_rect.collidepoint(pos):
                            self.launcher.uninstall_game(game_id)

    def run(self):
        while True:
            self.handle_events()
            self.draw_background()
            self.draw_header()
            self.draw_game_grid()
            self.draw_notification()
            pygame.display.flip()
            clock.tick(60)

if __name__ == "__main__":
    launcher = GameLauncher()
    menu = Menu(launcher)
    menu.run()
