from __future__ import annotations

import argparse
import socket
import threading
import traceback
from typing import Sequence

from modelo import ESPALHADOR, IGNORANTE, INATIVO, INVENTOR, Grade, eh_fonte_ativa
from socket_utils import enviar_objeto, receber_objeto


def contar_vizinhos_local(bloco: Sequence[Sequence[int]], i: int, j: int) -> int:
    linhas = len(bloco)
    colunas = len(bloco[0])
    total = 0
    for di in (-1, 0, 1):
        for dj in (-1, 0, 1):
            if di == 0 and dj == 0:
                continue
            ni = i + di
            nj = j + dj
            if 0 <= ni < linhas and 0 <= nj < colunas:
                if eh_fonte_ativa(bloco[ni][nj]):
                    total += 1
    return total


def calcular_estado_local(bloco: Sequence[Sequence[int]], i: int, j: int, limiar: int) -> int:
    estado = bloco[i][j]
    if estado == IGNORANTE:
        return ESPALHADOR if contar_vizinhos_local(bloco, i, j) >= limiar else IGNORANTE
    if estado == ESPALHADOR:
        return INATIVO
    if estado == INVENTOR:
        return INVENTOR
    return INATIVO


def processar_bloco(tarefa: dict) -> Grade:
  
    bloco: Grade = tarefa["bloco"]
    limiar: int = tarefa["limiar_convencimento"]
    linhas_reais: int = tarefa["linhas_reais"]
    possui_halo_superior: bool = tarefa["possui_halo_superior"]

    offset = 1 if possui_halo_superior else 0
    colunas = len(bloco[0])
    resultado: Grade = []

    for linha_real in range(linhas_reais):
        i_local = linha_real + offset
        nova_linha = [0 for _ in range(colunas)]
        for j in range(colunas):
            nova_linha[j] = calcular_estado_local(bloco, i_local, j, limiar)
        resultado.append(nova_linha)

    return resultado


def atender_conexao(conexao: socket.socket, endereco) -> None:
    try:
        with conexao:
            tarefa = receber_objeto(conexao)
            if tarefa.get("tipo") == "ping":
                enviar_objeto(conexao, {"status": "ok"})
                return
            if tarefa.get("tipo") != "processar_bloco":
                enviar_objeto(conexao, {"erro": "tipo de tarefa inválido"})
                return

            resultado = processar_bloco(tarefa)
            enviar_objeto(conexao, {"status": "ok", "linhas": resultado})
    except Exception as exc:  # retorno controlado para facilitar depuração
        try:
            enviar_objeto(conexao, {"status": "erro", "mensagem": str(exc), "traceback": traceback.format_exc()})
        except Exception:
            pass


def iniciar_worker(host: str = "0.0.0.0", porta: int = 5001) -> None:
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    servidor.bind((host, porta))
    servidor.listen(50)
    print(f"[worker] aguardando tarefas em {host}:{porta}")

    try:
        while True:
            conexao, endereco = servidor.accept()
            thread = threading.Thread(target=atender_conexao, args=(conexao, endereco), daemon=True)
            thread.start()
    except KeyboardInterrupt:
        print("\n[worker] encerrado pelo usuário")
    finally:
        servidor.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Worker distribuído da simulação de fake news")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=5001)
    args = parser.parse_args()
    iniciar_worker(args.host, args.port)


if __name__ == "__main__":
    main()
