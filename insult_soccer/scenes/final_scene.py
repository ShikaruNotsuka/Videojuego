# insult_soccer/scenes/final_scene.py
import pygame

from engine.ui import Scene, Button
from engine.ui_elements import Label, Panel


class FinalScene(Scene):
    def __init__(self, game, goles_jugador=0, goles_rival=0):
        super().__init__(game)
        self.goles_jugador = goles_jugador
        self.goles_rival = goles_rival
        self.ganaste = goles_jugador > goles_rival

        self.font_grande = pygame.font.Font(None, 84)
        self.font = pygame.font.Font(None, 40)

        self.boton_revancha = Button(280, 400, 240, 54, "Revancha", self.revancha)
        self.boton_menu = Button(280, 466, 240, 54, "Menú", self.menu)
        self.t = 0.0

    def on_enter(self):
        self.game.audio.play_sound("whistle")
        if self.ganaste:
            self.game.audio.play_sound("cheer")
        else:
            self.game.audio.play_sound("wrong")

    def revancha(self):
        self.game.audio.play_sound("click")
        self.game.change_scene("match")

    def menu(self):
        self.game.audio.play_sound("click")
        self.game.change_scene("menu")

    def handle_events(self, events):
        for event in events:
            self.boton_revancha.handle_event(event)
            self.boton_menu.handle_event(event)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.game.change_scene("menu")
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self.revancha()

    def update(self):
        self.t += 1.0 / self.game.fps

    def draw(self, surface):
        surface.fill((12, 24, 40))
        w = surface.get_width()

        titulo = "¡VICTORIA!" if self.ganaste else "DERROTA"
        color = (140, 240, 150) if self.ganaste else (255, 120, 120)
        img = self.font_grande.render(titulo, True, color)
        surface.blit(img, img.get_rect(centerx=w // 2, y=140))

        panel = Panel((w // 2 - 160, 250, 320, 70),
                      color=(0, 0, 0, 160), border=(240, 240, 240, 255))
        panel.draw(surface)
        marcador = Label(f"{self.goles_jugador}  -  {self.goles_rival}",
                        (w // 2, 285), size=52, color=(255, 255, 255),
                        align="center")
        marcador.draw(surface)

        sub = "Tu equipo" if self.ganaste else "El rival"
        sub += " gano el duelo verbal"
        s = self.font.render(sub, True, (210, 220, 235))
        surface.blit(s, s.get_rect(centerx=w // 2, y=336))

        self.boton_revancha.draw(surface)
        self.boton_menu.draw(surface)
