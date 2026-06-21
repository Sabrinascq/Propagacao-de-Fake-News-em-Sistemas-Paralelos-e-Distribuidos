# Propagação de Fake News em Sistemas Paralelos e Distribuídos

Projeto em Python para simular a propagação de fake news em uma população representada por uma matriz bidimensional.

Cada célula da matriz representa um indivíduo em um dos estados:

- `0 = IGNORANTE`: ainda não recebeu/acredita na informação;
- `1 = ESPALHADOR`: acredita e compartilha a fake news;
- `2 = INATIVO`: recebeu a informação, mas não compartilha mais;
- `3 = INVENTOR`: cria a fake news e atua como fonte inicial ativa da propagação.

A propagação ocorre em gerações discretas, usando vizinhança de Moore. Um indivíduo ignorante passa a espalhador quando possui pelo menos `limiar_convencimento` vizinhos ativos. Espalhadores comuns e inventores contam como fontes ativas. Um espalhador comum vira inativo na geração seguinte. Um inativo permanece inativo. O inventor permanece inventor, pois representa a origem da fake news.

## O que foi ajustado em relação à versão inicial

1. O código foi reorganizado para evitar duplicação entre as versões.
2. A versão paralela usa `threading.Thread` explicitamente e divide a matriz por faixas de linhas.
3. A versão distribuída usa sockets TCP com arquitetura mestre-workers.
4. A versão distribuída agora envia apenas blocos da matriz com linhas de fronteira, e não a matriz inteira para todos os workers.
5. A comunicação por socket usa cabeçalho de tamanho antes do `pickle`, evitando leitura incompleta de mensagens grandes.
6. Foi incluído script de validação de equivalência entre sequencial, paralela e distribuída.
7. Foi incluído script de benchmark com cálculo de tempo médio, speedup e eficiência.
8. Foi incluído um modelo estendido opcional com 6 melhorias explícitas: inventor, probabilidades diferentes, influenciadores, bots, múltiplas fake news e resistência individual.

## Estrutura dos arquivos

```text
fake_revisado/
├── modelo.py                         # funções comuns, estados, regras e métricas
├── sequencial.py                     # versão sequencial
├── paralela_threads.py               # versão paralela com Threads
├── socket_utils.py                   # protocolo TCP com tamanho de mensagem + pickle
├── distribuida_worker.py             # worker distribuído via socket
├── distribuida_master.py             # master distribuído via socket
├── executar_distribuido_local.py     # demo local com múltiplos processos workers
├── validar_equivalencia.py           # valida igualdade lógica das três versões
├── benchmark.py                      # experimentos e CSV de desempenho
├── gerar_graficos.py                 # gráficos opcionais a partir do CSV
├── modelo_extendido.py               # modelo com 6 melhorias/inovações
├── executar_melhorias.py              # atalho para executar o modelo estendido
├── docs/
│   ├── COMANDOS_DEMO.md
│   ├── ROTEIRO_APRESENTACAO.md
│   └── REFERENCIAS.md
└── resultados/
```

## Requisitos

O projeto principal usa apenas biblioteca padrão do Python.

Versão recomendada:

```bash
python --version
# Python 3.10 ou superior
```

Para gerar gráficos, instale o matplotlib:

```bash
python -m pip install matplotlib
```

## Como executar

### 1. Versão sequencial

```bash
python sequencial.py --linhas 100 --colunas 100 --geracoes 50 --percentual 0.05 --inventores 1 --limiar 3
```

### 2. Versão paralela com Threads

```bash
python paralela_threads.py --linhas 100 --colunas 100 --geracoes 50 --percentual 0.05 --inventores 1 --limiar 3 --threads 4
```

### 3. Versão distribuída em uma máquina, com workers locais

Esse modo é útil para demonstrar na apresentação usando múltiplos processos locais:

```bash
python executar_distribuido_local.py --linhas 100 --colunas 100 --geracoes 50 --percentual 0.05 --inventores 1 --limiar 3 --workers-locais 2
```

### 4. Versão distribuída em terminais separados

