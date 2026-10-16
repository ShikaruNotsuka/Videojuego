# platformer/scenes/game_over_scene.py
import pygame

from engine.ui import Scene, Button


class GameOverScene(Scene):
    def __init__(self, game, win=False):
        super().__init__(game)
        self.win = win
        self.font_grande = pygame.font.Font(None, 80)
        self.menu_button = Button(412, 420, 200, 56, "Menú", self.volver_al_menu)

    def volver_al_menu(self):
        self.game.change_scene("menu")

    def handle_events(self, events):
        for event in events:
            self.menu_button.handle_event(event)

    def draw(self, surface):
        surface.fill((40, 60, 110))
        titulo = "¡NIVEL COMPLETADO!" if self.win else "GAME OVER"
        color = (140, 240, 140) if self.win else (240, 90, 90)
        t = self.font_grande.render(titulo, True, color)
        surface.blit(t, t.get_rect(centerx=surface.get_width() // 2, centery=280))
        self.menu_button.draw(surface)
