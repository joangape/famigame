# Famigame Project Harness 🎮

Sistema embebido de gestión de tareas, arquitectura y seguimiento del proyecto **Famigame**.

## ¿Qué es el Harness?
El harness es el marco de trabajo y seguimiento integrado en el propio repositorio. Permite a desarrolladores y agentes de IA:
1. Tener visibilidad total del estado de las tareas y epics sin depender de herramientas externas propietarias.
2. Mantener las decisiones de arquitectura (ADRs) junto con el código.
3. Descomponer el proyecto en hitos claros con trazabilidad.

## Estructura de Directorios

```
harness/
├── README.md               # Esta guía
├── harness.py              # CLI para inspeccionar y gestionar el backlog
├── epics/                  # Definición de grandes bloques de funcionalidad
│   ├── EPIC-01-core-architecture.md
│   ├── EPIC-02-mobile-controller.md
│   ├── EPIC-03-host-display-lobby.md
│   └── EPIC-04-minigames-engine.md
├── tasks/                  # Tareas individuales accionables
│   ├── TASK-001-stack-selection-adr.md
│   ├── ...
└── adr/                    # Architecture Decision Records
    └── 0001-stack-selection.md
```

## Convenciones de Tareas y Epics

### Estados de Tarea
- `TODO`: Pendiente de iniciar.
- `IN_PROGRESS`: En desarrollo activo.
- `BLOCKED`: Bloqueada por dependencia o decisión pendiente.
- `DONE`: Completada y verificada.

### Prioridades
- `P0`: Crítico / Bloqueante para la versión mínima jugable.
- `P1`: Importante para la experiencia de juego.
- `P2`: Mejora, pulido o minijuegos adicionales.

## Uso del CLI `harness.py`

El CLI es multiplataforma y no requiere dependencias externas (usa la biblioteca estándar de Python 3):

```bash
# Ver resumen del proyecto, avance y estado general
python3 harness/harness.py status

# Listar todas las tareas
python3 harness/harness.py list

# Filtrar tareas por estado o epic
python3 harness/harness.py list --status TODO
python3 harness/harness.py list --epic EPIC-01

# Ver detalle de una tarea específica
python3 harness/harness.py show TASK-001
```
