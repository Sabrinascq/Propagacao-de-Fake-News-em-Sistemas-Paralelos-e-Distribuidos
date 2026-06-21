from __future__ import annotations

import argparse
import csv
import platform
import random
import sys
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from typing import Callable, List, Sequence, Tuple

IGNORANTE = 0
ESPALHADOR = 1
INATIVO = 2
INVENTOR = 3

ESTADOS_ATIVOS = {ESPALHADOR, INVENTOR}

Grade = List[List[int]]
Intervalo = Tuple[int, int]


@dataclass
class ResultadoSimulacao:
    versao: str
    linhas: int
    colunas: int
    geracoes_solicitadas: int
    geracoes_executadas: int
    percentual_espalhadores: float
    limiar_convencimento: int
    quantidade_inventores: int
    tempo_segundos: float
    contagem_final: dict[int, int]
    historico: list[dict[str, int]]


def criar_grade(
    linhas: int,
    colunas: int,
    percentual_espalhadores: float = 0.02,
    semente: int = 42,
    quantidade_inventores: int = 1,
) -> Grade:

    validar_parametros(linhas, colunas, percentual_espalhadores, quantidade_inventores)

    rng = random.Random(semente)
    grade = [[IGNORANTE for _ in range(colunas)] for _ in range(linhas)]

    total_celulas = linhas * colunas
    total_espalhadores = int(total_celulas * percentual_espalhadores)

    for _ in range(total_espalhadores):
        i = rng.randint(0, linhas - 1)
        j = rng.randint(0, colunas - 1)
        grade[i][j] = ESPALHADOR

    posicoes_inventores: set[tuple[int, int]] = set()
    while len(posicoes_inventores) < quantidade_inventores:
        i = rng.randint(0, linhas - 1)
        j = rng.randint(0, colunas - 1)
        posicoes_inventores.add((i, j))

    for i, j in posicoes_inventores:
        grade[i][j] = INVENTOR

    return grade


def validar_parametros(
    linhas: int,
    colunas: int,
    percentual_espalhadores: float,
    quantidade_inventores: int = 1,
) -> None:
    if linhas <= 0 or colunas <= 0:
        raise ValueError("linhas e colunas devem ser maiores que zero")
    if not (0 <= percentual_espalhadores <= 1):
        raise ValueError("percentual_espalhadores deve estar entre 0 e 1")
    if quantidade_inventores < 0:
        raise ValueError("quantidade_inventores não pode ser negativa")
    if quantidade_inventores > linhas * colunas:
        raise ValueError("quantidade_inventores não pode ultrapassar o total de células")


def copiar_grade(grade: Grade) -> Grade:
    return [linha[:] for linha in grade]


def eh_fonte_ativa(estado: int) -> bool:
    return estado in ESTADOS_ATIVOS


def contar_vizinhos_espalhadores(grade: Sequence[Sequence[int]], i: int, j: int) -> int:

    linhas = len(grade)
    colunas = len(grade[0])
    total = 0

    for di in (-1, 0, 1):
        for dj in (-1, 0, 1):
            if di == 0 and dj == 0:
                continue

            ni = i + di
            nj = j + dj

            if 0 <= ni < linhas and 0 <= nj < colunas:
                if eh_fonte_ativa(grade[ni][nj]):
                    total += 1

    return total


def calcular_estado_celula(
    grade: Sequence[Sequence[int]],
    i: int,
    j: int,
    limiar_convencimento: int,
) -> int:
    estado_atual = grade[i][j]

    if estado_atual == IGNORANTE:
        vizinhos = contar_vizinhos_espalhadores(grade, i, j)
        return ESPALHADOR if vizinhos >= limiar_convencimento else IGNORANTE

    if estado_atual == ESPALHADOR:
        return INATIVO

    if estado_atual == INVENTOR:
        return INVENTOR

    return INATIVO


