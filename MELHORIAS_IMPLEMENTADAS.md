# Melhorias e extensões implementadas

O enunciado da atividade indica que melhorias e extensões podem diferenciar o trabalho. Foram implementadas 6 melhorias explícitas no arquivo `modelo_extendido.py`.

| Nº | Melhoria | Justificativa técnica | Onde aparece no código |
|---:|---|---|---|
| 1 | Inventor da fake news | Representa a fonte original da notícia falsa, que permanece ativa e influencia a vizinhança durante toda a simulação. | `Celula(tipo="inventor")`, `criar_grade_extendida`, `proxima_geracao_extendida` |
| 2 | Probabilidades diferentes de convencimento | Simula fake news com diferentes níveis de persuasão. Uma fake mais convincente tem maior chance de transformar ignorantes em espalhadores. | `criar_probabilidades_fake`, `probabilidades_fake[fake_id]` |
| 3 | Influenciadores digitais | Simula perfis com maior alcance/impacto na rede. Eles aumentam a pressão local e podem continuar espalhando por mais gerações. | `escolher_influenciadores`, `pressao_por_fake`, `peso_influenciador` |
| 4 | Bots automatizados | Simula contas artificiais que podem criar novos focos de disseminação e permanecer espalhando. | `escolher_bots`, `probabilidade_bot`, tratamento de bots em `proxima_geracao_extendida` |
| 5 | Múltiplas fake news simultâneas | Permite competição entre diferentes fake news na mesma população. Cada célula carrega um `fake_id`. | `Celula.fake_id`, `quantidade_fake_news`, `pressao_por_fake` |
| 6 | Resistência à propagação | Simula indivíduos com diferentes níveis de ceticismo/alfabetização midiática, reduzindo a probabilidade de convencimento. | `criar_mapa_resistencia`, `probabilidade * (1 - resistencia[i][j])` |

## Comando de execução

```bash
python executar_melhorias.py --linhas 60 --colunas 60 --geracoes 30 --fake-news 3 --inventores-por-fake 1 --influenciadores 20 --bots 12 --exportar-csv resultados/melhorias_demo.csv
```

## Observação importante

O modelo estendido altera as regras originais, portanto ele é usado como demonstração de inovação. A comparação de desempenho entre sequencial, paralela e distribuída continua usando o modelo principal, para preservar a equivalência lógica entre as três versões.
