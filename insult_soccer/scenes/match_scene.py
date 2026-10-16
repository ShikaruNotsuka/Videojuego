# insult_soccer/scenes/match_scene.py
"""
Escena del partido: duelos verbales por turnos.

En cada turno aparece un reto de opción múltiple (engine.challenge.Challenge).
- Acierta  -> el balón avanza y metes gol (sfx kick + cheer).
- Falla    -> gol del rival (sfx wrong).
El primero en llegar a 3 goles gana y se pasa a la escena 'final'.
"""
import random

import pygame

from engine.ui import Scene
from engine.ui_elements import Label, Panel
from engine.challenge import Challenge

# Puntos de meta (jugador ataca arriba, rival abajo).
META_JUGADOR = (400, 78)
META_RIVAL = (400, 522)
CENTRO = (400, 300)

TIME_LIMIT = 6.0
GOLES_PARA_GANAR = 3


RETOS = [
    {
        "prompt": "El rival suelta: '¡Juegas como mi abuela!'",
        "opciones": [
            "Tu abuela al menos entiende el fuera de juego",
            "Gracias, me entrenó ella",
            "¿Y tú por qué miras tanto a mi abuela?",
        ],
        "correcta": 0,
    },
    {
        "prompt": "El rival dice: '¡No corrés ni para el autobús!'",
        "opciones": [
            "El autobús me espera, tú llegas tarde a todo",
            "Cierto, prefiero el tren",
            "Autobús... ¿cuál?",
        ],
        "correcta": 0,
    },
    {
        "prompt": "El rival se burla: '¡Tus botines son de plástico!'",
        "opciones": [
            "Y aun así te ganan los de plástico",
            "Los compré en oferta, gracias",
            "Son reciclados, cuido el planeta",
        ],
        "correcta": 0,
    },
    {
        "prompt": "El rival grita: '¡Eres más lento que una tortuga!'",
        "opciones": [
            "Y aun así te llego a la pelota antes",
            "Me gustan las tortugas",
            "La tortuga gana la carrera al final",
        ],
        "correcta": 0,
    },
    {
        "prompt": "El rival dice: '¡Apostaría mi casa a que pierdes!'",
        "opciones": [
            "Empieza a hacer las valijas",
            "No apuestes, es de mala educación",
            "¿Me la vendes barata?",
        ],
        "correcta": 0,
    },
    {
        "prompt": "El rival se ríe: '¡Hasta el arco se aburre contigo!'",
        "opciones": [
            "El arco tiene miedo de tus remates",
            "El arco y yo somos amigos",
            "Los arcos no sienten nada",
        ],
        "correcta": 0,
    },
    {
        "prompt": "El rival afirma: '¡Tú no sabes ni tirar un penal!'",
        "opciones": [
            "Mírame ahora y toma nota",
            "Los penales son de cobarde",
            "¿Me enseñas tú?",
        ],
        "correcta": 0,
    },
    {
        "prompt": "El rival dice: '¡Mi equipo juega mejor sin ti... digo, sin mí!'",
        "opciones": [
            "Se te trabó la lengua y el cerebro",
            "Hablás solo, ¿eh?",
            "Sin ti juegan mejor, es verdad",
        ],
        "correcta": 0,
    },
    {
        "prompt": "El rival se burla: '¡Ese peinado no ayuda a correr!'",
        "opciones": [
            "A mi peinado le sobra velocidad para dos",
            "El peinado va conmigo a todos lados",
            "Y el tuyo sí que vuela... la peluca",
        ],
        "correcta": 0,
    },
    {
        "prompt": "El rival reta: '¡A que no la metes ni en sueños!'",
        "opciones": [
            "Estoy despierto y ya vas perdiendo",
            "Sueño con la victoria, es distinto",
            "¿Contamos ovejas o goles?",
        ],
        "correcta": 0,
    },
]


