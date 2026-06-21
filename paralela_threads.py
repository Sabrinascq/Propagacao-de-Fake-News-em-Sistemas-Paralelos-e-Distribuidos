
from __future__ import annotations

import argparse
import threading

from modelo import (
    Grade,
    adicionar_argumentos_simulacao,
    calcular_estado_celula,
    dividir_intervalos,
    executar_loop_simulacao,
)


def processar_fatia(
    thread_id: int,
    grade_atual: Grade,
    nova_grade: Grade,
    linha_inicio: int,
    linha_fim: int,
    limiar_convencimento: int,
) -> None:
    colunas = len(grade_atual[0])
    for i in range(linha_inicio, linha_fim):
        for j in range(colunas):
            nova_grade[i][j] = calcular_estado_celula(grade_atual, i, j, limiar_convencimento)


def proxima_geracao_paralela(
    grade: Grade,
    limiar_convencimento: int = 2,
    num_threads: int = 4,
) -> Grade:
    linhas = len(grade)
    colunas = len(grade[0])
    nova_grade = [[0 for _ in range(colunas)] for _ in range(linhas)]

    threads: list[threading.Thread] = []
    intervalos = dividir_intervalos(linhas, num_threads)

    for thread_id, (inicio, fim) in enumerate(intervalos):
        thread = threading.Thread(
            target=processar_fatia,
            args=(thread_id, grade, nova_grade, inicio, fim, limiar_convencimento),
            name=f"worker-thread-{thread_id}",
        )
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    return nova_grade


def executar_simulacao_paralela(
    linhas: int = 100,
    colunas: int = 100,
    geracoes: int = 50,
    percentual_espalhadores: float = 0.05,
    limiar_convencimento: int = 3,
    num_threads: int = 4,
    semente: int = 42,
    quantidade_inventores: int = 1,
    mostrar: bool = True,
):
    def proxima(grade: Grade, limiar: int) -> Grade:
        return proxima_geracao_paralela(grade, limiar, num_threads)

    return executar_loop_simulacao(
        versao=f"paralela_threads_{num_threads}",
        proxima_geracao=proxima,
        linhas=linhas,
        colunas=colunas,
        geracoes=geracoes,
        percentual_espalhadores=percentual_espalhadores,
        limiar_convencimento=limiar_convencimento,
        semente=semente,
        quantidade_inventores=quantidade_inventores,
        mostrar=mostrar,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Simulação paralela com threads")
    adicionar_argumentos_simulacao(parser)
    parser.add_argument("--threads", type=int, default=4)
    args = parser.parse_args()

    executar_simulacao_paralela(
        linhas=args.linhas,
        colunas=args.colunas,
        geracoes=args.geracoes,
        percentual_espalhadores=args.percentual,
        limiar_convencimento=args.limiar,
        num_threads=args.threads,
        semente=args.semente,
        quantidade_inventores=args.inventores,
        mostrar=not args.sem_log,
    )


if __name__ == "__main__":
    main()
