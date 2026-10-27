#!/usr/bin/env python3
"""
Famigame Harness CLI
Herramienta embebida para gestionar y visualizar tareas, epics y progreso del proyecto.
Cero dependencias externas (Python 3 standard library).
"""

import os
import re
import sys
import argparse
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
EPICS_DIR = BASE_DIR / "epics"
TASKS_DIR = BASE_DIR / "tasks"
ADR_DIR = BASE_DIR / "adr"

STATUS_COLORS = {
    "DONE": "\033[92m",        # Green
    "IN_PROGRESS": "\033[93m", # Yellow
    "TODO": "\033[94m",        # Blue
    "BLOCKED": "\033[91m",     # Red
}
RESET_COLOR = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"

def parse_markdown_metadata(file_path: Path) -> dict:
    content = file_path.read_text(encoding="utf-8")
    metadata = {
        "file": file_path.name,
        "path": str(file_path),
        "id": file_path.stem.split("-")[0] if "-" in file_path.stem else file_path.stem,
        "title": file_path.stem,
        "status": "TODO",
        "priority": "P1",
        "epic": "UNASSIGNED",
        "raw_content": content,
    }

    # Match first markdown heading as title
    h1_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    if h1_match:
        metadata["title"] = h1_match.group(1).strip()

    # Match frontmatter / key-value lines like: - **Status**: DONE or Status: TODO
    status_match = re.search(r"[-*]?\s*\**Status\**\s*:\s*([A-Z_]+)", content, re.IGNORECASE)
    if status_match:
        metadata["status"] = status_match.group(1).upper()

    priority_match = re.search(r"[-*]?\s*\**Priority\**\s*:\s*(P[0-2])", content, re.IGNORECASE)
    if priority_match:
        metadata["priority"] = priority_match.group(1).upper()

    epic_match = re.search(r"[-*]?\s*\**Epic\**\s*:\s*(EPIC-[0-9]+)", content, re.IGNORECASE)
    if epic_match:
        metadata["epic"] = epic_match.group(1).upper()

    return metadata

def get_all_epics():
    if not EPICS_DIR.exists():
        return []
    epics = []
    for f in sorted(EPICS_DIR.glob("*.md")):
        epics.append(parse_markdown_metadata(f))
    return epics

def get_all_tasks():
    if not TASKS_DIR.exists():
        return []
    tasks = []
    for f in sorted(TASKS_DIR.glob("*.md")):
        tasks.append(parse_markdown_metadata(f))
    return tasks

def format_status(status: str) -> str:
    color = STATUS_COLORS.get(status, "")
    return f"{color}{status:12}{RESET_COLOR}"

def cmd_status(args):
    epics = get_all_epics()
    tasks = get_all_tasks()

    total_tasks = len(tasks)
    done_tasks = sum(1 for t in tasks if t["status"] == "DONE")
    in_progress = sum(1 for t in tasks if t["status"] == "IN_PROGRESS")
    blocked = sum(1 for t in tasks if t["status"] == "BLOCKED")
    todo = sum(1 for t in tasks if t["status"] == "TODO")

    percent = int((done_tasks / total_tasks * 100)) if total_tasks > 0 else 0
    bar_width = 30
    filled = int(bar_width * percent / 100)
    bar = "█" * filled + "░" * (bar_width - filled)

    print(f"\n{BOLD}🎮 FAMIGAME PROJECT DASHBOARD{RESET_COLOR}")
    print("=" * 60)
    print(f"Progreso global: [{bar}] {percent}% ({done_tasks}/{total_tasks} tareas)")
    print(f"Desglose: {STATUS_COLORS['DONE']}● DONE: {done_tasks}{RESET_COLOR} | "
          f"{STATUS_COLORS['IN_PROGRESS']}● IN PROGRESS: {in_progress}{RESET_COLOR} | "
          f"{STATUS_COLORS['TODO']}● TODO: {todo}{RESET_COLOR} | "
          f"{STATUS_COLORS['BLOCKED']}● BLOCKED: {blocked}{RESET_COLOR}\n")

    print(f"{BOLD}EPICS:{RESET_COLOR}")
    for ep in epics:
        match = re.search(r"(EPIC-\d+)", ep["file"])
        ep_id = match.group(1) if match else ep["file"]
        ep_tasks = [t for t in tasks if t.get("epic") == ep_id]
        ep_done = sum(1 for t in ep_tasks if t["status"] == "DONE")
        ep_total = len(ep_tasks)
        ep_pct = int((ep_done / ep_total * 100)) if ep_total > 0 else 0
        print(f"  • {BOLD}{ep_id}{RESET_COLOR} - {ep['title']}")
        print(f"    Progreso: {ep_done}/{ep_total} tareas ({ep_pct}%)")

    print("\n" + "=" * 60)
    print(f"{DIM}Usa 'python3 harness/harness.py list' para ver todas las tareas.{RESET_COLOR}\n")

