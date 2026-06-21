from __future__ import annotations

import argparse
import csv
import random
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from typing import Iterable

IGNORANTE = "ignorante"
ESPALHADOR = "espalhador"
INATIVO = "inativo"
INVENTOR = "inventor"


@dataclass(frozen=True)
class Celula:

    tipo: str
    fake_id: int | None = None


GradeExtendida = list[list[Celula]]
MapaResistencia = list[list[float]]
Posicao = tuple[int, int]


@dataclass
class ConfigExtensoes:
    linhas: int = 80
    colunas: int = 80
    geracoes: int = 40
    quantidade_fake_news: int = 3
    inventores_por_fake: int = 1
    percentual_espalhadores: float = 0.03
    limiar_pressao: float = 3.0
    resistencia_media: float = 0.25
    influenciadores: int = 20
    peso_influenciador: float = 2.0
    bots: int = 12
    probabilidade_bot: float = 0.001
    semente: int = 42


@dataclass
class ResultadoExtendido:
    tempo_segundos: float
    historico: list[dict[str, int | float | str]]
    grade_final: GradeExtendida
    probabilidades_fake: dict[int, float]
    influenciadores: set[Posicao]
    bots: set[Posicao]


def criar_probabilidades_fake(quantidade_fake_news: int) -> dict[int, float]:
    if quantidade_fake_news <= 0:
        raise ValueError("quantidade_fake_news deve ser maior que zero")
    probabilidades: dict[int, float] = {}
    for fake_id in range(1, quantidade_fake_news + 1):
        probabilidades[fake_id] = max(0.20, 0.80 - 0.12 * (fake_id - 1))
    return probabilidades


def criar_grade_extendida(config: ConfigExtensoes) -> GradeExtendida:
    validar_config(config)
    rng = random.Random(config.semente)
    grade: GradeExtendida = [
        [Celula(IGNORANTE, None) for _ in range(config.colunas)]
        for _ in range(config.linhas)
    ]

    todas_posicoes = [(i, j) for i in range(config.linhas) for j in range(config.colunas)]
    posicoes_ocupadas: set[Posicao] = set()

    # Melhoria 1: Inventores da fake news. Cada fake news recebe ao menos uma fonte original persistente.
    for fake_id in range(1, config.quantidade_fake_news + 1):
        for _ in range(config.inventores_por_fake):
            posicao = sortear_posicao_livre(rng, todas_posicoes, posicoes_ocupadas)
            posicoes_ocupadas.add(posicao)
            i, j = posicao
            grade[i][j] = Celula(INVENTOR, fake_id)

    total_celulas = config.linhas * config.colunas
    total_espalhadores = int(total_celulas * config.percentual_espalhadores)

    for _ in range(total_espalhadores):
        posicao = sortear_posicao_livre(rng, todas_posicoes, posicoes_ocupadas)
        posicoes_ocupadas.add(posicao)
        i, j = posicao
        fake_id = rng.randint(1, config.quantidade_fake_news)
        grade[i][j] = Celula(ESPALHADOR, fake_id)

    return grade


def sortear_posicao_livre(rng: random.Random, posicoes: list[Posicao], ocupadas: set[Posicao]) -> Posicao:
    while True:
        posicao = rng.choice(posicoes)
        if posicao not in ocupadas:
            return posicao


def validar_config(config: ConfigExtensoes) -> None:
    if config.linhas <= 0 or config.colunas <= 0:
        raise ValueError("linhas e colunas devem ser maiores que zero")
    if config.quantidade_fake_news <= 0:
        raise ValueError("quantidade_fake_news deve ser maior que zero")
    if config.inventores_por_fake < 0:
        raise ValueError("inventores_por_fake não pode ser negativo")
    if not (0 <= config.percentual_espalhadores <= 1):
        raise ValueError("percentual_espalhadores deve estar entre 0 e 1")
    if not (0 <= config.resistencia_media <= 1):
        raise ValueError("resistencia_media deve estar entre 0 e 1")
    if config.influenciadores < 0 or config.bots < 0:
        raise ValueError("influenciadores e bots não podem ser negativos")


def criar_mapa_resistencia(config: ConfigExtensoes) -> MapaResistencia:
    rng = random.Random(config.semente + 101)
    return [
        [
            min(1.0, max(0.0, rng.uniform(config.resistencia_media - 0.20, config.resistencia_media + 0.20)))
            for _ in range(config.colunas)
        ]
        for _ in range(config.linhas)
    ]


def sortear_posicoes(config: ConfigExtensoes, quantidade: int, deslocamento_semente: int) -> set[Posicao]:
    rng = random.Random(config.semente + deslocamento_semente)
    todas = [(i, j) for i in range(config.linhas) for j in range(config.colunas)]
    quantidade = min(quantidade, len(todas))
    return set(rng.sample(todas, quantidade))


def escolher_influenciadores(config: ConfigExtensoes) -> set[Posicao]:
    return sortear_posicoes(config, config.influenciadores, 202)


def escolher_bots(config: ConfigExtensoes) -> set[Posicao]:
    return sortear_posicoes(config, config.bots, 303)


