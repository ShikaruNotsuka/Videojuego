# La baliza olvidada

Aventura gráfica point-and-click hecha dentro de `aventuraGrafica`, usando el
bucle, los hotspots, el inventario y el gestor de diálogos existentes en `engine`.
No requiere imágenes ni cambios al motor.

## Ejecutar

Desde la raíz del proyecto:

```powershell
python -m aventuraGrafica.main
```

## Controles

- Haz clic en el escenario para caminar.
- Selecciona **MIRAR**, **USAR**, **HABLAR** o **COGER** y luego haz clic en un
  objeto o personaje.
- También puedes seleccionar los verbos con las teclas `1` a `4`.
- Con **USAR** activo, selecciona dos objetos del inventario para combinarlos.
- `F1` muestra las áreas de interacción; `Esc` cierra una conversación o el juego.

## Progresión

1. En la plaza, recoge el gancho del barril; en la taberna, recoge la cuerda.
2. Combina ambos objetos y usa el gancho con cuerda en la fuente para recuperar
   la llave antigua.
3. Usa la llave en el camino al faro para abrir la verja.
4. En la taberna, habla con Bruno o examina la nota. En el faro, activa las lentes
   en el orden **luna, estrella, sol** y usa el panel de la baliza.