def cmd_list(args):
    tasks = get_all_tasks()
    if args.status:
        tasks = [t for t in tasks if t["status"] == args.status.upper()]
    if args.epic:
        tasks = [t for t in tasks if t["epic"] == args.epic.upper()]
    if args.priority:
        tasks = [t for t in tasks if t["priority"] == args.priority.upper()]

    print(f"\n{BOLD}TAREAS REGISTRADAS ({len(tasks)}){RESET_COLOR}")
    print("-" * 75)
    print(f"{'ID':<12} {'PRIO':<6} {'STATUS':<14} {'EPIC':<10} {'TÍTULO'}")
    print("-" * 75)
    for t in tasks:
        task_id = t["file"].split(".")[0]
        # Shorten id
        short_id = task_id.split("-")[0] + "-" + task_id.split("-")[1] if len(task_id.split("-")) > 1 else task_id
        print(f"{short_id:<12} {t['priority']:<6} {format_status(t['status'])} {t['epic']:<10} {t['title'][:40]}")
    print("-" * 75 + "\n")

def cmd_show(args):
    target = args.id.lower()
    tasks = get_all_tasks()
    matched = [t for t in tasks if target in t["file"].lower()]
    if not matched:
        epics = get_all_epics()
        matched = [e for e in epics if target in e["file"].lower()]
    if not matched:
        print(f"\n❌ No se encontró tarea ni epic coincidente con: {args.id}\n")
        return

    item = matched[0]
    print("\n" + "=" * 60)
    print(f"{BOLD}{item['title']}{RESET_COLOR}")
    print("=" * 60)
    print(f"Archivo: {item['file']}")
    print(f"Estado:  {format_status(item['status'])}")
    print(f"Prio:    {item['priority']}")
    print(f"Epic:    {item['epic']}")
    print("-" * 60)
    print(item["raw_content"])
    print("=" * 60 + "\n")

def main():
    parser = argparse.ArgumentParser(description="Famigame Harness CLI")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("status", help="Muestra el panel de control y avance")

    list_p = subparsers.add_parser("list", help="Lista las tareas")
    list_p.add_argument("--status", choices=["TODO", "IN_PROGRESS", "DONE", "BLOCKED"], help="Filtrar por estado")
    list_p.add_argument("--epic", help="Filtrar por ID de epic (ej. EPIC-01)")
    list_p.add_argument("--priority", choices=["P0", "P1", "P2"], help="Filtrar por prioridad")

    show_p = subparsers.add_parser("show", help="Muestra el contenido de una tarea o epic")
    show_p.add_argument("id", help="ID de la tarea o epic (ej. TASK-001 o EPIC-01)")

    args = parser.parse_args()
    if not args.command:
        cmd_status(args)
    elif args.command == "status":
        cmd_status(args)
    elif args.command == "list":
        cmd_list(args)
    elif args.command == "show":
        cmd_show(args)

if __name__ == "__main__":
    main()