def celula_ativa(celula: Celula) -> bool:
    return celula.tipo in {ESPALHADOR, INVENTOR}


def pressao_por_fake(
    grade: GradeExtendida,
    i: int,
    j: int,
    influenciadores: set[Posicao],
    peso_influenciador: float,
) -> dict[int, float]:
    linhas = len(grade)
    colunas = len(grade[0])
    pressao: dict[int, float] = {}

    for di in (-1, 0, 1):
        for dj in (-1, 0, 1):
            if di == 0 and dj == 0:
                continue
            ni = i + di
            nj = j + dj
            if not (0 <= ni < linhas and 0 <= nj < colunas):
                continue
            vizinho = grade[ni][nj]
            if celula_ativa(vizinho) and vizinho.fake_id is not None:
                peso = peso_influenciador if (ni, nj) in influenciadores else 1.0
                pressao[vizinho.fake_id] = pressao.get(vizinho.fake_id, 0.0) + peso

    return pressao


def escolher_fake_dominante(pressao: dict[int, float]) -> tuple[int | None, float]:
    if not pressao:
        return None, 0.0
    fake_id, valor = max(pressao.items(), key=lambda item: item[1])
    return fake_id, valor


def proxima_geracao_extendida(
    grade: GradeExtendida,
    config: ConfigExtensoes,
    resistencia: MapaResistencia,
    influenciadores: set[Posicao],
    bots: set[Posicao],
    probabilidades_fake: dict[int, float],
    rng: random.Random,
) -> GradeExtendida:
    linhas = len(grade)
    colunas = len(grade[0])
    nova: GradeExtendida = [[Celula(IGNORANTE, None) for _ in range(colunas)] for _ in range(linhas)]

    for i in range(linhas):
        for j in range(colunas):
            atual = grade[i][j]

            if atual.tipo == IGNORANTE:
                pressao = pressao_por_fake(grade, i, j, influenciadores, config.peso_influenciador)
                fake_id, valor_pressao = escolher_fake_dominante(pressao)

                # Melhoria 4: bots podem iniciar propagação mesmo com baixa pressão local. A fake associada ao bot é sorteada.
                if (i, j) in bots and rng.random() < config.probabilidade_bot:
                    fake_bot = rng.randint(1, config.quantidade_fake_news)
                    nova[i][j] = Celula(ESPALHADOR, fake_bot)
                    continue

                if fake_id is None or valor_pressao < config.limiar_pressao:
                    nova[i][j] = Celula(IGNORANTE, None)
                    continue

                # Melhorias 2 e 6: probabilidade por fake news ajustada pela resistência individual da pessoa.
                probabilidade = probabilidades_fake[fake_id] * (1.0 - resistencia[i][j])
                nova[i][j] = Celula(ESPALHADOR, fake_id) if rng.random() < probabilidade else Celula(IGNORANTE, None)

            elif atual.tipo == ESPALHADOR:
                # Melhoria 3: influenciadores e bots tendem a permanecer espalhando por mais tempo que pessoas comuns.
                if (i, j) in bots and rng.random() < 0.90:
                    nova[i][j] = atual
                elif (i, j) in influenciadores and rng.random() < 0.65:
                    nova[i][j] = atual
                else:
                    nova[i][j] = Celula(INATIVO, atual.fake_id)

            elif atual.tipo == INVENTOR:
                # Melhoria 1: inventor é uma fonte persistente.
                nova[i][j] = atual

            else:
                nova[i][j] = Celula(INATIVO, atual.fake_id)

    return nova


def contar_grade_extendida(grade: GradeExtendida, quantidade_fake_news: int) -> dict[str, int]:
    contagem: dict[str, int] = {
        "ignorantes": 0,
        "espalhadores": 0,
        "inativos": 0,
        "inventores": 0,
    }
    for fake_id in range(1, quantidade_fake_news + 1):
        contagem[f"fake_{fake_id}_ativos"] = 0
        contagem[f"fake_{fake_id}_total_alcancado"] = 0

    for linha in grade:
        for celula in linha:
            if celula.tipo == IGNORANTE:
                contagem["ignorantes"] += 1
            elif celula.tipo == ESPALHADOR:
                contagem["espalhadores"] += 1
                if celula.fake_id is not None:
                    contagem[f"fake_{celula.fake_id}_ativos"] += 1
                    contagem[f"fake_{celula.fake_id}_total_alcancado"] += 1
            elif celula.tipo == INVENTOR:
                contagem["inventores"] += 1
                if celula.fake_id is not None:
                    contagem[f"fake_{celula.fake_id}_ativos"] += 1
                    contagem[f"fake_{celula.fake_id}_total_alcancado"] += 1
            else:
                contagem["inativos"] += 1
                if celula.fake_id is not None:
                    contagem[f"fake_{celula.fake_id}_total_alcancado"] += 1
    return contagem


