# insult_soccer/scenes/menu_scene.py
import pygame

from engine.ui import Scene, Button


class MenuScene(Scene):
    def __init__(self, game):
        super().__init__(game)
        self.font_title = pygame.font.Font(None, 78)
        self.font_hint = pygame.font.Font(None, 26)

        self.boton_jugar = Button(300, 340, 200, 56, "Jugar", self.jugar)
        self.boton_salir = Button(300, 410, 200, 56, "Salir", self.salir)
        self.t = 0.0

    def on_enter(self):
        self.game.audio.play_music(volume=0.4)

    def jugar(self):
        self.game.audio.play_sound("click")
        self.game.audio.play_sound("whistle")
        self.game.change_scene("match")

    def salir(self):
        self.game.audio.play_sound("click")
        self.game.running = False

    def handle_events(self, events):
        for event in events:
            self.boton_jugar.handle_event(event)
            self.boton_salir.handle_event(event)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.game.running = False
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self.jugar()

    def update(self):
        self.t += 1.0 / self.game.fps

    def draw(self, surface):
        try:
            surface.blit(self.game.assets.get_image("campo"), (0, 0))
        except Exception:
            surface.fill((30, 110, 55))

        # Oscurecer para que se lea el texto
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        surface.blit(overlay, (0, 0))

        try:
            logo = self.game.assets.get_image("logo")
            surface.blit(logo, logo.get_rect(centerx=surface.get_width() // 2, y=120))
        except Exception:
            self._text_center(surface, "INSULT SOCCER", 78, 130, (255, 240, 120))

        self._text_center(surface, "Futbol de duelo verbal", 34, 230, (230, 240, 255))
        self._text_center(surface, "Primero en meter 3 goles gana", 26, 275,
                          (180, 220, 190))

        # Balón que bota
        try:
            balon = self.game.assets.get_image("balon")
            import math
            y = 300 + int(math.sin(self.t * 3) * 10)
            surface.blit(balon, balon.get_rect(center=(surface.get_width() // 2, y)))
        except Exception:
            pass

        self.boton_jugar.draw(surface)
        self.boton_salir.draw(surface)

    def _text_center(self, surface, texto, size, y, color):
        font = pygame.font.Font(None, size)
        img = font.render(texto, True, color)
        surface.blit(img, img.get_rect(centerx=surface.get_width() // 2, y=y))
