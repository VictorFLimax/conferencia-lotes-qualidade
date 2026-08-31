"""
Sistema Desktop Legado Simulado (Tkinter).
"LG - Controle de Estoque Legado v4.2"
Simula cliente Windows GUI sem API para automação desktop de tela.
"""

import argparse
import json
import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

# Dados iniciais de estoque legado
ITENS_ESTOQUE_PADRAO = [
    {"Cod_Item": "LG-DISP-001", "Descricao": "Display OLED 55 polegadas 4K", "Estoque_Fisico": 150, "Status": "ATIVO", "Observacao": "Lote inspecionado sem avarias visiveis"},
    {"Cod_Item": "LG-PLACA-002", "Descricao": "Placa Principal Smart TV", "Estoque_Fisico": 45, "Status": "ATIVO", "Observacao": "Divergencia relatada na contagem fisica do armazem"},
    {"Cod_Item": "LG-FONTE-003", "Descricao": "Fonte Alimentacao Bivolt 120W", "Estoque_Fisico": 200, "Status": "ATIVO", "Observacao": "Fornecedor comunicou atraso no despacho rodoviario"},
    {"Cod_Item": "LG-AUTO-004", "Descricao": "Alto-falante Integrado 20W", "Estoque_Fisico": 80, "Status": "ATIVO", "Observacao": "Item cadastrado com codigo antigo no ERP legado"},
    {"Cod_Item": "LG-CTRL-005", "Descricao": "Controle Remoto Smart Magic", "Estoque_Fisico": 320, "Status": "ATIVO", "Observacao": "Recebido conforme Nota Fiscal"},
    {"Cod_Item": "LG-CABO-006", "Descricao": "Cabo Flat LVDS 50 vias", "Estoque_Fisico": 0, "Status": "BLOQUEADO", "Observacao": "Atraso critico no desembaraço aduaneiro do porto"},
    {"Cod_Item": "LG-SUP-007", "Descricao": "Suporte de Parede VESA", "Estoque_Fisico": 95, "Status": "ATIVO", "Observacao": "Estoque fisico diverge do saldo no WMS"},
]

ARQUIVO_EXPORTACAO_PADRAO = Path("logs/desktop_estoque_exportado.json")


