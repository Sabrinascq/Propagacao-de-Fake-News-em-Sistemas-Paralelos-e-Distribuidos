from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path


def carregar_csv(caminho: Path) -> list[dict]:
    with caminho.open("r", encoding="utf-8") as arquivo:
        return list(csv.DictReader(arquivo))


def gerar_graficos(caminho_csv: Path, pasta_saida: Path) -> None:
    import matplotlib.pyplot as plt

    dados = carregar_csv(caminho_csv)
    pasta_saida.mkdir(parents=True, exist_ok=True)

    for tamanho in sorted({linha["tamanho"] for linha in dados}):
        linhas_tamanho = [linha for linha in dados if linha["tamanho"] == tamanho]
        rotulos = [f"{l['versao']}\n{l['recursos']} rec." for l in linhas_tamanho]
        tempos = [float(l["tempo_medio_s"]) for l in linhas_tamanho]
        speedups = [float(l["speedup"]) for l in linhas_tamanho]
        eficiencias = [float(l["eficiencia"]) for l in linhas_tamanho]

        plt.figure(figsize=(9, 5))
        plt.bar(rotulos, tempos)
        plt.title(f"Tempo médio - {tamanho}")
        plt.ylabel("Tempo médio (s)")
        plt.xticks(rotation=30, ha="right")
        plt.tight_layout()
        plt.savefig(pasta_saida / f"tempo_{tamanho}.png", dpi=160)
        plt.close()

        plt.figure(figsize=(9, 5))
        plt.bar(rotulos, speedups)
        plt.title(f"Speedup - {tamanho}")
        plt.ylabel("Speedup")
        plt.xticks(rotation=30, ha="right")
        plt.tight_layout()
        plt.savefig(pasta_saida / f"speedup_{tamanho}.png", dpi=160)
        plt.close()

        plt.figure(figsize=(9, 5))
        plt.bar(rotulos, eficiencias)
        plt.title(f"Eficiência - {tamanho}")
        plt.ylabel("Eficiência")
        plt.xticks(rotation=30, ha="right")
        plt.tight_layout()
        plt.savefig(pasta_saida / f"eficiencia_{tamanho}.png", dpi=160)
        plt.close()

    print(f"Gráficos gerados em: {pasta_saida}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Gera gráficos a partir do benchmark.csv")
    parser.add_argument("--csv", default="resultados/benchmark.csv")
    parser.add_argument("--saida", default="resultados/graficos")
    args = parser.parse_args()
    gerar_graficos(Path(args.csv), Path(args.saida))


if __name__ == "__main__":
    main()
