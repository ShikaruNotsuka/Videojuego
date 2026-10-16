# insult_soccer/game.py
"""
INSULT SOCCER — fútbol de duelo verbal (clases 24-25).

Enfoque ESCENAS:
    'menu'  -> elegir jugar
    'match' -> partido por turnos de retos verbales (engine.challenge.Challenge)
               El primero en meter 3 goles gana.
    'final' -> resultado y revancha.

Clase principal: InsultSoccerGame
"""
import os

from engine.game_loop import Game
from engine.asset_manager import AssetManager
from engine.audio import AudioManager
from engine.shared_assets import sfx_path, music_path

from insult_soccer.scenes.menu_scene import MenuScene
from insult_soccer.scenes.match_scene import MatchScene
from insult_soccer.scenes.final_scene import FinalScene


class InsultSoccerGame(Game):
    def __init__(self):
        super().__init__(800, 600, "Insult Soccer", 60)

        self.game_dir = os.path.dirname(os.path.abspath(__file__))
        self.assets_dir = os.path.join(self.game_dir, "assets", "sprites")

        self.assets = AssetManager()
        self.audio = AudioManager()
        self.load_assets()

        # Escenas (clases, no instancias).
        self.add_scene("menu", MenuScene)
        self.add_scene("match", MatchScene)
        self.add_scene("final", FinalScene)
        self.change_scene("menu")

    def load_assets(self):
        """Carga las imágenes generadas y los sonidos compartidos."""
        imagenes = {
            "campo": "campo.png",
            "arco": "arco.png",
            "balon": "balon.png",
            "jugador_azul": "jugador_azul.png",
            "jugador_rojo": "jugador_rojo.png",
            "jugador_azul_kick": "jugador_azul_kick.png",
            "jugador_rojo_kick": "jugador_rojo_kick.png",
            "icono_correcto": "icono_correcto.png",
            "icono_fallo": "icono_fallo.png",
            "logo": "logo.png",
        }
        for nombre, archivo in imagenes.items():
            try:
                self.assets.load_image(nombre, os.path.join(self.assets_dir, archivo))
            except Exception as e:  # pragma: no cover - solo si falta un PNG
                print(f"Aviso: no se pudo cargar '{archivo}': {e}")

        for sonido in ("kick", "cheer", "wrong", "correct", "whistle", "click"):
            self.audio.load_sound(sonido, sfx_path(sonido))
        self.audio.load_music(music_path("soccer"))
