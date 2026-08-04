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
    incluidos: list[str] = []
    with zipfile.ZipFile(OUT, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in ROOT.rglob("*"):
            if not path.is_file() or not deve_incluir(path):
                continue
            nome = path.relative_to(ROOT).as_posix()
            zf.write(path, nome)
            incluidos.append(nome)

    obrigatorios = ["bot.py", "requirements.txt", ".env.botcity", "html/login.html", "html/lote-teste.html"]
    faltando = [nome for nome in obrigatorios if nome not in incluidos]
    htmls = [nome for nome in incluidos if nome.startswith("html/") or nome.startswith("web/")]

    print(f"ZIP gerado: {OUT} ({len(incluidos)} arquivos)")
    print(f"Páginas HTML incluídas ({len(htmls)}):")
    for nome in sorted(htmls):
        print(f"  - {nome}")
    if faltando:
        print(f"ATENÇÃO — arquivos obrigatórios ausentes: {faltando}")
    print("Suba este arquivo no Easy Deploy (tecnologia Python). Entry point: bot.py")
    print("WEB_AUTOMATION_URL padrão: html/login.html")


if __name__ == "__main__":
    main()
