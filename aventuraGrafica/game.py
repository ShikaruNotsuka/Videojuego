"""Aventura gráfica point-and-click: La baliza olvidada."""

import math
from enum import Enum, auto

import pygame

from engine.dialogue_manager import DialogueManager
from engine.game_loop import GameLoop
from engine.hotspot import Hotspot
from engine.inventory import Inventory, Item


SCREEN_WIDTH = 960
SCREEN_HEIGHT = 640
WORLD_HEIGHT = 490
UI_TOP = WORLD_HEIGHT

INK = (20, 19, 35)
PANEL = (37, 31, 43)
GOLD = (230, 184, 104)
PAPER = (241, 220, 169)


class GameState(Enum):
    IDLE = auto()
    WALKING = auto()
    INTERACTING = auto()
    DIALOGUE = auto()
    WON = auto()


class AventuraGrafica(GameLoop):
    """Controla la aventura, sus escenas, el inventario y las interacciones."""

    VERBS = ("MIRAR", "USAR", "HABLAR", "COGER")

    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, "La baliza olvidada", 60)
        pygame.mouse.set_visible(True)
        self.font = pygame.font.Font(None, 25)
        self.small_font = pygame.font.Font(None, 20)
        self.large_font = pygame.font.Font(None, 34)
        self.dialogue = DialogueManager(self.screen, font_size=24, color=PAPER)
        self.inventory = Inventory(capacity=6)
        self.scene = "plaza"
        self.verb = "MIRAR"
        self.state = GameState.IDLE
        self.player = pygame.Vector2(480, 420)
        self.target = self.player.copy()
        self.pending_hotspot = None
        self.pending_item = None
        self.dialogue_choices = []
        self.message = "La noche cae sobre Puerto Bruma. La baliza lleva años apagada."
        self.message_timer = 0
        self.debug_hotspots = False
        self.fountain_solved = False
        self.gate_unlocked = False
        self.lens_progress = 0
        self.lens_order = ("luna", "estrella", "sol")
        self.hotspots = {}
        self.walkable = {}
        self._setup_world()
        self._set_scene("plaza", starting_position=(480, 420))
        self._say("La noche cae sobre Puerto Bruma. La baliza lleva años apagada.")

    def _setup_world(self):
        self.walkable = {
            "plaza": [(35, 470), (90, 420), (260, 385), (380, 400),
                      (510, 380), (650, 408), (815, 375), (950, 425), (950, 480)],
            "taberna": [(90, 470), (155, 405), (280, 375), (410, 390),
                        (560, 365), (700, 395), (870, 430), (930, 480)],
            "faro": [(40, 470), (155, 410), (285, 400), (415, 365),
                     (550, 395), (690, 355), (830, 390), (950, 430), (950, 480)],
        }
        self.hotspots = {
            "plaza": [
                Hotspot((110, 190, 160, 205), "Puerta de la taberna"),
                Hotspot((390, 285, 190, 150), "Fuente rota"),
                Hotspot((38, 360, 78, 112), "Barril"),
                Hotspot((806, 350, 140, 125), "Camino al faro"),
                Hotspot((270, 190, 70, 185), "Cartel del puerto"),
            ],
            "taberna": [
                Hotspot((12, 280, 110, 195), "Salir a la plaza"),
                Hotspot((350, 180, 190, 220), "Tabernero"),
                Hotspot((650, 330, 190, 95), "Cuerda"),
                Hotspot((560, 175, 190, 130), "Nota de las lentes"),
                Hotspot((165, 325, 155, 105), "Mesa"),
            ],
            "faro": [
                Hotspot((15, 340, 130, 135), "Volver al puerto"),
                Hotspot((315, 95, 215, 250), "Puerta del faro"),
                Hotspot((655, 230, 78, 82), "Lente de la luna"),
                Hotspot((747, 230, 78, 82), "Lente de la estrella"),
                Hotspot((839, 230, 78, 82), "Lente del sol"),
                Hotspot((548, 345, 140, 95), "Panel de la baliza"),
            ],
        }

    def _set_scene(self, scene, starting_position=None):
        self.scene = scene
        self.state = GameState.IDLE
        self.pending_hotspot = None
        self.target = self.player.copy()
        if starting_position is not None:
            self.player.update(starting_position)
            self.target.update(starting_position)

    def _say(self, text, duration=3.5):
        self.message = text
        self.message_timer = pygame.time.get_ticks() + int(duration * 1000)
        self.dialogue.show_message(text, duration_seconds=duration, position="top")

    def _point_in_polygon(self, point, polygon):
        x, y = point
        inside = False
        previous = polygon[-1]
        for current in polygon:
            x1, y1 = previous
            x2, y2 = current
            if (y1 > y) != (y2 > y):
                crossing_x = (x2 - x1) * (y - y1) / (y2 - y1) + x1
                if x < crossing_x:
                    inside = not inside
            previous = current
        return inside

    def _nearest_walkable(self, point):
        polygon = self.walkable[self.scene]
        if self._point_in_polygon(point, polygon):
            return pygame.Vector2(point)
        candidate = None
        best_distance = float("inf")
        for index, start in enumerate(polygon):
            end = polygon[(index + 1) % len(polygon)]
            segment = pygame.Vector2(end) - pygame.Vector2(start)
            length_squared = segment.length_squared()
            if length_squared == 0:
                closest = pygame.Vector2(start)
            else:
                fraction = max(0, min(1, (pygame.Vector2(point) - pygame.Vector2(start)).dot(segment)
                                         / length_squared))
                closest = pygame.Vector2(start) + segment * fraction
            distance = closest.distance_squared_to(point)
            if distance < best_distance:
                candidate = closest
                best_distance = distance
        return candidate

    def _start_interaction(self, hotspot):
        if self.state in (GameState.DIALOGUE, GameState.WON):
            return
        self.pending_hotspot = hotspot
        self.pending_item = self.inventory.selected if self.verb == "USAR" else None
        self.target = self._nearest_walkable(hotspot.rect.center)
        self.state = GameState.WALKING
        if self.player.distance_to(self.target) < 13:
            self._arrive_at_hotspot()

    def _arrive_at_hotspot(self):
        hotspot = self.pending_hotspot
        self.pending_hotspot = None
        self.state = GameState.INTERACTING
        if hotspot is not None:
            self._interact(hotspot.name, self.verb, self.pending_item)
        if self.state == GameState.INTERACTING:
            self.state = GameState.IDLE

    def _look(self, name):
        descriptions = {
            "Puerta de la taberna": "Una taberna cálida y ruidosa. La puerta está abierta.",
            "Fuente rota": "La fuente está seca. Algo metálico brilla bajo la rejilla.",
            "Barril": "Un viejo barril; alguien dejó un gancho entre las tablas.",
            "Camino al faro": "El sendero sube por el acantilado. La verja está cerrada.",
            "Cartel del puerto": "Puerto Bruma: «Donde la niebla guarda lo que el mar olvida».",
            "Salir a la plaza": "La salida conduce a la plaza del puerto.",
            "Tabernero": "Bruno, tabernero y antiguo farero, pule un vaso detrás de la barra.",
            "Cuerda": "Una cuerda resistente, enrollada junto a la mesa.",
            "Nota de las lentes": "La nota dice: «La luna despierta a la estrella; el sol cierra el ciclo».",
            "Mesa": "Un mapa húmedo del acantilado cubre la mesa.",
            "Volver al puerto": "El camino baja de regreso a Puerto Bruma.",
            "Puerta del faro": "La cerradura tiene forma de llave antigua.",
            "Lente de la luna": "Un disco de vidrio azul con una luna grabada.",
            "Lente de la estrella": "Un disco de vidrio violeta con una estrella grabada.",
            "Lente del sol": "Un disco de vidrio dorado con un sol grabado.",
            "Panel de la baliza": "Tres lentes y un panel de encendido. El orden importa.",
        }
        self._say(descriptions.get(name, "No encuentro nada especial."))

    def _take(self, name):
        if name == "Barril" and self.scene == "plaza":
            if self.inventory.has("Gancho"):
                self._say("Ya tengo el gancho.")
            else:
                self.inventory.add(Item("Gancho", description="Un gancho oxidado pero firme."))
                self._say("Cojo el gancho oxidado.")
        elif name == "Cuerda" and self.scene == "taberna":
            if self.inventory.has("Cuerda"):
                self._say("Ya recogí la cuerda.")
            else:
                self.inventory.add(Item("Cuerda", description="Cuerda de cáñamo, todavía útil."))
                self._say("Guardo la cuerda en el inventario.")
        elif name == "Fuente rota":
            self._say("La llave está bajo la rejilla. Necesito algo para alcanzarla.")
        else:
            self._say("Eso no parece algo que pueda llevarme.")

    def _use(self, name, item):
        if item is None:
            self._say("Primero selecciona un objeto del inventario.")
            return
        if name == "Fuente rota" and item.name == "Gancho con cuerda":
            if not self.fountain_solved:
                self.inventory.remove("Gancho con cuerda")
                self.inventory.add(Item("Llave antigua", description="La llave de hierro del faro."))
                self.fountain_solved = True
                self._say("¡La llave! El gancho y la cuerda alcanzan justo hasta el fondo.")
            else:
                self._say("La fuente ya está vacía.")
        elif name == "Camino al faro" and item.name == "Llave antigua":
            self.gate_unlocked = True
            self._say("La llave gira. La verja del acantilado se abre.")
        elif name == "Puerta del faro" and item.name == "Llave antigua":
            self.gate_unlocked = True
            self._say("La puerta cede con un chirrido y deja entrar al faro.")
        elif name.startswith("Lente de") and item.name == "Llave antigua":
            self._say("No necesito una llave aquí; debo activar las lentes en orden.")
        else:
            self._say("No parece que " + item.name.lower() + " sirva con eso.")

    def _combine_items(self, first, second):
        pair = {first.name, second.name}
        if pair == {"Gancho", "Cuerda"}:
            self.inventory.remove("Gancho")
            self.inventory.remove("Cuerda")
            self.inventory.add(Item("Gancho con cuerda",
                                    description="Una cuerda larga con un gancho firme."))
            self.inventory.select("Gancho con cuerda")
            self._say("Combino la cuerda con el gancho. ¡Alcanza para la fuente!")
        else:
            self._say("No consigo combinar esos objetos.")

    def _open_bartender_dialogue(self):
        self.state = GameState.DIALOGUE
        self.dialogue_choices = [
            ("¿Qué sabes de la baliza?", "baliza"),
            ("¿Recuerdas el orden de las lentes?", "orden"),
            ("¿Puedo ayudar en algo?", "ayuda"),
            ("Me voy.", "salir"),
        ]
        self._say("Bruno: «La niebla vuelve esta noche. ¿Qué quieres saber?»", duration=0)

    def _choose_dialogue(self, choice):
        if choice == "baliza":
            self._say("Bruno: «Sin la baliza, los barcos no ven los arrecifes. Hace falta la llave del faro».",
                      duration=0)
        elif choice == "orden":
            self._say("Bruno: «Mi nota lo recuerda: luna, estrella y al final el sol».", duration=0)
        elif choice == "ayuda":
            if not self.inventory.has("Cuerda"):
                self._say("Bruno: «La cuerda junto a esa mesa ya no me sirve. Llévatela».", duration=0)
            else:
                self._say("Bruno: «El faro depende de ti, marinero».", duration=0)
        else:
            self.state = GameState.IDLE
            self.dialogue.clear_message()
            return
        self.dialogue_choices = [
            ("Volver a preguntar", "volver"),
            ("Terminar conversación", "salir"),
        ]

    def _activate_hotspot(self, name):
        if self.scene == "plaza" and name == "Puerta de la taberna":
            self._set_scene("taberna", starting_position=(160, 430))
        elif self.scene == "plaza" and name == "Camino al faro":
            if not self.gate_unlocked and not self.inventory.has("Llave antigua"):
                self._say("La verja del faro está cerrada. La llave debe estar por la plaza.")
            else:
                if self.inventory.has("Llave antigua"):
                    self.inventory.remove("Llave antigua")
                    self.gate_unlocked = True
                self._set_scene("faro", starting_position=(170, 435))
                self._say("El sendero asciende hasta la vieja torre.")
        elif self.scene == "taberna" and name == "Salir a la plaza":
            self._set_scene("plaza", starting_position=(230, 420))
        elif self.scene == "faro" and name == "Volver al puerto":
            self._set_scene("plaza", starting_position=(830, 425))
        elif self.scene == "faro" and name == "Puerta del faro":
            if not self.gate_unlocked:
                self._say("La puerta del faro está cerrada. La cerradura espera una llave.")
            else:
                self._say("Dentro, las tres lentes esperan el orden correcto.")
        elif self.scene == "faro" and name.startswith("Lente de"):
            self._activate_lens(name)
        elif self.scene == "faro" and name == "Panel de la baliza":
            if self.lens_progress == len(self.lens_order):
                self.state = GameState.WON
                self._say("La baliza se enciende. Un barco responde con una campana entre la niebla.", duration=0)
            else:
                self._say("El panel permanece oscuro. Primero debo ordenar las tres lentes.")

    def _activate_lens(self, name):
        clicked = {
            "Lente de la luna": "luna",
            "Lente de la estrella": "estrella",
            "Lente del sol": "sol",
        }[name]
        expected = self.lens_order[self.lens_progress]
        if clicked == expected:
            self.lens_progress += 1
            if self.lens_progress == len(self.lens_order):
                self._say("Las lentes se alinean. ¡La baliza está lista para encenderse!")
            else:
                self._say("La lente encaja. " + str(len(self.lens_order) - self.lens_progress)
                          + " más en el orden correcto.")
        else:
            self.lens_progress = 0
            self._say("La luz se apaga. El orden vuelve a empezar: luna, estrella, sol.")

    def _interact(self, name, verb, item):
        if (self.scene == "plaza" and name == "Puerta de la taberna") or (
                self.scene == "plaza" and name == "Camino al faro") or (
                self.scene == "taberna" and name == "Salir a la plaza") or (
                self.scene == "faro" and name == "Volver al puerto"):
            if verb == "MIRAR":
                self._look(name)
            elif verb == "USAR":
                if name == "Camino al faro" and item is not None and item.name == "Llave antigua":
                    self.gate_unlocked = True
                    self.inventory.remove("Llave antigua")
                self._activate_hotspot(name)
            else:
                self._say("Para cruzar, selecciona USAR y haz clic en la salida.")
            return
        if self.scene == "faro" and name in (
                "Puerta del faro", "Lente de la luna", "Lente de la estrella",
                "Lente del sol", "Panel de la baliza"):
            if verb == "USAR":
                if name == "Puerta del faro" and item is not None and item.name == "Llave antigua":
                    self.gate_unlocked = True
                    self.inventory.remove("Llave antigua")
                self._activate_hotspot(name)
            elif verb == "MIRAR":
                self._look(name)
            else:
                self._say("Puedo examinarlo o usarlo.")
            return
        if verb == "USAR":
            self._use(name, item)
            return
        if verb == "MIRAR":
            self._look(name)
        elif verb == "COGER":
            self._take(name)
        elif verb == "HABLAR":
            if name == "Tabernero" and self.scene == "taberna":
                self._open_bartender_dialogue()
            else:
                self._say("No hay nadie aquí con quien hablar.")

    def handle_specific_events(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if self.state == GameState.DIALOGUE:
                    self.state = GameState.IDLE
                    self.dialogue.clear_message()
                else:
                    self.running = False
            elif event.key == pygame.K_F1:
                self.debug_hotspots = not self.debug_hotspots
            elif event.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4):
                self.verb = self.VERBS[event.key - pygame.K_1]
            elif event.key == pygame.K_r and self.state == GameState.WON:
                self.__init__()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._handle_click(event.pos)

    def _handle_click(self, position):
        if self.state == GameState.WON:
            self.running = False
            return
        if self.state == GameState.DIALOGUE:
            self._click_dialogue(position)
            return
        if position[1] >= UI_TOP:
            self._click_ui(position)
            return
        for hotspot in self.hotspots[self.scene]:
            if hotspot.contains(position):
                if self.verb == "MIRAR" and self.scene == "plaza" and hotspot.name in (
                        "Puerta de la taberna", "Camino al faro"):
                    self._look(hotspot.name)
                else:
                    self._start_interaction(hotspot)
                return
        self.pending_hotspot = None
        self.target = self._nearest_walkable(position)
        self.state = GameState.WALKING

    def _click_ui(self, position):
        x, y = position
        button_width, button_height = 98, 40
        verbs_origin = (18, UI_TOP + 41)
        for index, verb in enumerate(self.VERBS):
            rect = pygame.Rect(verbs_origin[0] + index * (button_width + 7),
                               verbs_origin[1], button_width, button_height)
            if rect.collidepoint(position):
                self.verb = verb
                return
        slot, gap = 78, 8
        inventory_origin = (475, UI_TOP + 43)
        for index, item in enumerate(self.inventory.items):
            rect = pygame.Rect(inventory_origin[0] + index * (slot + gap),
                               inventory_origin[1], slot, 76)
            if rect.collidepoint(position):
                selected = self.inventory.selected
                if selected is not None and selected is not item and self.verb == "USAR":
                    self._combine_items(selected, item)
                elif selected is item:
                    self.inventory.select("")
                    self.verb = "MIRAR"
                else:
                    self.inventory.select(item.name)
                    self.verb = "USAR"
                return
        if x < 455 and y > UI_TOP + 90:
            self.verb = "MIRAR"

    def _click_dialogue(self, position):
        start_y = 380
        for index, (_, choice) in enumerate(self.dialogue_choices):
            rect = pygame.Rect(310, start_y + index * 34, 630, 30)
            if rect.collidepoint(position):
                self._choose_dialogue(choice)
                if choice == "volver":
                    self._open_bartender_dialogue()
                return

    def update_game_logic(self):
        self.dialogue.update()
        if self.state == GameState.WALKING:
            offset = self.target - self.player
            distance = offset.length()
            if distance <= 4:
                self.player.update(self.target)
                if self.pending_hotspot is not None:
                    self._arrive_at_hotspot()
                else:
                    self.state = GameState.IDLE
            elif distance > 0:
                self.player += offset.normalize() * min(3.4, distance)

    def draw_game_elements(self):
        self.screen.fill(INK)
        if self.scene == "plaza":
            self._draw_plaza()
        elif self.scene == "taberna":
            self._draw_tavern()
        else:
            self._draw_lighthouse()
        self._draw_player()
        self._draw_message()
        self._draw_interface()
        if self.debug_hotspots:
            for hotspot in self.hotspots[self.scene]:
                pygame.draw.rect(self.screen, (255, 255, 0), hotspot.rect, 2)
        if self.state == GameState.DIALOGUE:
            self._draw_dialogue_choices()
        elif self.state == GameState.WON:
            self._draw_win_panel()

    def _draw_plaza(self):
        self._draw_night_sky((12, 21, 59))
        self._draw_far_town()
        pygame.draw.rect(self.screen, (44, 45, 71), (0, 294, SCREEN_WIDTH, 196))
        pygame.draw.polygon(self.screen, (60, 57, 81), [(0, 394), (960, 365), (960, 490), (0, 490)])
        self._draw_cobblestones(0, 375)
        self._draw_building(25, 95, 255, 294, (106, 58, 49), "TABERNA", True)
        self._draw_building(686, 96, 235, 300, (57, 64, 93), "MERCADO", False)
        self._draw_fountain()
        self._draw_barrel(75, 410)
        self._draw_sign(295, 213)
        self._draw_label("PLAZA DEL PUERTO", (24, 18))

    def _draw_tavern(self):
        self._draw_night_sky((16, 20, 48))
        pygame.draw.rect(self.screen, (49, 35, 37), (0, 0, SCREEN_WIDTH, 490))
        pygame.draw.rect(self.screen, (95, 56, 39), (0, 275, SCREEN_WIDTH, 215))
        pygame.draw.rect(self.screen, (56, 34, 30), (50, 65, 860, 330))
        pygame.draw.rect(self.screen, (123, 74, 43), (74, 82, 812, 294))
        pygame.draw.rect(self.screen, (36, 28, 35), (20, 285, 104, 180))
        pygame.draw.rect(self.screen, (151, 102, 60), (30, 294, 83, 171), 5)
        pygame.draw.rect(self.screen, (65, 42, 35), (42, 307, 58, 158))
        pygame.draw.circle(self.screen, GOLD, (89, 388), 4)
        for x in range(88, 885, 40):
            pygame.draw.line(self.screen, (88, 49, 34), (x, 82), (x, 376), 4)
        pygame.draw.rect(self.screen, (43, 29, 28), (105, 115, 680, 84))
        self._draw_text("LA GAVIOTA HUNDIDA", (445, 155), self.large_font, GOLD, centered=True)
        self._draw_bottle(175, 237, (115, 180, 138))
        self._draw_bottle(244, 228, (180, 113, 92))
        self._draw_shelf_and_bar()
        pygame.draw.ellipse(self.screen, (38, 25, 25), (160, 375, 660, 65))
        pygame.draw.polygon(self.screen, (139, 86, 47), [(156, 359), (793, 359), (836, 390), (128, 390)])
        pygame.draw.polygon(self.screen, (190, 124, 69), [(156, 350), (793, 350), (793, 371), (156, 371)])
        self._draw_rope_coil(742, 346)
        self._draw_note(648, 224)
        self._draw_bartender()
        self._draw_cobblestones(0, 410)
        self._draw_label("TABERNA LA GAVIOTA HUNDIDA", (24, 18))

    def _draw_lighthouse(self):
        self._draw_night_sky((8, 19, 54))
        pygame.draw.rect(self.screen, (24, 45, 75), (0, 295, SCREEN_WIDTH, 195))
        for i in range(9):
            wave_y = 345 + i * 19
            pygame.draw.arc(self.screen, (41 + i * 2, 83 + i, 117 + i),
                            (i * 41 - 20, wave_y, 180, 35), math.pi, math.tau, 2)
        pygame.draw.polygon(self.screen, (62, 64, 83),
                            [(0, 408), (140, 350), (270, 375), (430, 325),
                             (610, 380), (805, 333), (960, 394), (960, 490), (0, 490)])
        self._draw_cliff_stones()
        self._draw_lighthouse_tower()
        self._draw_beacon_panel()
        pygame.draw.rect(self.screen, (20, 27, 46), (26, 386, 125, 91))
        pygame.draw.rect(self.screen, (128, 112, 88), (37, 394, 101, 82), 3)
        self._draw_label("FARO DEL ACANTILADO", (24, 18))

    def _draw_night_sky(self, base):
        for y in range(0, WORLD_HEIGHT, 28):
            shade = min(28, y // 18)
            color = (base[0] + shade, base[1] + shade, min(100, base[2] + shade))
            pygame.draw.rect(self.screen, color, (0, y, SCREEN_WIDTH, 28))
        for index in range(66):
            x = (index * 157 + 43) % SCREEN_WIDTH
            y = (index * 71 + 17) % 245
            size = 2 if index % 5 else 3
            pygame.draw.rect(self.screen, (225, 220, 187), (x, y, size, size))
        pygame.draw.circle(self.screen, (243, 218, 151), (816, 69), 27)
        pygame.draw.circle(self.screen, (17, 25, 63), (828, 57), 23)

    def _draw_far_town(self):
        for x, width, height in ((0, 108, 155), (287, 90, 180), (382, 115, 142),
                                 (508, 92, 194), (604, 84, 144), (925, 110, 176)):
            y = 295 - height
            pygame.draw.rect(self.screen, (31, 39, 68), (x, y, width, height))
            pygame.draw.polygon(self.screen, (39, 45, 76), [(x - 8, y + 15),
                                 (x + width // 2, y - 18), (x + width + 8, y + 15)])
            for wx in range(x + 17, x + width - 10, 34):
                pygame.draw.rect(self.screen, (222, 171, 91), (wx, y + 35, 10, 18))

    def _draw_building(self, x, y, width, height, color, sign, tavern):
        pygame.draw.rect(self.screen, (28, 24, 37), (x - 8, y - 8, width + 16, height + 10))
        pygame.draw.rect(self.screen, color, (x, y, width, height))
        pygame.draw.polygon(self.screen, (47, 37, 43),
                            [(x - 14, y + 7), (x + width // 2, y - 54),
                             (x + width + 14, y + 7)])
        pygame.draw.polygon(self.screen, (112, 64, 51),
                            [(x - 10, y + 8), (x + width // 2, y - 37),
                             (x + width + 10, y + 8)], 8)
        for row in range(2):
            for col in range(3):
                wx = x + 22 + col * (width - 45) // 2
                wy = y + 30 + row * 80
                pygame.draw.rect(self.screen, (34, 31, 47), (wx, wy, 42, 54))
                pygame.draw.rect(self.screen, (191, 145, 84), (wx + 5, wy + 6, 32, 42))
                pygame.draw.line(self.screen, (60, 43, 42), (wx + 21, wy + 5), (wx + 21, wy + 48), 3)
                pygame.draw.line(self.screen, (60, 43, 42), (wx + 3, wy + 26), (wx + 39, wy + 26), 3)
            break
        pygame.draw.rect(self.screen, (43, 30, 34), (x + width // 2 - 30, y + 174, 62, 112))
        pygame.draw.rect(self.screen, (133, 86, 54), (x + width // 2 - 24, y + 180, 50, 106), 4)
        pygame.draw.rect(self.screen, (218, 177, 104), (x + width // 2 - 45, y + 66, 90, 40))
        self._draw_text(sign, (x + width // 2, y + 85), self.small_font, INK, centered=True)
        if tavern:
            pygame.draw.rect(self.screen, (244, 190, 90), (x + 28, y + 182, 66, 62))
            pygame.draw.rect(self.screen, (52, 33, 34), (x + 36, y + 190, 50, 46))
            self._draw_text("OPEN", (x + 61, y + 213), self.small_font, (255, 236, 174), centered=True)

    def _draw_fountain(self):
        pygame.draw.ellipse(self.screen, (26, 26, 46), (388, 407, 198, 35))
        pygame.draw.ellipse(self.screen, (102, 113, 137), (390, 335, 190, 95))
        pygame.draw.ellipse(self.screen, (49, 62, 86), (407, 348, 158, 63))
        pygame.draw.ellipse(self.screen, (101, 160, 176), (424, 346, 125, 34))
        pygame.draw.rect(self.screen, (112, 117, 139), (465, 281, 40, 74))
        pygame.draw.ellipse(self.screen, (132, 138, 152), (443, 268, 83, 25))
        pygame.draw.ellipse(self.screen, (102, 111, 135), (451, 256, 67, 19))
        pygame.draw.rect(self.screen, (111, 112, 133), (437, 400, 100, 22))
        pygame.draw.line(self.screen, (163, 171, 176), (461, 299), (493, 320), 3)
        pygame.draw.line(self.screen, (163, 171, 176), (493, 320), (475, 337), 3)
        if not self.fountain_solved:
            pygame.draw.circle(self.screen, (229, 196, 112), (502, 356), 5)

    def _draw_barrel(self, x, y):
        pygame.draw.ellipse(self.screen, (76, 47, 36), (x, y, 54, 54))
        pygame.draw.rect(self.screen, (112, 65, 43), (x + 4, y + 5, 46, 38))
        for offset in (11, 42):
            pygame.draw.line(self.screen, (190, 135, 72), (x + offset, y + 7), (x + offset, y + 45), 3)
        pygame.draw.arc(self.screen, (188, 139, 79), (x + 3, y + 9, 48, 27), 0, math.pi, 3)
        if not self.inventory.has("Gancho") and not self.inventory.has("Gancho con cuerda"):
            pygame.draw.line(self.screen, (206, 192, 158), (x + 23, y - 4), (x + 35, y + 14), 4)
            pygame.draw.arc(self.screen, (206, 192, 158), (x + 29, y - 5, 18, 15), 0, math.pi, 3)

    def _draw_sign(self, x, y):
        pygame.draw.line(self.screen, (80, 54, 39), (x + 23, y + 54), (x + 23, y + 162), 7)
        pygame.draw.rect(self.screen, (142, 96, 59), (x, y, 84, 55))
        pygame.draw.rect(self.screen, (205, 163, 105), (x + 4, y + 4, 76, 47), 2)
        self._draw_text("PUERTO", (x + 42, y + 17), self.small_font, PAPER, centered=True)
        self._draw_text("BRUMA", (x + 42, y + 37), self.small_font, PAPER, centered=True)

    def _draw_shelf_and_bar(self):
        for x in (311, 471, 631, 791):
            pygame.draw.rect(self.screen, (53, 33, 29), (x, 205, 9, 110))
        for y in (211, 261):
            pygame.draw.rect(self.screen, (75, 40, 31), (300, y, 510, 9))
        for x in (338, 392, 480, 543, 647, 713):
            self._draw_bottle(x, 230 + (x % 3) * 10,
                              ((120 + x % 80), (114 + x % 60), (74 + x % 80)))

    def _draw_bottle(self, x, y, color):
        pygame.draw.rect(self.screen, color, (x, y + 12, 23, 36))
        pygame.draw.rect(self.screen, color, (x + 6, y + 3, 11, 13))
        pygame.draw.rect(self.screen, (197, 158, 95), (x + 4, y, 15, 5))
        pygame.draw.rect(self.screen, (229, 190, 113), (x + 5, y + 20, 5, 18))

    def _draw_rope_coil(self, x, y):
        pygame.draw.ellipse(self.screen, (158, 120, 72), (x, y, 54, 30), 5)
        pygame.draw.ellipse(self.screen, (158, 120, 72), (x + 9, y + 5, 36, 19), 4)
        pygame.draw.line(self.screen, (204, 164, 101), (x + 42, y + 20), (x + 58, y + 36), 4)
        if not self.inventory.has("Cuerda") and not self.inventory.has("Gancho con cuerda"):
            pygame.draw.circle(self.screen, (232, 193, 127), (x + 26, y + 15), 2)

    def _draw_note(self, x, y):
        pygame.draw.rect(self.screen, (210, 190, 142), (x, y, 112, 72))
        pygame.draw.rect(self.screen, (139, 106, 68), (x, y, 112, 72), 3)
        for i in range(3):
            pygame.draw.line(self.screen, (107, 83, 59), (x + 14, y + 18 + i * 17),
                             (x + 92, y + 18 + i * 17), 2)
        self._draw_text("LUNA", (x + 52, y + 17), self.small_font, (75, 51, 41), centered=True)
        self._draw_text("ESTRELLA", (x + 52, y + 34), self.small_font, (75, 51, 41), centered=True)
        self._draw_text("SOL", (x + 52, y + 51), self.small_font, (75, 51, 41), centered=True)

    def _draw_bartender(self):
        pygame.draw.ellipse(self.screen, (23, 19, 28), (386, 307, 120, 42))
        pygame.draw.rect(self.screen, (50, 52, 60), (412, 263, 74, 85))
        pygame.draw.rect(self.screen, (218, 164, 117), (422, 226, 53, 53))
        pygame.draw.rect(self.screen, (92, 47, 35), (418, 217, 62, 18))
        pygame.draw.rect(self.screen, (46, 37, 40), (432, 249, 8, 5))
        pygame.draw.rect(self.screen, (46, 37, 40), (457, 249, 8, 5))
        pygame.draw.line(self.screen, (133, 72, 57), (439, 271), (458, 270), 3)
        pygame.draw.rect(self.screen, (209, 190, 147), (405, 282, 87, 20))
        self._draw_text("BRUNO", (446, 321), self.small_font, PAPER, centered=True)

    def _draw_cliff_stones(self):
        for index in range(28):
            x = (index * 127 + 28) % SCREEN_WIDTH
            y = 408 + (index * 43) % 70
            pygame.draw.rect(self.screen, (85 + index % 20, 82 + index % 15, 98 + index % 12),
                             (x, y, 23 + index % 17, 7), border_radius=2)

    def _draw_lighthouse_tower(self):
        pygame.draw.polygon(self.screen, (35, 34, 48),
                            [(327, 318), (350, 135), (498, 135), (525, 318)])
        pygame.draw.polygon(self.screen, (204, 190, 156),
                            [(340, 315), (361, 143), (486, 143), (510, 315)])
        for y in range(180, 310, 42):
            pygame.draw.rect(self.screen, (176, 68, 61), (349, y, 151, 12))
        pygame.draw.rect(self.screen, (44, 37, 45), (345, 122, 164, 24))
        pygame.draw.rect(self.screen, (83, 107, 132), (364, 69, 127, 60))
        pygame.draw.rect(self.screen, (30, 34, 48), (357, 62, 142, 13))
        pygame.draw.polygon(self.screen, (78, 58, 53), [(353, 65), (429, 28), (502, 65)])
        pygame.draw.rect(self.screen, (230, 200, 128), (392, 80, 70, 34))
        if self.lens_progress:
            pygame.draw.polygon(self.screen, (255, 227, 144), [(427, 97), (130, 211), (130, 244)])
            pygame.draw.polygon(self.screen, (255, 220, 148), [(427, 97), (870, 209), (870, 239)])
        pygame.draw.rect(self.screen, (45, 32, 39), (391, 261, 64, 81))
        pygame.draw.rect(self.screen, (153, 111, 70), (395, 267, 56, 75), 3)

    def _draw_beacon_panel(self):
        pygame.draw.rect(self.screen, (46, 43, 52), (646, 212, 282, 130))
        pygame.draw.rect(self.screen, (178, 144, 97), (646, 212, 282, 130), 4)
        lens_colors = [(72, 133, 209), (175, 103, 205), (226, 171, 63)]
        names = ("L", "*", "S")
        for index, x in enumerate((655, 747, 839)):
            color = lens_colors[index] if self.lens_progress > index else (74, 77, 91)
            pygame.draw.rect(self.screen, (28, 28, 39), (x, 230, 78, 82))
            pygame.draw.ellipse(self.screen, color, (x + 14, 238, 50, 50))
            pygame.draw.ellipse(self.screen, (237, 225, 190), (x + 25, 249, 28, 28), 3)
            self._draw_text(names[index], (x + 39, 263), self.large_font, PAPER, centered=True)
            pygame.draw.rect(self.screen, (128, 100, 68), (x + 26, 288, 27, 12))
        if self.lens_progress == len(self.lens_order):
            pygame.draw.circle(self.screen, (255, 235, 142), (786, 197), 15)
            pygame.draw.circle(self.screen, (255, 248, 193), (786, 197), 7)

    def _draw_cobblestones(self, start_y, end_y):
        for row, y in enumerate(range(start_y, end_y, 25)):
            offset = -35 if row % 2 else 0
            for x in range(offset, SCREEN_WIDTH, 70):
                stone = pygame.Rect(x + row % 3 * 4, y, 63, 20)
                pygame.draw.rect(self.screen, (73, 69, 88), stone, border_radius=4)
                pygame.draw.line(self.screen, (97, 91, 107), (stone.x + 8, y + 3),
                                 (stone.right - 9, y + 3), 2)

    def _draw_player(self):
        x, y = int(self.player.x), int(self.player.y)
        pygame.draw.ellipse(self.screen, (23, 21, 35), (x - 23, y - 7, 46, 12))
        pygame.draw.rect(self.screen, (53, 43, 42), (x - 15, y - 52, 12, 29))
        pygame.draw.rect(self.screen, (53, 43, 42), (x + 3, y - 52, 12, 29))
        pygame.draw.rect(self.screen, (120, 73, 48), (x - 17, y - 28, 15, 26))
        pygame.draw.rect(self.screen, (120, 73, 48), (x + 2, y - 28, 15, 26))
        pygame.draw.rect(self.screen, (47, 94, 108), (x - 21, y - 91, 42, 65))
        pygame.draw.rect(self.screen, (228, 215, 174), (x - 20, y - 76, 40, 8))
        pygame.draw.rect(self.screen, (228, 215, 174), (x - 19, y - 53, 38, 7))
        pygame.draw.rect(self.screen, (207, 151, 109), (x - 15, y - 119, 31, 31))
        pygame.draw.rect(self.screen, (66, 43, 36), (x - 18, y - 125, 36, 12))
        pygame.draw.rect(self.screen, (235, 191, 117), (x - 22, y - 124, 44, 6))
        pygame.draw.rect(self.screen, (38, 35, 39), (x + 3, y - 108, 4, 4))
        pygame.draw.rect(self.screen, (125, 72, 58), (x - 10, y - 94, 18, 4))

    def _draw_message(self):
        if self.message and pygame.time.get_ticks() < self.message_timer:
            panel = pygame.Rect(150, 14, 660, 58)
            pygame.draw.rect(self.screen, (17, 20, 35), panel, border_radius=4)
            pygame.draw.rect(self.screen, (180, 143, 91), panel, 2, border_radius=4)
            lines = []
            line = ""
            for word in self.message.split():
                candidate = (line + " " + word).strip()
                if line and self.font.size(candidate)[0] > panel.width - 24:
                    lines.append(line)
                    line = word
                else:
                    line = candidate
            if line:
                lines.append(line)
            lines = lines[:2]
            for index, line in enumerate(lines):
                self._draw_text(line, (panel.centerx, panel.y + 18 + index * 21),
                                self.font, PAPER, centered=True)
        elif self.state == GameState.DIALOGUE and self.dialogue.active_message:
            self.dialogue.draw()

    def _draw_interface(self):
        pygame.draw.rect(self.screen, (23, 22, 32), (0, UI_TOP, SCREEN_WIDTH, SCREEN_HEIGHT - UI_TOP))
        pygame.draw.line(self.screen, GOLD, (0, UI_TOP), (SCREEN_WIDTH, UI_TOP), 3)
        pygame.draw.rect(self.screen, PANEL, (12, UI_TOP + 10, 430, 128))
        pygame.draw.rect(self.screen, GOLD, (12, UI_TOP + 10, 430, 128), 2)
        self._draw_text("ACCIONES", (27, UI_TOP + 25), self.small_font, GOLD)
        button_width, button_height = 98, 40
        for index, verb in enumerate(self.VERBS):
            rect = pygame.Rect(18 + index * 105, UI_TOP + 47, button_width, button_height)
            active = self.verb == verb
            pygame.draw.rect(self.screen, (111, 78, 47) if active else (58, 52, 54), rect)
            pygame.draw.rect(self.screen, GOLD if active else (114, 102, 86), rect, 2)
            self._draw_text(verb, rect.center, self.font, PAPER, centered=True)
        self._draw_text("1-4", (414, UI_TOP + 112), self.small_font, (161, 151, 134), centered=True)
        pygame.draw.rect(self.screen, PANEL, (457, UI_TOP + 10, 490, 128))
        pygame.draw.rect(self.screen, GOLD, (457, UI_TOP + 10, 490, 128), 2)
        self._draw_text("INVENTARIO", (472, UI_TOP + 25), self.small_font, GOLD)
        if self.inventory.selected is not None:
            self._draw_text("Usando: " + self.inventory.selected.name,
                            (931, UI_TOP + 25), self.small_font, PAPER, right=True)
        slot, gap = 78, 8
        for index in range(self.inventory.capacity):
            rect = pygame.Rect(475 + index * (slot + gap), UI_TOP + 47, slot, 76)
            pygame.draw.rect(self.screen, (55, 49, 48), rect)
            pygame.draw.rect(self.screen, GOLD if (
                index < len(self.inventory.items) and
                self.inventory.items[index] is self.inventory.selected
            ) else (117, 100, 75), rect, 2)
            if index < len(self.inventory.items):
                item = self.inventory.items[index]
                self._draw_item_icon(item.name, rect.centerx, rect.y + 26)
                self._draw_text(item.name[:11], (rect.centerx, rect.bottom - 13),
                                self.small_font, PAPER, centered=True)

    def _draw_item_icon(self, name, x, y):
        if name == "Gancho":
            pygame.draw.arc(self.screen, (216, 206, 180), (x - 15, y - 13, 28, 28), 0, math.pi * 1.55, 4)
            pygame.draw.line(self.screen, (216, 206, 180), (x + 7, y + 5), (x + 13, y + 11), 3)
        elif name == "Cuerda":
            pygame.draw.ellipse(self.screen, (185, 137, 74), (x - 19, y - 10, 38, 23), 4)
            pygame.draw.arc(self.screen, (221, 180, 116), (x - 11, y - 6, 22, 15), 0, math.tau, 2)
        elif name == "Gancho con cuerda":
            pygame.draw.line(self.screen, (207, 193, 159), (x - 15, y - 7), (x + 12, y + 8), 3)
            pygame.draw.arc(self.screen, (207, 193, 159), (x + 4, y - 3, 20, 20), 0, math.pi, 3)
        else:
            pygame.draw.rect(self.screen, (168, 157, 126), (x - 6, y - 16, 12, 31))
            pygame.draw.circle(self.screen, (230, 192, 108), (x, y - 17), 7)
            pygame.draw.rect(self.screen, (230, 192, 108), (x + 5, y + 5, 13, 4))

    def _draw_dialogue_choices(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((5, 7, 17, 155))
        self.screen.blit(overlay, (0, 0))
        panel = pygame.Rect(270, 344, 670, 184)
        pygame.draw.rect(self.screen, (34, 30, 37), panel, border_radius=6)
        pygame.draw.rect(self.screen, GOLD, panel, 3, border_radius=6)
        self.dialogue.draw()
        for index, (label, _) in enumerate(self.dialogue_choices):
            rect = pygame.Rect(310, 380 + index * 34, 630, 30)
            pygame.draw.rect(self.screen, (72, 55, 43), rect, border_radius=3)
            self._draw_text("› " + label, (rect.x + 12, rect.centery), self.font, PAPER)

    def _draw_win_panel(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((4, 8, 20, 180))
        self.screen.blit(overlay, (0, 0))
        panel = pygame.Rect(180, 190, 600, 230)
        pygame.draw.rect(self.screen, (35, 32, 42), panel, border_radius=8)
        pygame.draw.rect(self.screen, GOLD, panel, 3, border_radius=8)
        self._draw_text("¡PUERTO BRUMA ESTÁ A SALVO!", (480, 245), self.large_font, GOLD, centered=True)
        self._draw_text("La baliza vuelve a brillar entre la niebla.", (480, 300), self.font, PAPER, centered=True)
        self._draw_text("Clic para salir · Esc para cerrar", (480, 365), self.small_font, PAPER, centered=True)

    def _draw_label(self, text, position):
        self._draw_text(text, position, self.small_font, PAPER)

    def _draw_text(self, text, position, font, color, centered=False, right=False):
        image = font.render(text, True, color)
        if centered:
            rect = image.get_rect(center=position)
        elif right:
            rect = image.get_rect(midright=position)
        else:
            rect = image.get_rect(topleft=position)
        self.screen.blit(image, rect)
