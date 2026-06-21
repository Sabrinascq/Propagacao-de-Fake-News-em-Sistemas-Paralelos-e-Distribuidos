from __future__ import annotations

import pickle
import socket
import struct
from typing import Any

TAMANHO_CABECALHO = 8


def recv_exato(conexao: socket.socket, quantidade: int) -> bytes:
    dados = bytearray()
    while len(dados) < quantidade:
        pacote = conexao.recv(quantidade - len(dados))
        if not pacote:
            raise ConnectionError("conexão encerrada antes de receber todos os dados")
        dados.extend(pacote)
    return bytes(dados)


def enviar_objeto(conexao: socket.socket, objeto: Any) -> None:
    payload = pickle.dumps(objeto, protocol=pickle.HIGHEST_PROTOCOL)
    cabecalho = struct.pack("!Q", len(payload))
    conexao.sendall(cabecalho + payload)


def receber_objeto(conexao: socket.socket) -> Any:
    cabecalho = recv_exato(conexao, TAMANHO_CABECALHO)
    tamanho = struct.unpack("!Q", cabecalho)[0]
    payload = recv_exato(conexao, tamanho)
    return pickle.loads(payload)
