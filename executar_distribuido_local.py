from __future__ import annotations

import argparse
import subprocess
import sys
import time
import socket
from pathlib import Path

from distribuida_master import WorkerConfig, executar_simulacao_distribuida
from modelo import adicionar_argumentos_simulacao


def iniciar_workers_locais(quantidade: int, porta_inicial: int) -> tuple[list[subprocess.Popen], list[WorkerConfig]]:
    processos: list[subprocess.Popen] = []
    workers: list[WorkerConfig] = []
    pasta = Path(__file__).resolve().parent

    for indice in range(quantidade):
        porta = porta_inicial + indice
        processo = subprocess.Popen(
            [sys.executable, str(pasta / "distribuida_worker.py"), "--host", "127.0.0.1", "--port", str(porta)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        processos.append(processo)
        workers.append(WorkerConfig("127.0.0.1", porta))

    aguardar_workers(workers, processos)
    return processos, workers


def aguardar_workers(workers: list[WorkerConfig], processos: list[subprocess.Popen], timeout: float = 8.0) -> None:
    limite = time.time() + timeout
    pendentes = set(range(len(workers)))

    while pendentes and time.time() < limite:
        for indice in list(pendentes):
            processo = processos[indice]
            if processo.poll() is not None:
                raise RuntimeError(f"worker {indice} encerrou antes de aceitar conexões")
            worker = workers[indice]
            try:
                with socket.create_connection((worker.host, worker.porta), timeout=0.2):
                    pendentes.remove(indice)
            except OSError:
                pass
        time.sleep(0.1)

    if pendentes:
        portas = ", ".join(str(workers[i].porta) for i in sorted(pendentes))
        raise TimeoutError(f"workers não iniciaram dentro do tempo esperado nas portas: {portas}")


def encerrar_processos(processos: list[subprocess.Popen]) -> None:
    for processo in processos:
        processo.terminate()
    for processo in processos:
        try:
            processo.wait(timeout=3)
        except subprocess.TimeoutExpired:
            processo.kill()


def main() -> None:
    parser = argparse.ArgumentParser(description="Executa a versão distribuída local com múltiplos processos")
    adicionar_argumentos_simulacao(parser)
    parser.add_argument("--workers-locais", type=int, default=2)
    parser.add_argument("--porta-inicial", type=int, default=5001)
    args = parser.parse_args()

    processos, workers = iniciar_workers_locais(args.workers_locais, args.porta_inicial)
    try:
        executar_simulacao_distribuida(
            linhas=args.linhas,
            colunas=args.colunas,
            geracoes=args.geracoes,
            percentual_espalhadores=args.percentual,
            limiar_convencimento=args.limiar,
            workers=workers,
            semente=args.semente,
            quantidade_inventores=args.inventores,
            mostrar=not args.sem_log,
        )
    finally:
        encerrar_processos(processos)


if __name__ == "__main__":
    main()
