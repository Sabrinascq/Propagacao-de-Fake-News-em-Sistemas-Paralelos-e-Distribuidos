# Comandos para demonstração na apresentação

## 1. Validar que as versões dão o mesmo resultado

```bash
python validar_equivalencia.py --linhas 80 --colunas 80 --geracoes 25 --threads 4 --workers 2 --inventores 1
```

Mostrar no terminal a mensagem:

```text
OK: as três versões produziram exatamente a mesma matriz final.
```

## 2. Rodar a versão sequencial

```bash
python sequencial.py --linhas 100 --colunas 100 --geracoes 50 --percentual 0.05 --inventores 1 --limiar 3
```

## 3. Rodar a versão paralela

```bash
python paralela_threads.py --linhas 100 --colunas 100 --geracoes 50 --percentual 0.05 --inventores 1 --limiar 3 --threads 4
```

## 4. Rodar a versão distribuída local

```bash
python executar_distribuido_local.py --linhas 100 --colunas 100 --geracoes 50 --percentual 0.05 --inventores 1 --limiar 3 --workers-locais 2
```

## 5. Rodar a versão distribuída com workers em terminais separados

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

## 6. Rodar benchmark

```bash
python benchmark.py --tamanhos 100,200,400 --geracoes 50 --inventores 1 --threads 2,4,8 --workers 2,4 --repeticoes 3 --saida resultados/benchmark.csv
```

## 7. Gerar gráficos

```bash
python -m pip install matplotlib
python gerar_graficos.py --csv resultados/benchmark.csv --saida resultados/graficos
```

## 8. Demonstrar as 6 melhorias do modelo estendido

```bash
python executar_melhorias.py --linhas 60 --colunas 60 --geracoes 30 --fake-news 3 --inventores-por-fake 1 --influenciadores 20 --bots 12 --exportar-csv resultados/melhorias_demo.csv
```

Melhorias demonstradas no terminal:

1. Inventor da fake news;
2. Probabilidades diferentes de convencimento;
3. Influenciadores digitais;
4. Bots automatizados;
5. Múltiplas fake news simultâneas;
6. Resistência individual à propagação.