Terminal 1:

```bash
python distribuida_worker.py --host 0.0.0.0 --port 5001
```

Terminal 2:

```bash
python distribuida_worker.py --host 0.0.0.0 --port 5002
```

Terminal 3:

```bash
python distribuida_master.py --workers localhost:5001,localhost:5002 --linhas 100 --colunas 100 --geracoes 50 --percentual 0.05 --inventores 1 --limiar 3
```

Para múltiplas máquinas, troque `localhost` pelo IP de cada máquina worker.

## Validação de consistência

Antes de apresentar, rode:

```bash
python validar_equivalencia.py --linhas 80 --colunas 80 --geracoes 25 --threads 4 --workers 2 --inventores 1
```

Resultado esperado:

```text
OK: as três versões produziram exatamente a mesma matriz final.
```

## Benchmark

Exemplo rápido:

```bash
python benchmark.py --tamanhos 100,200,400 --geracoes 50 --inventores 1 --threads 2,4,8 --workers 2,4 --repeticoes 3 --saida resultados/benchmark.csv
```

O CSV terá:

- versão;
- tamanho da matriz;
- número de recursos;
- tempo médio;
- speedup;
- eficiência.

As fórmulas usadas são:

```text
speedup = tempo_sequencial / tempo_paralelo_ou_distribuido
eficiencia = speedup / numero_de_recursos
```

## Gráficos

Depois do benchmark:

```bash
python gerar_graficos.py --csv resultados/benchmark.csv --saida resultados/graficos
```

## Observação importante sobre desempenho em Python

A versão paralela usa Threads porque isso foi exigido no trabalho. Em CPython, tarefas CPU-bound podem ter ganho limitado por causa do GIL. Por isso, é possível que a versão com Threads não seja mais rápida do que a sequencial em alguns cenários. Isso não é erro do algoritmo; é uma limitação relevante para discutir nos slides.

A versão distribuída usa processos separados e sockets, então pode explorar múltiplos núcleos/processos, mas possui custo de comunicação e serialização. Em matrizes pequenas, o overhead pode superar o ganho de paralelismo.

## Melhorias e extensões do modelo original

Além da transformação sequencial -> paralela -> distribuída, foi implementado um módulo estendido com **6 melhorias explícitas**, alinhadas à seção "Melhorias e Extensões" do enunciado. Esse módulo fica em `modelo_extendido.py` e pode ser executado por `executar_melhorias.py`.

| Nº | Melhoria | Como foi implementada |
|---:|---|---|
| 1 | Inventor da fake news | Cada fake news possui uma ou mais células `inventor`, que permanecem ativas e representam a origem da informação falsa. |
| 2 | Probabilidades diferentes de convencimento | Cada fake news recebe uma probabilidade própria de convencer um indivíduo. |
| 3 | Influenciadores digitais | Algumas posições têm peso maior na vizinhança e podem permanecer espalhando por mais tempo. |
| 4 | Bots automatizados | Algumas posições podem criar novos focos de propagação e também tendem a continuar espalhando. |
| 5 | Múltiplas fake news simultâneas | A grade armazena o `fake_id`, permitindo que várias fake news concorram pela mesma população. |
| 6 | Resistência à propagação | Cada indivíduo possui uma resistência individual entre 0 e 1, reduzindo sua probabilidade de convencimento. |

Executar demonstração das 6 melhorias:

```bash
python executar_melhorias.py --linhas 60 --colunas 60 --geracoes 30 --fake-news 3 --inventores-por-fake 1 --influenciadores 20 --bots 12 --exportar-csv resultados/melhorias_demo.csv
```

Também foram implementadas melhorias computacionais no projeto principal:

- Redução de comunicação distribuída: envio de bloco + linhas de fronteira, em vez de matriz completa para cada worker.
- Protocolo robusto de socket: cabeçalho de tamanho + `pickle`.
- Validação automática de equivalência entre versões.
- Benchmark com speedup e eficiência.
- Geração opcional de gráficos.

## Referências

Veja `docs/REFERENCIAS.md`.
