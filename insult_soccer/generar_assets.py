"""
insult_soccer/generar_assets.py

Genera los gráficos del juego "fútbol de duelo verbal" (clases 24-25):
campo, dos jugadores, balón, arco y logo. Ejecutar UNA vez:

    python insult_soccer/generar_assets.py
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from herramientas import genlib as g  # noqa: E402

OUT = os.path.join(HERE, "assets", "sprites")

W, H = 800, 600


def make_campo(w=W, h=H):
    """Campo de fútbol vertical: césped a rayas, líneas, círculo y áreas."""
    img = g.new(w, h)
    bg = g.vgrad(w, h, (46, 140, 66), (30, 104, 52))
    img = g.Image.alpha_composite(img, bg)
    d = g.ImageDraw.Draw(img)

    # Rayas de césped
    stripe = h // 8
    for i in range(9):
        if i % 2 == 0:
            d.rectangle([0, i * stripe, w, i * stripe + stripe],
                        fill=(40, 150, 72, 70))

    # Borde
    m = 28
    d.rectangle([m, m, w - m, h - m], outline=(240, 240, 240, 210), width=4)
    # Línea y círculo central
    d.line([(m, h // 2), (w - m, h // 2)], fill=(240, 240, 240, 210), width=4)
    r = 78
    d.ellipse([w // 2 - r, h // 2 - r, w // 2 + r, h // 2 + r],
              outline=(240, 240, 240, 210), width=4)
    d.ellipse([w // 2 - 6, h // 2 - 6, w // 2 + 6, h // 2 + 6],
              fill=(240, 240, 240, 210))

    # Áreas (arriba y abajo)
    aw, ah = 320, 90
    d.rectangle([w // 2 - aw // 2, m, w // 2 + aw // 2, m + ah],
                outline=(240, 240, 240, 210), width=4)
    d.rectangle([w // 2 - aw // 2, h - m - ah, w // 2 + aw // 2, h - m],
                outline=(240, 240, 240, 210), width=4)
    return img


def make_arco(w=190, h=72):
    """Portería con red."""
    img = g.new(w, h)
    d = g.ImageDraw.Draw(img)
    post = (240, 240, 240, 255)
    edge = (110, 110, 120, 255)
    # Red
    for x in range(12, w - 8, 12):
        d.line([(x, 10), (x, h)], fill=(230, 230, 230, 130), width=1)
    for y in range(10, h, 12):
        d.line([(10, y), (w - 10, y)], fill=(230, 230, 230, 130), width=1)
    # Postes y travesaño
    d.rectangle([0, 0, 10, h], fill=post, outline=edge, width=1)
    d.rectangle([w - 10, 0, w, h], fill=post, outline=edge, width=1)
    d.rectangle([0, 0, w, 10], fill=post, outline=edge, width=1)
    return img


def make_balon(r=15):
    img = g.make_ball((250, 250, 250, 255), r)
    d = g.ImageDraw.Draw(img)
    size = r * 2
    # Manchas negras sencillas
    spots = [(0.5, 0.35), (0.32, 0.62), (0.68, 0.62)]
    for fx, fy in spots:
        cx, cy = int(size * fx), int(size * fy)
        pr = max(2, r // 4)
        d.ellipse([cx - pr, cy - pr, cx + pr, cy + pr], fill=(30, 30, 30, 255))
    return img


def make_icono(texto, color):
    """Icono circular con una letra (para el reto)."""
    size = 44
    img = g.new(size, size)
    d = g.ImageDraw.Draw(img)
    d.ellipse([1, 1, size - 2, size - 2], fill=color, outline=(20, 20, 30, 255),
              width=2)
    f = g.font(26)
    box = d.textbbox((0, 0), texto, font=f)
    d.text(((size - (box[2] - box[0])) / 2 - box[0],
            (size - (box[3] - box[1])) / 2 - box[1]), texto, font=f,
           fill=(255, 255, 255, 255))
    return img


def main():
    g.ensure_dir(OUT)

    g.save_png(make_campo(), os.path.join(OUT, "campo.png"))
    g.save_png(make_arco(), os.path.join(OUT, "arco.png"))
    g.save_png(make_balon(), os.path.join(OUT, "balon.png"))

    skin = (232, 194, 158, 255)
    azul = dict(skin=skin, shirt=(50, 110, 235, 255),
                pants=(240, 240, 245, 255), hair=(40, 30, 20, 255))
    rojo = dict(skin=skin, shirt=(220, 55, 55, 255),
                pants=(60, 40, 40, 255), hair=(25, 20, 15, 255))

    g.save_png(g.make_humanoid(74, 108, pose="idle", **azul),
               os.path.join(OUT, "jugador_azul.png"))
    g.save_png(g.make_humanoid(74, 108, pose="idle", **rojo),
               os.path.join(OUT, "jugador_rojo.png"))
    g.save_png(g.make_humanoid(74, 108, pose="kick", **azul),
               os.path.join(OUT, "jugador_azul_kick.png"))
    g.save_png(g.make_humanoid(74, 108, pose="kick", **rojo),
               os.path.join(OUT, "jugador_rojo_kick.png"))

    # Iconos de resultado del duelo verbal
    g.save_png(make_icono("!", (60, 180, 80, 255)),
               os.path.join(OUT, "icono_correcto.png"))
    g.save_png(make_icono("X", (210, 60, 60, 255)),
               os.path.join(OUT, "icono_fallo.png"))

    g.save_png(g.text_image("INSULT SOCCER", 56, (255, 240, 120, 255)),
               os.path.join(OUT, "logo.png"))

    print("Assets de insult_soccer generados en", OUT)


if __name__ == "__main__":
    main()
