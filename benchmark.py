from __future__ import annotations

import argparse
import csv
from pathlib import Path
from statistics import mean
from time import perf_counter

from distribuida_master import proxima_geracao_distribuida
from executar_distribuido_local import encerrar_processos, iniciar_workers_locais
from modelo import ESPALHADOR, ambiente_execucao, contar_estados, criar_grade, existe_potencial_propagacao
from paralela_threads import proxima_geracao_paralela
from sequencial import proxima_geracao_sequencial


def tempo_execucao(funcao, grade_inicial, geracoes: int, limiar: int) -> tuple[float, dict[int, int]]:
    grade = [linha[:] for linha in grade_inicial]
    inicio = perf_counter()
    executadas = 0
    for _ in range(geracoes):
        grade = funcao(grade, limiar)
        executadas += 1
        contagem = contar_estados(grade)
        if contagem[ESPALHADOR] == 0 and not existe_potencial_propagacao(grade, limiar):
            break
    tempo = perf_counter() - inicio
    return tempo, contar_estados(grade)


def benchmark(
    tamanhos: list[int],
    geracoes: int,
    percentual: float,
    limiar: int,
    threads_lista: list[int],
    workers_lista: list[int],
    repeticoes: int,
    saida_csv: Path,
    inventores: int = 1,
) -> None:
    saida_csv.parent.mkdir(parents=True, exist_ok=True)
    linhas_saida: list[dict] = []

    for tamanho in tamanhos:
        grade_inicial = criar_grade(tamanho, tamanho, percentual, semente=42, quantidade_inventores=inventores)

        tempos_seq = []
        for _ in range(repeticoes):
            tempo, contagem = tempo_execucao(proxima_geracao_sequencial, grade_inicial, geracoes, limiar)
            tempos_seq.append(tempo)
        tempo_seq = mean(tempos_seq)

        linhas_saida.append({
            "versao": "sequencial",
            "tamanho": f"{tamanho}x{tamanho}",
            "linhas": tamanho,
            "colunas": tamanho,
            "geracoes": geracoes,
            "percentual": percentual,
            "limiar": limiar,
            "inventores": inventores,
            "recursos": 1,
            "tempo_medio_s": f"{tempo_seq:.6f}",
            "speedup": "1.000000",
            "eficiencia": "1.000000",
        })

        for qtd_threads in threads_lista:
            tempos = []
            for _ in range(repeticoes):
                tempo, _ = tempo_execucao(
                    lambda grade, limiar: proxima_geracao_paralela(grade, limiar, qtd_threads),
                    grade_inicial,
                    geracoes,
                    limiar,
                )
                tempos.append(tempo)
            tempo_medio = mean(tempos)
            speedup = tempo_seq / tempo_medio if tempo_medio > 0 else 0
            eficiencia = speedup / qtd_threads
            linhas_saida.append({
                "versao": "paralela_threads",
                "tamanho": f"{tamanho}x{tamanho}",
                "linhas": tamanho,
                "colunas": tamanho,
                "geracoes": geracoes,
                "percentual": percentual,
                "limiar": limiar,
                "inventores": inventores,
                "recursos": qtd_threads,
                "tempo_medio_s": f"{tempo_medio:.6f}",
                "speedup": f"{speedup:.6f}",
                "eficiencia": f"{eficiencia:.6f}",
            })

        for qtd_workers in workers_lista:
            processos, workers = iniciar_workers_locais(qtd_workers, porta_inicial=5200 + qtd_workers * 10)
            try:
                tempos = []
                for _ in range(repeticoes):
                    tempo, _ = tempo_execucao(
                        lambda grade, limiar: proxima_geracao_distribuida(grade, limiar, workers),
                        grade_inicial,
                        geracoes,
                        limiar,
                    )
                    tempos.append(tempo)
            finally:
                encerrar_processos(processos)

            tempo_medio = mean(tempos)
            speedup = tempo_seq / tempo_medio if tempo_medio > 0 else 0
            eficiencia = speedup / qtd_workers
            linhas_saida.append({
                "versao": "distribuida_sockets_local",
                "tamanho": f"{tamanho}x{tamanho}",
                "linhas": tamanho,
                "colunas": tamanho,
                "geracoes": geracoes,
                "percentual": percentual,
                "limiar": limiar,
                "inventores": inventores,
                "recursos": qtd_workers,
                "tempo_medio_s": f"{tempo_medio:.6f}",
                "speedup": f"{speedup:.6f}",
                "eficiencia": f"{eficiencia:.6f}",
            })

    with saida_csv.open("w", newline="", encoding="utf-8") as arquivo:
        campos = [
            "versao", "tamanho", "linhas", "colunas", "geracoes", "percentual", "limiar", "inventores",
            "recursos", "tempo_medio_s", "speedup", "eficiencia",
        ]
        escritor = csv.DictWriter(arquivo, fieldnames=campos)
        escritor.writeheader()
        escritor.writerows(linhas_saida)

    print(f"Resultados salvos em: {saida_csv}")
    print("Ambiente detectado pelo Python:")
    for chave, valor in ambiente_execucao().items():
        print(f"- {chave}: {valor}")


def parse_lista_int(texto: str) -> list[int]:
    return [int(item.strip()) for item in texto.split(",") if item.strip()]


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark sequencial x threads x sockets")
    parser.add_argument("--tamanhos", default="100,200", help="Tamanhos quadrados separados por vírgula")
    parser.add_argument("--geracoes", type=int, default=50)
    parser.add_argument("--percentual", type=float, default=0.05)
    parser.add_argument("--limiar", type=int, default=3)
    parser.add_argument("--inventores", type=int, default=1)
    parser.add_argument("--threads", default="2,4", help="Quantidade de threads, separadas por vírgula")
    parser.add_argument("--workers", default="2", help="Quantidade de workers locais, separados por vírgula")
    parser.add_argument("--repeticoes", type=int, default=3)
    parser.add_argument("--saida", default="resultados/benchmark.csv")
    args = parser.parse_args()

    benchmark(
        tamanhos=parse_lista_int(args.tamanhos),
        geracoes=args.geracoes,
        percentual=args.percentual,
        limiar=args.limiar,
        threads_lista=parse_lista_int(args.threads),
        workers_lista=parse_lista_int(args.workers),
        repeticoes=args.repeticoes,
        saida_csv=Path(args.saida),
        inventores=args.inventores,
    )


if __name__ == "__main__":
    main()
