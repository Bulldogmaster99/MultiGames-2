# launcher.py
import random
import pygame
import sys
import json
import importlib
import math
import os
from pathlib import Path

# Constants
WIDTH, HEIGHT = 1280, 800
STORAGE_LIMIT = 200  # MB
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

# Initialize Pygame
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Multigames")
clock = pygame.time.Clock()

# Load fonts
try:
    title_font = pygame.font.Font("assets/fonts/Poppins-Bold.ttf", 48)
    text_font = pygame.font.Font("assets/fonts/Roboto-Medium.ttf", 24)
    small_font = pygame.font.Font("assets/fonts/Roboto-Medium.ttf", 18)
except:
    title_font = pygame.font.SysFont("Arial", 48, bold=True)
    text_font = pygame.font.SysFont("Arial", 24)
    small_font = pygame.font.SysFont("Arial", 18)

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
        self.x = random.randint(0, WIDTH)
        self.y = random.randint(0, HEIGHT)
        self.size = random.randint(1, 3)
        self.speed = random.uniform(0.1, 0.5)
        self.color = (255, 255, 255)  # White stars

    def update(self):
        self.y -= self.speed
        if self.y < 0:
            self.y = HEIGHT
            self.x = random.randint(0, WIDTH)

class GameCard:
    def __init__(self, game_data, x, y, installed=False):
        self.game_data = game_data
        self.x = x
        self.y = y
        self.width = 300
        self.height = 160
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
        title_rect = title.get_rect(center=(self.x + self.width//2, self.y + self.height - 30))
        surface.blit(title, title_rect)
        
        status_color = COLORS['success'] if self.installed else COLORS['secondary']
        pygame.draw.circle(surface, status_color, (self.x + 20, self.y + 20), 6)

class StorageMeter:
    def __init__(self):
        self.radius = 120
        self.center = (WIDTH - 140, 100)

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
                           angle - 0.03, angle, 8)
        
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
        pygame.draw.rect(screen, (0, 0, 0), (0, 0, WIDTH, 80))  # Black header
        title = title_font.render("MultiGames", True, (255, 255, 255))  # White text
        screen.blit(title, (40, 20))
        self.storage_meter.draw(screen, self.launcher.get_used_space(), STORAGE_LIMIT)

    def draw_game_grid(self):
        installed_games = [g for g in self.launcher.installed if g in self.launcher.games]
        available_games = [g for g in self.launcher.games if g not in installed_games]
        
        # Installed games
        y = 150
        screen.blit(text_font.render("Your Library", True, COLORS['text']), (40, 120))
        for i, game_id in enumerate(installed_games):
            card = GameCard(self.launcher.games[game_id], 40 + (i % 3)*320, y + (i // 3)*180, True)
            card.draw(screen)
        
        # Store section with extra spacing
        store_y = 150 + ((len(installed_games) + 2) // 3) * 180 + 50
        screen.blit(text_font.render("Store", True, COLORS['text']), (40, store_y - 30))
        for i, game_id in enumerate(available_games):
            card = GameCard(self.launcher.games[game_id], 40 + (i % 3)*320, store_y + (i // 3)*180)
            card.draw(screen)

    def draw_notification(self):
        if self.launcher.notification:
            text = text_font.render(self.launcher.notification['message'], True, COLORS['text'])
            
            bg_rect = pygame.Rect(WIDTH/2 - 200, HEIGHT - 80, 400, 50)
            pygame.draw.rect(screen, COLORS['surface'], bg_rect, border_radius=25)
            pygame.draw.rect(screen, COLORS[self.launcher.notification['type']], bg_rect, 2, 25)
            screen.blit(text, text.get_rect(center=bg_rect.center))
            
            self.launcher.notification['timer'] -= 1
            if self.launcher.notification['timer'] <= 0:
                self.launcher.notification = None

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
                
            if event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                installed_games = [g for g in self.launcher.installed if g in self.launcher.games]
                available_games = [g for g in self.launcher.games if g not in installed_games]
                
                # Left click handling
                if event.button == 1:
                    # Check installed games for launching
                    for i, game_id in enumerate(installed_games):
                        x = 40 + (i % 3)*320
                        y = 150 + (i // 3)*180
                        card_rect = pygame.Rect(x, y, 300, 160)
                        if card_rect.collidepoint(pos):
                            # Launch the game
                            game_module = self.launcher.games[game_id]['module']
                            game_module.run()
                            # Restore launcher display
                            pygame.display.set_mode((WIDTH, HEIGHT))
                            return
                    
                    # Check available games for installation
                    for i, game_id in enumerate(available_games):
                        x = 40 + (i % 3)*320
                        y = 150 + ((len(installed_games) + 2) // 3)*180 + 50 + (i // 3)*180
                        card_rect = pygame.Rect(x, y, 300, 160)
                        if card_rect.collidepoint(pos):
                            self.launcher.install_game(game_id)
                
                # Right click to uninstall
                elif event.button == 3:
                    for i, game_id in enumerate(installed_games):
                        x = 40 + (i % 3)*320
                        y = 150 + (i // 3)*180
                        card_rect = pygame.Rect(x, y, 300, 160)
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
