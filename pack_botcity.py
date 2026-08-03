"""Gera ZIP pronto para Easy Deploy / BotCity (sem .venv, .git, logs)."""
from __future__ import annotations

import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "dist" / "conferencia-lotes-botcity.zip"

IGNORE_DIRS = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    ".idea",
    ".vscode",
    "logs",
    "dist",
    "agent-transcripts",
    ".cursor",
}
IGNORE_FILES = {".env", ".DS_Store"}
IGNORE_SUFFIX = {".pyc", ".log", ".xlsx", ".zip", ".png"}


def deve_incluir(path: Path) -> bool:
    rel = path.relative_to(ROOT)
    if any(part in IGNORE_DIRS for part in rel.parts):
        return False
    if path.name in IGNORE_FILES:
        return False
    if path.suffix.lower() in IGNORE_SUFFIX:
        return False
    return True


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(OUT, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in ROOT.rglob("*"):
            if not path.is_file() or not deve_incluir(path):
                continue
            zf.write(path, path.relative_to(ROOT).as_posix())
    print(f"ZIP gerado: {OUT}")
    print("Suba este arquivo no Easy Deploy (tecnologia Python). Entry point: bot.py")


if __name__ == "__main__":
    main()