def contar_estados(grade: Sequence[Sequence[int]]) -> dict[int, int]:
    contagem = {IGNORANTE: 0, ESPALHADOR: 0, INATIVO: 0, INVENTOR: 0}
    for linha in grade:
        for celula in linha:
            contagem[celula] = contagem.get(celula, 0) + 1
    return contagem


def dividir_intervalos(total_linhas: int, partes: int) -> list[Intervalo]:
    if partes <= 0:
        raise ValueError("partes deve ser maior que zero")

    partes = min(partes, total_linhas)
    base = total_linhas // partes
    resto = total_linhas % partes

    intervalos: list[Intervalo] = []
    inicio = 0
    for parte in range(partes):
        tamanho = base + (1 if parte < resto else 0)
        fim = inicio + tamanho
        intervalos.append((inicio, fim))
        inicio = fim

    return intervalos


def montar_historico_linha(geracao: int, contagem: dict[int, int]) -> dict[str, int]:
    return {
        "geracao": geracao,
        "ignorantes": contagem[IGNORANTE],
        "espalhadores": contagem[ESPALHADOR],
        "inativos": contagem[INATIVO],
        "inventores": contagem[INVENTOR],
    }


def existe_potencial_propagacao(
    grade: Sequence[Sequence[int]],
    limiar_convencimento: int,
) -> bool:
    for i, linha in enumerate(grade):
        for j, estado in enumerate(linha):
            if estado == IGNORANTE and contar_vizinhos_espalhadores(grade, i, j) >= limiar_convencimento:
                return True
    return False


def executar_loop_simulacao(
    versao: str,
    proxima_geracao: Callable[[Grade, int], Grade],
    linhas: int,
    colunas: int,
    geracoes: int,
    percentual_espalhadores: float,
    limiar_convencimento: int,
    semente: int,
    quantidade_inventores: int = 1,
    mostrar: bool = True,
) -> ResultadoSimulacao:
    grade = criar_grade(linhas, colunas, percentual_espalhadores, semente, quantidade_inventores)
    historico: list[dict[str, int]] = []

    if mostrar:
        imprimir_cabecalho(
            versao,
            linhas,
            colunas,
            geracoes,
            percentual_espalhadores,
            limiar_convencimento,
            quantidade_inventores,
        )
        contagem_inicial = contar_estados(grade)
        print(formatar_linha_contagem(0, contagem_inicial))

    inicio = perf_counter()
    geracoes_executadas = 0

    for geracao in range(1, geracoes + 1):
        grade = proxima_geracao(grade, limiar_convencimento)
        geracoes_executadas = geracao
        contagem = contar_estados(grade)
        historico.append(montar_historico_linha(geracao, contagem))

        if mostrar:
            print(formatar_linha_contagem(geracao, contagem))

        if contagem[ESPALHADOR] == 0 and not existe_potencial_propagacao(grade, limiar_convencimento):
            if mostrar:
                print("\nA propagação terminou: não há novos indivíduos que possam ser convencidos.")
            break

    tempo = perf_counter() - inicio
    contagem_final = contar_estados(grade)

    if mostrar:
        imprimir_resultado_final(tempo, contagem_final, linhas * colunas)

    return ResultadoSimulacao(
        versao=versao,
        linhas=linhas,
        colunas=colunas,
        geracoes_solicitadas=geracoes,
        geracoes_executadas=geracoes_executadas,
        percentual_espalhadores=percentual_espalhadores,
        limiar_convencimento=limiar_convencimento,
        quantidade_inventores=quantidade_inventores,
        tempo_segundos=tempo,
        contagem_final=contagem_final,
        historico=historico,
    )