def executar_modelo_extendido(config: ConfigExtensoes, mostrar: bool = True) -> ResultadoExtendido:
    grade = criar_grade_extendida(config)
    resistencia = criar_mapa_resistencia(config)
    influenciadores = escolher_influenciadores(config)
    bots = escolher_bots(config)
    probabilidades_fake = criar_probabilidades_fake(config.quantidade_fake_news)
    rng = random.Random(config.semente + 404)
    historico: list[dict[str, int | float | str]] = []

    if mostrar:
        print("=== MODELO ESTENDIDO COM 6 MELHORIAS ===")
        print("Melhorias: inventor, probabilidades, influenciadores, bots, múltiplas fake news e resistência")
        print(f"Fake news simultâneas: {config.quantidade_fake_news}")
        print(f"Probabilidades por fake: {probabilidades_fake}")
        print(f"Influenciadores: {len(influenciadores)} | Bots: {len(bots)}")
        print()

    inicio = perf_counter()
    for geracao in range(0, config.geracoes + 1):
        contagem = contar_grade_extendida(grade, config.quantidade_fake_news)
        linha_historico: dict[str, int | float | str] = {"geracao": geracao, **contagem}
        historico.append(linha_historico)

        if mostrar:
            ativos_por_fake = " | ".join(
                f"F{fake_id}: {contagem[f'fake_{fake_id}_ativos']} ativos"
                for fake_id in range(1, config.quantidade_fake_news + 1)
            )
            print(
                f"Geração {geracao:03d} | "
                f"Ignorantes: {contagem['ignorantes']:>6} | "
                f"Espalhadores: {contagem['espalhadores']:>6} | "
                f"Inativos: {contagem['inativos']:>6} | "
                f"Inventores: {contagem['inventores']:>4} | {ativos_por_fake}"
            )

        if geracao == config.geracoes:
            break

        grade = proxima_geracao_extendida(
            grade,
            config,
            resistencia,
            influenciadores,
            bots,
            probabilidades_fake,
            rng,
        )

    tempo = perf_counter() - inicio
    if mostrar:
        print(f"\nTempo total: {tempo:.6f}s")

    return ResultadoExtendido(
        tempo_segundos=tempo,
        historico=historico,
        grade_final=grade,
        probabilidades_fake=probabilidades_fake,
        influenciadores=influenciadores,
        bots=bots,
    )


def salvar_historico_extendido(historico: Iterable[dict[str, int | float | str]], caminho: str | Path) -> None:
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    linhas = list(historico)
    if not linhas:
        return
    campos = list(linhas[0].keys())
    with caminho.open("w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=campos)
        escritor.writeheader()
        escritor.writerows(linhas)


def grade_para_texto(grade: GradeExtendida, limite: int = 30) -> str:
    """Gera visualização textual simples da matriz para demonstração."""
    simbolos = {
        IGNORANTE: ".",
        ESPALHADOR: "E",
        INATIVO: "N",
        INVENTOR: "V",
    }
    linhas = min(len(grade), limite)
    colunas = min(len(grade[0]), limite)
    saida = []
    for i in range(linhas):
        saida.append(" ".join(simbolos.get(grade[i][j].tipo, "?") for j in range(colunas)))
    return "\n".join(saida)


def criar_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Modelo estendido com 6 melhorias")
    parser.add_argument("--linhas", type=int, default=80)
    parser.add_argument("--colunas", type=int, default=80)
    parser.add_argument("--geracoes", type=int, default=40)
    parser.add_argument("--fake-news", type=int, default=3, help="Quantidade de fake news simultâneas")
    parser.add_argument("--inventores-por-fake", type=int, default=1)
    parser.add_argument("--percentual", type=float, default=0.03)
    parser.add_argument("--limiar", type=float, default=3.0)
    parser.add_argument("--resistencia-media", type=float, default=0.25)
    parser.add_argument("--influenciadores", type=int, default=20)
    parser.add_argument("--peso-influenciador", type=float, default=2.0)
    parser.add_argument("--bots", type=int, default=12)
    parser.add_argument("--probabilidade-bot", type=float, default=0.001)
    parser.add_argument("--semente", type=int, default=42)
    parser.add_argument("--exportar-csv", default="")
    parser.add_argument("--mostrar-grade", action="store_true")
    return parser


def main() -> None:
    parser = criar_parser()
    args = parser.parse_args()
    config = ConfigExtensoes(
        linhas=args.linhas,
        colunas=args.colunas,
        geracoes=args.geracoes,
        quantidade_fake_news=args.fake_news,
        inventores_por_fake=args.inventores_por_fake,
        percentual_espalhadores=args.percentual,
        limiar_pressao=args.limiar,
        resistencia_media=args.resistencia_media,
        influenciadores=args.influenciadores,
        peso_influenciador=args.peso_influenciador,
        bots=args.bots,
        probabilidade_bot=args.probabilidade_bot,
        semente=args.semente,
    )
    resultado = executar_modelo_extendido(config, mostrar=True)

    if args.exportar_csv:
        salvar_historico_extendido(resultado.historico, args.exportar_csv)
        print(f"Histórico salvo em: {args.exportar_csv}")

    if args.mostrar_grade:
        print("\nVisualização textual da grade final:")
        print(grade_para_texto(resultado.grade_final))


if __name__ == "__main__":
    main()
