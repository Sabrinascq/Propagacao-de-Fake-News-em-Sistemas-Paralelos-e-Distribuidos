from __future__ import annotations

import argparse

from distribuida_master import WorkerConfig, proxima_geracao_distribuida
from executar_distribuido_local import encerrar_processos, iniciar_workers_locais
from modelo import contar_estados, criar_grade, grades_iguais
from paralela_threads import proxima_geracao_paralela
from sequencial import proxima_geracao_sequencial


def executar_geracoes(grade, funcao, geracoes: int, limiar: int):
    for _ in range(geracoes):
        grade = funcao(grade, limiar)
    return grade


def main() -> None:
    parser = argparse.ArgumentParser(description="Validação de equivalência entre versões")
    parser.add_argument("--linhas", type=int, default=80)
    parser.add_argument("--colunas", type=int, default=80)
    parser.add_argument("--geracoes", type=int, default=25)
    parser.add_argument("--percentual", type=float, default=0.05)
    parser.add_argument("--limiar", type=int, default=3)
    parser.add_argument("--inventores", type=int, default=1)
    parser.add_argument("--threads", type=int, default=4)
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--semente", type=int, default=42)
    args = parser.parse_args()

    inicial = criar_grade(args.linhas, args.colunas, args.percentual, args.semente, args.inventores)

    seq = executar_geracoes(inicial, proxima_geracao_sequencial, args.geracoes, args.limiar)
    par = executar_geracoes(
        inicial,
        lambda grade, limiar: proxima_geracao_paralela(grade, limiar, args.threads),
        args.geracoes,
        args.limiar,
    )

    processos, workers = iniciar_workers_locais(args.workers, 5101)
    try:
        dist = executar_geracoes(
            inicial,
            lambda grade, limiar: proxima_geracao_distribuida(grade, limiar, workers),
            args.geracoes,
            args.limiar,
        )
    finally:
        encerrar_processos(processos)

    print("Sequencial:", contar_estados(seq))
    print("Paralela:  ", contar_estados(par))
    print("Distribuída:", contar_estados(dist))

    assert grades_iguais(seq, par), "paralela diferente da sequencial"
    assert grades_iguais(seq, dist), "distribuída diferente da sequencial"
    print("OK: as três versões produziram exatamente a mesma matriz final.")


if __name__ == "__main__":
    main()
