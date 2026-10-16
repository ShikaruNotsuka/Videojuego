# platformer/scenes/menu_scene.py
import pygame

from engine.ui import Scene, Button


class MenuScene(Scene):
    def __init__(self, game):
        super().__init__(game)
        self.font_title = pygame.font.Font(None, 74)
        self.title = self.font_title.render("MARIO CLONE", True, (255, 255, 255))
        self.start_button = Button(412, 320, 200, 56, "Jugar", self.start_game)

    def on_enter(self):
        self.game.audio.play_music(volume=0.4)

    def start_game(self):
        self.game.change_scene("game")

    def handle_events(self, events):
        for event in events:
            self.start_button.handle_event(event)

    def draw(self, surface):
        surface.fill((92, 148, 252))
        surface.blit(self.title, self.title.get_rect(centerx=surface.get_width() // 2, y=150))
        self.start_button.draw(surface)