def imprimir_cabecalho(
    versao: str,
    linhas: int,
    colunas: int,
    geracoes: int,
    percentual_espalhadores: float,
    limiar_convencimento: int,
    quantidade_inventores: int,
) -> None:
    print(f"=== SIMULAÇÃO {versao.upper()} DE PROPAGAÇÃO DE FAKE NEWS ===")
    print(f"Tamanho da grade: {linhas} x {colunas} ({linhas * colunas:,} pessoas)")
    print(f"Gerações máximas: {geracoes}")
    print(f"Percentual inicial de espalhadores: {percentual_espalhadores * 100:.2f}%")
    print(f"Inventores iniciais: {quantidade_inventores}")
    print(f"Limiar de convencimento: {limiar_convencimento} vizinhos ativos")
    print()


def formatar_linha_contagem(geracao: int, contagem: dict[int, int]) -> str:
    return (
        f"Geração {geracao:03d} | "
        f"Ignorantes: {contagem[IGNORANTE]:>10,} | "
        f"Espalhadores: {contagem[ESPALHADOR]:>10,} | "
        f"Inativos: {contagem[INATIVO]:>10,} | "
        f"Inventores: {contagem[INVENTOR]:>6,}"
    )


def imprimir_resultado_final(tempo: float, contagem_final: dict[int, int], total: int) -> None:
    print("\n=== RESULTADO FINAL ===")
    print(f"Tempo total de execução: {tempo:.6f} segundos")
    print(f"Ignorantes finais: {contagem_final[IGNORANTE]:,} ({contagem_final[IGNORANTE] / total * 100:.2f}%)")
    print(f"Espalhadores finais: {contagem_final[ESPALHADOR]:,} ({contagem_final[ESPALHADOR] / total * 100:.2f}%)")
    print(f"Inativos finais: {contagem_final[INATIVO]:,} ({contagem_final[INATIVO] / total * 100:.2f}%)")
    print(f"Inventores finais: {contagem_final[INVENTOR]:,} ({contagem_final[INVENTOR] / total * 100:.2f}%)")


def salvar_historico_csv(resultado: ResultadoSimulacao, caminho: str | Path) -> None:
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with caminho.open("w", newline="", encoding="utf-8") as arquivo:
        campos = ["versao", "geracao", "ignorantes", "espalhadores", "inativos", "inventores"]
        escritor = csv.DictWriter(arquivo, fieldnames=campos)
        escritor.writeheader()
        for linha in resultado.historico:
            escritor.writerow({"versao": resultado.versao, **linha})


def grades_iguais(a: Sequence[Sequence[int]], b: Sequence[Sequence[int]]) -> bool:
    return len(a) == len(b) and all(list(la) == list(lb) for la, lb in zip(a, b))


def imprimir_grade(grade: Sequence[Sequence[int]], limite: int = 30) -> None:
    simbolos = {IGNORANTE: ".", ESPALHADOR: "E", INATIVO: "N", INVENTOR: "V"}
    linhas = min(len(grade), limite)
    colunas = min(len(grade[0]), limite)
    for i in range(linhas):
        print(" ".join(simbolos.get(grade[i][j], "?") for j in range(colunas)))
    print()


def adicionar_argumentos_simulacao(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--linhas", type=int, default=100)
    parser.add_argument("--colunas", type=int, default=100)
    parser.add_argument("--geracoes", type=int, default=50)
    parser.add_argument("--percentual", type=float, default=0.05, help="Percentual inicial de espalhadores. Ex.: 0.05 = 5%%")
    parser.add_argument("--inventores", type=int, default=1, help="Quantidade de inventores da fake news na matriz inicial")
    parser.add_argument("--limiar", type=int, default=3, help="Quantidade mínima de vizinhos ativos")
    parser.add_argument("--semente", type=int, default=42)
    parser.add_argument("--sem-log", action="store_true", help="Não imprime estatísticas por geração")


def ambiente_execucao() -> dict[str, str | int]:
    return {
        "sistema_operacional": platform.platform(),
        "processador": platform.processor() or "não identificado pelo Python",
        "python": sys.version.split()[0],
        "implementacao_python": platform.python_implementation(),
    }
