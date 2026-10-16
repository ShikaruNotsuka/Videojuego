# insult_soccer/main.py
"""Ejecutar desde la carpeta 2027 con:  python -m insult_soccer.main"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from insult_soccer.game import InsultSoccerGame


def main():
    InsultSoccerGame().run()


if __name__ == "__main__":
    main()