class DesktopAppLegado:
    def __init__(self, root: tk.Tk, auto_export: bool = False, crash_mode: bool = False):
        self.root = root
        self.root.title("LG - Controle de Estoque Legado v4.2")
        self.root.geometry("820x450")
        self.root.configure(bg="#F0F2F5")
        self.crash_mode = crash_mode

        self.itens = list(ITENS_ESTOQUE_PADRAO)
        self._build_ui()

        if self.crash_mode:
            # Simula crash fechando abruptamente após 1.5s
            self.root.after(1500, self._simulate_crash)
        elif auto_export:
            # Exportação automática programada para testes headless/automatizados
            self.root.after(1000, self.exportar_dados)

    def _build_ui(self):
        # Header corporativo
        header = tk.Frame(self.root, bg="#A50034", height=50)
        header.pack(fill=tk.X)
        lbl_title = tk.Label(
            header,
            text="LG Electronics — Sistema de Controle de Estoque (Cliente Windows v4.2)",
            fg="white",
            bg="#A50034",
            font=("Segoe UI", 12, "bold")
        )
        lbl_title.pack(side=tk.LEFT, padx=15, pady=10)

        # Barra de Operações
        toolbar = tk.Frame(self.root, bg="#E1E4E8", padx=10, pady=8)
        toolbar.pack(fill=tk.X)

        tk.Label(toolbar, text="Buscar Item:", bg="#E1E4E8", font=("Segoe UI", 9)).pack(side=tk.LEFT, padx=5)
        self.txt_busca = tk.Entry(toolbar, width=20, font=("Segoe UI", 9))
        self.txt_busca.pack(side=tk.LEFT, padx=5)

        btn_filtrar = tk.Button(toolbar, text="🔍 Filtrar", command=self._filtrar, bg="#005A9E", fg="white", font=("Segoe UI", 9, "bold"))
        btn_filtrar.pack(side=tk.LEFT, padx=5)

        self.btn_exportar = tk.Button(
            toolbar,
            text="📥 Exportar Dados (F6)",
            command=self.exportar_dados,
            bg="#107C41",
            fg="white",
            font=("Segoe UI", 9, "bold")
        )
        self.btn_exportar.pack(side=tk.RIGHT, padx=5)

        btn_crash = tk.Button(
            toolbar,
            text="💥 Simular Crash",
            command=self._simulate_crash,
            bg="#D83B01",
            fg="white",
            font=("Segoe UI", 8)
        )
        btn_crash.pack(side=tk.RIGHT, padx=5)

        # Grid de Itens
        frame_grid = tk.Frame(self.root, padx=10, pady=10)
        frame_grid.pack(fill=tk.BOTH, expand=True)

        cols = ("Cod_Item", "Descricao", "Estoque_Fisico", "Status", "Observacao")
        self.tree = ttk.Treeview(frame_grid, columns=cols, show="headings", height=12)
        
        self.tree.heading("Cod_Item", text="Código")
        self.tree.heading("Descricao", text="Descrição do Material")
        self.tree.heading("Estoque_Fisico", text="Saldo Físico")
        self.tree.heading("Status", text="Status")
        self.tree.heading("Observacao", text="Observação da Linha")

        self.tree.column("Cod_Item", width=110, anchor=tk.W)
        self.tree.column("Descricao", width=220, anchor=tk.W)
        self.tree.column("Estoque_Fisico", width=90, anchor=tk.CENTER)
        self.tree.column("Status", width=90, anchor=tk.CENTER)
        self.tree.column("Observacao", width=280, anchor=tk.W)

        scrollbar = ttk.Scrollbar(frame_grid, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self._popular_grid(self.itens)

        # Status Bar
        self.status_bar = tk.Label(
            self.root,
            text="Pronto | Sessão: DEDICADA | Runner: MONITORADO",
            bd=1,
            relief=tk.SUNKEN,
            anchor=tk.W,
            bg="#F0F2F5",
            font=("Segoe UI", 8)
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def _popular_grid(self, lista):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for row in lista:
            self.tree.insert("", tk.END, values=(
                row["Cod_Item"],
                row["Descricao"],
                row["Estoque_Fisico"],
                row["Status"],
                row["Observacao"]
            ))

    def _filtrar(self):
        termo = self.txt_busca.get().strip().upper()
        if not termo:
            self._popular_grid(self.itens)
            return
        filtrados = [it for it in self.itens if termo in it["Cod_Item"] or termo in it["Descricao"].upper()]
        self._popular_grid(filtrados)

    def exportar_dados(self):
        """Exporta os dados exibidos na tela para arquivo JSON de intercâmbio com o bot."""
        ARQUIVO_EXPORTACAO_PADRAO.parent.mkdir(parents=True, exist_ok=True)
        with open(ARQUIVO_EXPORTACAO_PADRAO, "w", encoding="utf-8") as f:
            json.dump(self.itens, f, indent=2, ensure_ascii=False)
        self.status_bar.config(text=f"Exportação concluída com sucesso! ({len(self.itens)} itens)")
        # Se for exportação automática pelo bot, fecha a janela após salvar
        self.root.after(300, self.root.destroy)

    def _simulate_crash(self):
        """Simula travamento/fechamento inesperado da aplicação."""
        print("[MOCK DESKTOP] CRASH SIMULADO: Encerrando processo inesperadamente com código 1")
        self.root.destroy()
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="LG Estoque Legado Desktop Mock")
    parser.add_argument("--auto-export", action="store_true", help="Dispara exportação automática dos dados")
    parser.add_argument("--crash", action="store_true", help="Simula falha/crash do sistema desktop")
    args = parser.parse_args()

    root = tk.Tk()
    app = DesktopAppLegado(root, auto_export=args.auto_export, crash_mode=args.crash)
    root.mainloop()


if __name__ == "__main__":
    main()
