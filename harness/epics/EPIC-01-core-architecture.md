# EPIC-01: Core Architecture & Communication Hub

- **Status**: IN_PROGRESS
- **Priority**: P0

## Descripción
Diseñar e implementar el núcleo de la aplicación que se ejecutará en la Raspberry Pi. Este componente actúa como:
1. Servidor HTTP para servir la aplicación web del mando a los smartphones de los jugadores.
2. Servidor WebSocket de muy baja latencia para recibir los inputs de los mandos móviles y transmitir eventos de juego.
3. Orquestador de salas / sesiones (conexión de jugadores, asignación de slots, desconexiones y reconexiones).
4. Bucle principal de juego (Game Loop) desacoplado o sincronizado según la tecnología elegida.

## Criterios de Aceptación
- La Raspberry Pi expone un servidor HTTP y WebSocket accesible en la red local.
- Soporta detección automática de IP local para componer la URL del QR.
- Latencia de recepción de eventos de mando < 20ms en red Wi-Fi local.
- Capacidad para conectar entre 2 y 8 jugadores simultáneos sin degradación.
