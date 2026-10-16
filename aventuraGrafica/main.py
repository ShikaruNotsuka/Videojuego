"""Ejecutar desde la raíz del proyecto con: python -m aventuraGrafica.main"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aventuraGrafica.game import AventuraGrafica


if __name__ == "__main__":
    AventuraGrafica().run()
