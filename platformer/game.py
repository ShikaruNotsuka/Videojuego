# platformer/game.py
import os

from engine.game_loop import Game
from engine.asset_manager import AssetManager
from engine.audio import AudioManager
from platformer.scenes.menu_scene import MenuScene
from platformer.scenes.game_scene import GameScene
from platformer.scenes.game_over_scene import GameOverScene


class PlatformerGame(Game):
    """
    Plataformero usando el enfoque de ESCENAS + tilemap + cámara.
    """

    def __init__(self):
        super().__init__(1024, 768, "Plataformero", 60)

        self.game_dir = os.path.dirname(__file__)

        self.assets = AssetManager()
        self.audio = AudioManager()

        self.load_assets()

        self.add_scene("menu", MenuScene)
        self.add_scene("game", GameScene)
        self.add_scene("game_over", GameOverScene)
        self.change_scene("menu")

    def load_assets(self):
        self.audio.load_music(os.path.join(self.game_dir, "assets", "audio", "music.mp3"))