class MatchScene(Scene):
    def __init__(self, game):
        super().__init__(game)

        self.font_grande = pygame.font.Font(None, 64)
        self.font = pygame.font.Font(None, 34)
        self.font_chico = pygame.font.Font(None, 26)

        self.marcador_jugador = 0
        self.marcador_rival = 0

        self.retos = list(RETOS)
        random.shuffle(self.retos)
        self.reto_idx = 0

        self.challenge = None
        self.estado = "espera"     # espera | jugada | resultado
        self.timer = 0.9
        self.mensaje = "¡Que empiece el duelo!"
        self.ultimo_acierto = True

        self.balon = pygame.Vector2(CENTRO)
        self.balon_objetivo = pygame.Vector2(CENTRO)
        self.kick_timer = 0.0

    # ------------------------------------------------------------------ #
    def on_enter(self):
        self.game.audio.play_music(volume=0.4)
        self.game.audio.play_sound("whistle")

    def on_exit(self):
        pass

    # ------------------------------------------------------------------ #
    def _nuevo_reto(self):
        reto = self.retos[self.reto_idx % len(self.retos)]
        self.reto_idx += 1
        self.challenge = Challenge(
            reto["prompt"], reto["opciones"], reto["correcta"],
            time_limit=TIME_LIMIT,
        )
        self.challenge.start()
        self.estado = "jugada"
        self.mensaje = "¡Responde rapido!"
        self.balon_objetivo.update(CENTRO)
        self.kick_timer = 0.0

    def _resolver(self, correcto):
        self.ultimo_acierto = bool(correcto)
        if correcto:
            self.game.audio.play_sound("correct")
            self.game.audio.play_sound("kick")
            self.game.audio.play_sound("cheer")
            self.marcador_jugador += 1
            self.mensaje = "¡GOL de tu equipo!"
            self.balon_objetivo.update(META_JUGADOR)
            self.kick_timer = 0.5
        else:
            self.game.audio.play_sound("wrong")
            self.marcador_rival += 1
            self.mensaje = "Respuesta floja... gol del rival"
            self.balon_objetivo.update(META_RIVAL)

        self.estado = "resultado"
        self.timer = 1.6

    # ------------------------------------------------------------------ #
    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.game.change_scene("menu")
                return
            if self.estado == "jugada" and self.challenge is not None:
                self.challenge.handle_event(event)

    def update(self):
        dt = 1.0 / self.game.fps
        self.balon += (self.balon_objetivo - self.balon) * min(1.0, dt * 5.0)
        if self.kick_timer > 0:
            self.kick_timer -= dt

        if self.estado == "espera":
            self.timer -= dt
            if self.timer <= 0:
                self._nuevo_reto()

        elif self.estado == "jugada":
            if self.challenge is not None and self.challenge.active:
                self.challenge.update(dt)
            if self.challenge is not None and self.challenge.result is not None:
                self._resolver(self.challenge.result)

        elif self.estado == "resultado":
            self.timer -= dt
            if self.timer <= 0:
                if (self.marcador_jugador >= GOLES_PARA_GANAR or
                        self.marcador_rival >= GOLES_PARA_GANAR):
                    self.game.change_scene(
                        "final",
                        goles_jugador=self.marcador_jugador,
                        goles_rival=self.marcador_rival,
                    )
                else:
                    self._nuevo_reto()

    # ------------------------------------------------------------------ #
    def _blit(self, surface, nombre, **kwargs):
        try:
            img = self.game.assets.get_image(nombre)
            surface.blit(img, img.get_rect(**kwargs))
        except Exception:
            pass

    def draw(self, surface):
        w, h = surface.get_size()
        try:
            surface.blit(self.game.assets.get_image("campo"), (0, 0))
        except Exception:
            surface.fill((30, 110, 55))

        # Porterías
        self._blit(surface, "arco", midbottom=(400, 90))
        arc2 = None
        try:
            arc2 = pygame.transform.flip(self.game.assets.get_image("arco"), False, True)
            surface.blit(arc2, arc2.get_rect(midtop=(400, 510)))
        except Exception:
            pass

        # Jugadores
        kick_local = self.kick_timer > 0
        jug_azul = "jugador_azul_kick" if kick_local else "jugador_azul"
        jug_rojo = "jugador_rojo_kick" if kick_local else "jugador_rojo"
        bx = int(self.balon.x)
        self._blit(surface, jug_azul, midbottom=(bx - 70, 470))
        self._blit(surface, jug_rojo, midbottom=(bx + 70, 470))

        # Balón
        self._blit(surface, "balon", center=(bx, int(self.balon.y)))

        # Marcador (engine.ui_elements)
        panel = Panel((w // 2 - 190, 12, 380, 58),
                      color=(10, 15, 25, 190), border=(240, 240, 240, 255))
        panel.draw(surface)
        marcador = Label(
            f"TU {self.marcador_jugador}   -   {self.marcador_rival} RIVAL",
            (w // 2, 41), size=40, color=(255, 255, 255), align="center",
        )
        marcador.draw(surface)
        meta = Label(f"Primero a {GOLES_PARA_GANAR}", (w // 2, 78),
                     size=22, color=(255, 240, 140), align="center")
        meta.draw(surface)

        # Mensaje de estado
        if self.mensaje:
            color = (140, 240, 150) if self.ultimo_acierto else (255, 150, 140)
            msg = self.font.render(self.mensaje, True, color)
            surface.blit(msg, msg.get_rect(centerx=w // 2, y=100))

        # Reto activo / resultado del reto
        if self.challenge is not None and self.estado in ("jugada", "resultado"):
            self.challenge.draw(surface)

        # Ayuda
        ayuda = self.font_chico.render(
            "Flechas/W-S elegir   ENTER responder   ESC menu",
            True, (235, 235, 235),
        )
        surface.blit(ayuda, (12, h - 30))

        # Icono del último resultado del duelo verbal
        if self.estado == "resultado":
            icono = "icono_correcto" if self.ultimo_acierto else "icono_fallo"
            self._blit(surface, icono, center=(bx - 70, 400))
