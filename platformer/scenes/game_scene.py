# platformer/scenes/game_scene.py
import json
import os

import pygame

from engine.ui import Scene
from engine.camera import Camera
from engine.game_object import GameObject
from platformer.entities import Player, Enemy


class GameScene(Scene):
    def __init__(self, game):
        super().__init__(game)

        level_path = os.path.join(self.game.game_dir, "levels", "level1.json")
        with open(level_path, encoding="utf-8") as level_file:
            level = json.load(level_file)

        self.world_w = level["world_width"]
        self.world_h = level["world_height"]
        self.sprite_groups = {
            "all_sprites": pygame.sprite.Group(),
            "collision_sprites": pygame.sprite.Group(),
            "hazards": pygame.sprite.Group(),
            "enemies": pygame.sprite.Group(),
            "powerups": pygame.sprite.Group(),
            "spawns": [],
        }

        for platform in level["platforms"]:
            sprite = self._make_block(platform)
            self.sprite_groups["all_sprites"].add(sprite)
            if platform["kind"] == "obstacle":
                sprite.mask = pygame.mask.from_surface(sprite.image)
                self.sprite_groups["hazards"].add(sprite)
            else:
                self.sprite_groups["collision_sprites"].add(sprite)

        for decoration in level.get("decorations", []):
            self.sprite_groups["all_sprites"].add(self._make_block(decoration))

        # Jugador
        self.jugador = Player(*level["player_start"])
        self.sprite_groups["all_sprites"].add(self.jugador)

        # Enemigos opcionales del nivel
        self.enemigos = pygame.sprite.Group()
        for spawn in level.get("enemies", []):
            enemigo = Enemy(spawn["x"], spawn["y"])
            self.enemigos.add(enemigo)
            self.sprite_groups["all_sprites"].add(enemigo)

        self.camara = Camera(self.game.screen.get_width(),
                             self.game.screen.get_height(),
                             self.world_w, self.world_h)

    @staticmethod
    def _make_block(block):
        colors = {
            "ground": (112, 76, 45),
            "platform": (80, 145, 170),
            "goal": (245, 210, 75),
        }
        size = (block["width"], block["height"])
        if block["kind"] == "obstacle":
            image = pygame.Surface(size, pygame.SRCALPHA)
            triangle = [(0, size[1] - 1), (size[0] // 2, 0), (size[0] - 1, size[1] - 1)]
            pygame.draw.polygon(image, (205, 65, 55), triangle)
            pygame.draw.polygon(image, (255, 190, 110), triangle, 2)
        else:
            image = pygame.Surface(size)
            image.fill(colors[block["kind"]])

        if block["kind"] == "ground":
            pygame.draw.rect(image, (85, 175, 75), (0, 0, size[0], min(10, size[1])))
        elif block["kind"] == "platform":
            pygame.draw.rect(image, (135, 205, 210), (0, 0, size[0], min(5, size[1])))

        sprite = GameObject(
            block["x"] + size[0] // 2,
            block["y"] + size[1] // 2,
            image,
        )
        return sprite

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.game.change_scene("menu")
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                self.jugador.jump()

    def update(self):
        plataformas = self.sprite_groups["collision_sprites"]
        self.sprite_groups["all_sprites"].update(plataformas=plataformas)
        self.camara.update(self.jugador)

        # Los peligros usan la máscara del triángulo, no su rectángulo exterior.
        if pygame.sprite.spritecollide(
            self.jugador,
            self.sprite_groups["hazards"],
            False,
            pygame.sprite.collide_mask,
        ):
            self.game.change_scene("game_over", win=False)
            return

        # ¿Hemos llegado al final del nivel?
        if self.jugador.rect.right >= self.world_w - 64:
            self.game.change_scene("game_over", win=True)

        # ¿Nos ha tocado un enemigo?
        if pygame.sprite.spritecollide(self.jugador, self.enemigos, False):
            self.game.change_scene("game_over", win=False)

        # ¿Nos hemos caído del mundo?
        if self.jugador.rect.top > self.world_h:
            self.game.change_scene("game_over", win=False)

    def draw(self, surface):
        surface.fill((92, 148, 252))  # cielo
        for sprite in self.sprite_groups["all_sprites"]:
            surface.blit(sprite.image, self.camara.apply(sprite))
