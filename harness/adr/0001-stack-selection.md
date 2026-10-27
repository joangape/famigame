# ADR 0001: Selección del Stack Tecnológico para Famigame

- **Fecha**: 2026-10-27
- **Estado**: ACEPTADO
- **Decisores**: Usuario y Asistente
- **Hardware Objetivo Confirmado**: Raspberry Pi 3 / 3B / 3B+ (1GB RAM, Quad-core ARM Cortex-A53)

## Contexto y Restricciones de Hardware

El proyecto consiste en una consola de juegos para fiestas/grupos estilo Jackbox / Mario Party:
1. **Hardware Host**: Raspberry Pi antigua (por ejemplo Raspberry Pi 2 Modelo B, 3B o Pi Zero 2W).
   - CPU: Quad-core ARM Cortex-A7 (Pi 2) o Cortex-A53 (Pi 3) a 0.9-1.2 GHz.
   - RAM: 512 MB a 1 GB.
   - GPU: Broadcom VideoCore IV (soporte OpenGL ES 2.0).
   - Salida de vídeo: HDMI directo a TV o monitor.
2. **Mandos**: Smartphones de los jugadores conectados por Wi-Fi (sin instalar apps, escanean QR y juegan en el navegador).
3. **Dinámica**: Colección de minijuegos 2D sencillos, rápidos y fáciles de entender, controlados con cruceta direccional (D-pad) y 2 botones (A y B).

---

## Opciones Evaluadas

### Opción 1: Python + Pygame-CE (SDL2) + aiohttp/WebSockets *(Recomendada)*

- **Host (Pantalla HDMI)**: Renderizado nativo en Python usando **Pygame-CE** (Community Edition, basado en SDL2 acelerado por hardware).
- **Servidor Web y WebSockets**: Módulo `aiohttp` o `websockets` en Python ejecutándose en hilo/asíncrono paralelo al renderizador.
- **Mando Móvil**: Web ultraligera en HTML5 / CSS3 / Vanilla JavaScript con WebSockets.
- **Ventajas**:
  - **Eficiencia extrema en Raspberry Pi**: Pygame-CE consume apenas ~35-60 MB de RAM.
  - **No requiere entorno de escritorio**: Puede ejecutarse en Raspberry Pi OS Lite directamente contra KMS/DRM (Kernel Mode Setting) o un servidor X mínimo sin navegador pesado.
  - **Cero riesgo de sobrecarga de memoria**: No hay fugas del motor Chromium.
  - **Facilidad para crear minijuegos**: Escribir minijuegos 2D en Python es rápido, legible y muy limpio para prototipar mecánicas.
- **Desventajas**:
  - Dos lenguajes en el repositorio: Python para el juego/host y JavaScript/HTML para el mando web móvil.

---

### Opción 2: Full Web (Node.js + Kiosk Chromium + HTML5 Canvas)

- **Host (Pantalla HDMI)**: Raspberry Pi ejecuta un navegador Chromium en modo Kiosk a pantalla completa apuntando a `http://localhost:3000`. Gráficos 2D en HTML5 Canvas o PixiJS.
- **Servidor**: Node.js con `ws` (WebSockets) y Fastify/Express.
- **Mando Móvil**: HTML5 / CSS3 / Vanilla JS o framework ligero.
- **Ventajas**:
  - Todo el proyecto comparte un único ecosistema (JavaScript / TypeScript).
  - Recarga en caliente (Hot reload) muy cómoda en el navegador durante el desarrollo.
- **Desventajas**:
  - **Muy pesado para una Pi antigua**: Chromium en una Raspberry Pi 2 o 3 consume entre 300 y 550 MB de RAM solo para arrancar.
  - Riesgo de caídas de frames (*jank*) por recolección de basura (Garbage Collection) de V8 en CPUs ARM lentas.
  - Requiere arrancar un entorno gráfico completo X11 o Wayland en la Pi.

---

### Opción 3: Go o Rust + Raylib nativo + WebSockets

- **Host**: Raylib / Ebitengine compilado a binario nativo ARM.
- **Mando**: Web estándar.
- **Ventajas**:
  - Rendimiento insuperable (binario nativo de pocos megabytes, consumo de RAM < 20 MB).
- **Desventajas**:
  - Mayor lentitud y fricción a la hora de codificar nuevos minijuegos rápidamente.
  - Tiempos de compilación cruzada para Raspberry Pi.

---

## Recomendación

Se recomienda la **Opción 1 (Python + Pygame-CE + aiohttp/WebSockets)** por ser el balance óptimo:
1. Rendimiento fluido y garantizado a 60 FPS en hardware antiguo con recursos limitados.
2. Simplicidad para programar minijuegos adictivos en Python.
3. El mando en el móvil sigue siendo 100% web accesible por QR sin fricción.
