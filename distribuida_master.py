from __future__ import annotations

import argparse
import socket
import threading
from dataclasses import dataclass

from modelo import (
    Grade,
    adicionar_argumentos_simulacao,
    criar_grade,
    dividir_intervalos,
    executar_loop_simulacao,
)
from socket_utils import enviar_objeto, receber_objeto


@dataclass(frozen=True)
class WorkerConfig:
    host: str
    porta: int


def parse_workers(texto: str) -> list[WorkerConfig]:
    workers: list[WorkerConfig] = []
    for item in texto.split(","):
        item = item.strip()
        if not item:
            continue
        if ":" not in item:
            raise ValueError(f"worker inválido: {item}. Use host:porta")
        host, porta = item.rsplit(":", 1)
        workers.append(WorkerConfig(host, int(porta)))
    if not workers:
        raise ValueError("informe ao menos um worker")
    return workers


def enviar_tarefa(worker: WorkerConfig, tarefa: dict, timeout: float = 120.0) -> list[list[int]]:
    with socket.create_connection((worker.host, worker.porta), timeout=timeout) as conexao:
        enviar_objeto(conexao, tarefa)
        resposta = receber_objeto(conexao)

    if resposta.get("status") != "ok":
        raise RuntimeError(f"erro no worker {worker.host}:{worker.porta}: {resposta}")
    return resposta["linhas"]


def montar_tarefa_bloco(grade: Grade, inicio: int, fim: int, limiar: int) -> dict:
    linhas = len(grade)
    topo = inicio - 1 if inicio > 0 else inicio
    base = fim + 1 if fim < linhas else fim

    bloco = [linha[:] for linha in grade[topo:base]]

    return {
        "tipo": "processar_bloco",
        "bloco": bloco,
        "linhas_reais": fim - inicio,
        "possui_halo_superior": inicio > 0,
        "possui_halo_inferior": fim < linhas,
        "limiar_convencimento": limiar,
        "linha_inicio_global": inicio,
        "linha_fim_global": fim,
    }


def proxima_geracao_distribuida(
    grade: Grade,
    limiar_convencimento: int,
    workers: list[WorkerConfig],
) -> Grade:
    intervalos = dividir_intervalos(len(grade), len(workers))
    resultados: list[list[list[int]] | None] = [None for _ in intervalos]
    erros: list[BaseException] = []
    lock_erros = threading.Lock()

    def thread_envio(indice: int, worker: WorkerConfig, inicio: int, fim: int) -> None:
        try:
            tarefa = montar_tarefa_bloco(grade, inicio, fim, limiar_convencimento)
            resultados[indice] = enviar_tarefa(worker, tarefa)
        except BaseException as exc:
            with lock_erros:
                erros.append(exc)

    threads: list[threading.Thread] = []
    for indice, ((inicio, fim), worker) in enumerate(zip(intervalos, workers)):
        thread = threading.Thread(
            target=thread_envio,
            args=(indice, worker, inicio, fim),
            name=f"envio-worker-{indice}",
        )
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    if erros:
        raise RuntimeError(f"falha no processamento distribuído: {erros[0]}")

    nova_grade: Grade = []
    for bloco_processado in resultados:
        if bloco_processado is None:
            raise RuntimeError("worker não retornou resultado")
        nova_grade.extend(bloco_processado)

    return nova_grade


def executar_simulacao_distribuida(
    linhas: int = 100,
    colunas: int = 100,
    geracoes: int = 50,
    percentual_espalhadores: float = 0.05,
    limiar_convencimento: int = 3,
    workers: list[WorkerConfig] | None = None,
    semente: int = 42,
    quantidade_inventores: int = 1,
    mostrar: bool = True,
):
    if workers is None:
        workers = [WorkerConfig("localhost", 5001)]

    def proxima(grade: Grade, limiar: int) -> Grade:
        return proxima_geracao_distribuida(grade, limiar, workers)

    return executar_loop_simulacao(
        versao=f"distribuida_sockets_{len(workers)}_workers",
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


def testar_workers(workers: list[WorkerConfig]) -> None:
    for worker in workers:
        with socket.create_connection((worker.host, worker.porta), timeout=5.0) as conexao:
            enviar_objeto(conexao, {"tipo": "ping"})
            resposta = receber_objeto(conexao)
        if resposta.get("status") != "ok":
            raise RuntimeError(f"worker sem resposta adequada: {worker}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Master distribuído da simulação de fake news")
    adicionar_argumentos_simulacao(parser)
    parser.add_argument("--workers", default="localhost:5001", help="Lista host:porta separada por vírgula")
    parser.add_argument("--testar-workers", action="store_true")
    args = parser.parse_args()

    workers = parse_workers(args.workers)
    if args.testar_workers:
        testar_workers(workers)
        print("Todos os workers responderam ao ping.")

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


if __name__ == "__main__":
    main()
