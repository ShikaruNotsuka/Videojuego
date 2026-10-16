# platformer/entities.py
import pygame

from engine.game_object import GameObject


class Player(GameObject):
    """Jugador como rectángulo, con gravedad y colisiones contra plataformas."""

    def __init__(self, x, y, scale=(48, 48)):
        image = pygame.Surface(scale)
        image.fill((40, 90, 220))
        super().__init__(x, y, image)

        self.velocidad_mov = 4
        self.fuerza_salto = 16
        self.gravedad = 0.7
        self.pos = pygame.math.Vector2(self.rect.center)
        self.vel = pygame.math.Vector2(0, 0)
        self.en_suelo = False
        self.vidas = 3

    def jump(self):
        """Salta solo cuando el jugador está apoyado en una plataforma."""
        if self.en_suelo:
            self.vel.y = -self.fuerza_salto
            self.en_suelo = False

    def update(self, plataformas=None, *args, **kwargs):
        if plataformas is None:
            plataformas = pygame.sprite.Group()

        self.vel.x = 0
        teclas = pygame.key.get_pressed()
        if teclas[pygame.K_LEFT]:
            self.vel.x = -self.velocidad_mov
        elif teclas[pygame.K_RIGHT]:
            self.vel.x = self.velocidad_mov

        self.vel.y += self.gravedad
        if self.vel.y > 20:
            self.vel.y = 20

        # Movimiento y colisión en X
        self.pos.x += self.vel.x
        self.rect.centerx = round(self.pos.x)
        self._check_collision_x(plataformas)

        # Movimiento y colisión en Y
        self.pos.y += self.vel.y
        self.rect.centery = round(self.pos.y)
        self._check_collision_y(plataformas)

        super().update()

    def _check_collision_x(self, plataformas):
        for plat in pygame.sprite.spritecollide(self, plataformas, False):
            if self.vel.x > 0:
                self.rect.right = plat.rect.left
            elif self.vel.x < 0:
                self.rect.left = plat.rect.right
            self.pos.x = self.rect.centerx

    def _check_collision_y(self, plataformas):
        self.en_suelo = False
        for plat in pygame.sprite.spritecollide(self, plataformas, False):
            if self.vel.y > 0:
                self.rect.bottom = plat.rect.top
                self.en_suelo = True
                self.vel.y = 0
            elif self.vel.y < 0:
                self.rect.top = plat.rect.bottom
                self.vel.y = 0
            self.pos.y = self.rect.centery

    def reset(self, x, y):
        self.pos.update(x, y)
        self.rect.center = (x, y)
        self.vel.update(0, 0)


class Enemy(GameObject):
    """
    Enemigo sencillo que patrulla horizontalmente y cae con la gravedad.
    Si no se le pasa imagen, se genera un cuadrado rojo.
    """

    def __init__(self, x, y, image=None):
        if image is None:
            image = pygame.Surface((24, 24), pygame.SRCALPHA)
            pygame.draw.circle(image, (200, 40, 40), (12, 12), 12)
        super().__init__(x, y, image)

        self.vel_x = 2
        self.vel_y = 0
        self.gravedad = 0.7
        self.pos = pygame.math.Vector2(self.rect.center)
        self.en_suelo = False

    def update(self, plataformas=None, *args, **kwargs):
        if plataformas is None:
            plataformas = pygame.sprite.Group()

        self.vel_y += self.gravedad
        if self.vel_y > 20:
            self.vel_y = 20

        self.pos.x += self.vel_x
        self.rect.centerx = round(self.pos.x)
        for plat in pygame.sprite.spritecollide(self, plataformas, False):
            if self.vel_x > 0:
                self.rect.right = plat.rect.left
            else:
                self.rect.left = plat.rect.right
            self.vel_x *= -1
            self.pos.x = self.rect.centerx

        self.pos.y += self.vel_y
        self.rect.centery = round(self.pos.y)
        self.en_suelo = False
        for plat in pygame.sprite.spritecollide(self, plataformas, False):
            if self.vel_y > 0:
                self.rect.bottom = plat.rect.top
                self.en_suelo = True
                self.vel_y = 0
            elif self.vel_y < 0:
                self.rect.top = plat.rect.bottom
                self.vel_y = 0
            self.pos.y = self.rect.centery

        super().update()
