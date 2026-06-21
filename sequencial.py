from __future__ import annotations

import argparse

from modelo import (
    Grade,
    adicionar_argumentos_simulacao,
    calcular_estado_celula,
    executar_loop_simulacao,
)


def proxima_geracao_sequencial(grade: Grade, limiar_convencimento: int = 2) -> Grade:
    linhas = len(grade)
    colunas = len(grade[0])
    nova_grade = [[0 for _ in range(colunas)] for _ in range(linhas)]

    for i in range(linhas):
        for j in range(colunas):
            nova_grade[i][j] = calcular_estado_celula(grade, i, j, limiar_convencimento)

    return nova_grade


def executar_simulacao_sequencial(
    linhas: int = 100,
    colunas: int = 100,
    geracoes: int = 50,
    percentual_espalhadores: float = 0.05,
    limiar_convencimento: int = 3,
    semente: int = 42,
    quantidade_inventores: int = 1,
    mostrar: bool = True,
):
    return executar_loop_simulacao(
        versao="sequencial",
        proxima_geracao=proxima_geracao_sequencial,
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
    parser = argparse.ArgumentParser(description="Simulação sequencial de fake news")
    adicionar_argumentos_simulacao(parser)
    args = parser.parse_args()

    executar_simulacao_sequencial(
        linhas=args.linhas,
        colunas=args.colunas,
        geracoes=args.geracoes,
        percentual_espalhadores=args.percentual,
        limiar_convencimento=args.limiar,
        semente=args.semente,
        quantidade_inventores=args.inventores,
        mostrar=not args.sem_log,
    )


if __name__ == "__main__":
    main()
