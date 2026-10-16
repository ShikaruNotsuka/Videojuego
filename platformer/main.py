# platformer/main.py
"""
Ejecutar desde la carpeta 2027 con:
    python -m platformer.main
o directamente:
    python platformer/main.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from platformer.game import PlatformerGame


def main():
    PlatformerGame().run()


if __name__ == "__main__":
    main()
