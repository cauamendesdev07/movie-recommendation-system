# Sistema de Recomendação de Filmes

Projeto acadêmico de Ciência de Dados que implementa um sistema de recomendação de filmes utilizando **Python**, **Neo4j** e a base de avaliações **MovieLens Latest Small**.

## 1. Objetivo

Desenvolver um sistema de recomendação colaborativa baseado na similaridade entre filmes, utilizando as avaliações de usuários para estimar notas de filmes ainda não avaliados e gerar recomendações personalizadas.

## 2. Tecnologias utilizadas

- **Python:** processamento dos dados, cálculo de similaridades, recomendação e avaliação.
- **Neo4j:** armazenamento e consulta do grafo de filmes, usuários e avaliações.
- **Cypher:** linguagem de consulta do banco de grafos.
- **MovieLens Latest Small:** conjunto de dados utilizado no projeto.

## 3. Base de dados

O projeto utiliza os arquivos `movies.csv` e `ratings.csv`.

| Informação | Quantidade |
|---|---:|
| Filmes | 9.742 |
| Usuários | 610 |
| Avaliações | 100.836 |
| Avaliações para treino | 80.668 |
| Avaliações para teste | 20.168 |
| Relações de similaridade calculadas | 483.197 |

## 4. Modelo do grafo

O banco utiliza os seguintes elementos:

- `(:User)`: representa um usuário.
- `(:Movie)`: representa um filme, com identificador, título e gêneros.
- `[:RATED]`: relaciona usuários aos filmes avaliados, armazenando nota e data.
- `[:RATED_TRAIN]`: armazena as avaliações utilizadas no treinamento e na geração das recomendações.
- `[:SIMILAR_TO]`: relaciona filmes semelhantes, armazenando a similaridade de Pearson e a quantidade de usuários em comum.

Representação simplificada:

```text
(User)-[:RATED]->(Movie)
(User)-[:RATED_TRAIN]->(Movie)
(Movie)-[:SIMILAR_TO]->(Movie)
```

Restrições de unicidade são utilizadas nos identificadores de usuários e filmes.

## 5. Algoritmo de recomendação

### 5.1. Divisão dos dados

As avaliações são separadas em conjuntos de treinamento e teste, na proporção aproximada de 80% e 20%. O conjunto de treinamento é utilizado para calcular as similaridades e gerar as recomendações.

### 5.2. Similaridade de Pearson

A similaridade entre dois filmes é calculada a partir das avaliações dos usuários que avaliaram ambos. O cálculo utiliza o coeficiente de correlação de Pearson.

Para reduzir o efeito de amostras muito pequenas, são considerados pares com pelo menos cinco usuários em comum. Na implementação atual, somente similaridades positivas são armazenadas.

### 5.3. Previsão de notas

A nota prevista para um filme ainda não avaliado pelo usuário é calculada pela média ponderada das notas dos filmes semelhantes:

\[
\hat r_{u,i} =
\frac{\sum_{j \in N(i)} sim(i,j)\,r_{u,j}}
{\sum_{j \in N(i)} |sim(i,j)|}
\]

Onde:

- \(\hat r_{u,i}\): nota prevista para o filme \(i\) pelo usuário \(u\).
- \(sim(i,j)\): similaridade entre os filmes \(i\) e \(j\).
- \(r_{u,j}\): nota dada pelo usuário \(u\) ao filme \(j\).
- \(N(i)\): conjunto de vizinhos considerados para a previsão.

A implementação considera até 20 vizinhos por candidato e exige pelo menos cinco vizinhos para gerar uma recomendação.

### 5.4. Geração das recomendações

O sistema identifica filmes ainda não avaliados pelo usuário, calcula as notas previstas e retorna os candidatos com as maiores previsões.

## 6. Avaliação

A avaliação utiliza os filmes do conjunto de teste com nota igual ou superior a 4,0 como relevantes.

As métricas implementadas são:

- **Precision@10:** proporção das dez recomendações que são relevantes.
- **Recall@10:** proporção dos filmes relevantes do teste que aparecem entre as recomendações.

Em um teste inicial com os usuários de IDs 1 a 20, após a aplicação do filtro de pelo menos cinco vizinhos, os resultados foram:

| Métrica | Resultado |
|---|---:|
| Precision@10 média | 0,0050 |
| Recall@10 médio | 0,0010 |

Esses resultados indicam desempenho baixo nesse teste inicial e devem ser interpretados como uma limitação da implementação atual. A avaliação foi realizada em uma amostra de 20 usuários, não em todos os usuários da base.

## 7. Estrutura do projeto

```text
projeto/
├── movies.csv
├── ratings.csv
├── README.md
├── test_connection.py
├── src/
│   ├── import_data.py
│   ├── graph_queries.py
│   ├── recommender.py
│   └── evaluate.py
└── docs/
```

## 8. Instalação e execução

### Pré-requisitos

- Python instalado.
- Neo4j Desktop ou outra instância Neo4j acessível.
- Base MovieLens Latest Small baixada.
- Driver Python do Neo4j instalado.

Instale a dependência:

```bash
py -m pip install neo4j
```

Configure a conexão com o banco em `src/graph_queries.py`, utilizando a URI, o usuário e a senha da sua instância Neo4j.

### Importação dos dados

Com o banco Neo4j iniciado e os arquivos CSV disponíveis na raiz do projeto, execute:

```bash
py -m src.import_data
```

Não execute novamente a importação se os dados já estiverem carregados e corretos.

### Geração das recomendações

Para consultar recomendações para o usuário de ID 1:

```bash
py -c "from src.recommender import recommend_movies; [print(x) for x in recommend_movies(1, limit=10)]"
```

### Avaliação

Para executar a avaliação inicial nos usuários de ID 1 a 20:

```bash
py -c "from src.evaluate import split_ratings, evaluate_multiple_users; treino, teste = split_ratings(); evaluate_multiple_users(treino, teste, list(range(1, 21)), k=10)"
```

A avaliação pressupõe que as relações `RATED_TRAIN` e `SIMILAR_TO` já estejam preparadas no banco.

## 9. Limitações

- O desempenho observado na avaliação inicial é baixo.
- A avaliação foi feita em uma amostra de usuários.
- A implementação atual considera somente similaridades positivas.
- As recomendações dependem da quantidade e da distribuição das avaliações disponíveis.
- O sistema não possui, nesta versão, tratamento específico para usuários ou filmes sem histórico suficiente.

## 10. Conclusão

O projeto implementa uma abordagem de filtragem colaborativa baseada em grafos, utilizando o Neo4j para representar as relações entre usuários e filmes e o Python para calcular similaridades, estimar notas e avaliar recomendações.

A implementação permite explorar como a similaridade entre filmes pode ser utilizada para gerar recomendações personalizadas. Os resultados iniciais também evidenciam a importância de validar o algoritmo e aperfeiçoar a estratégia de avaliação.

## 11. Referências

- MovieLens: https://grouplens.org/datasets/movielens/
- Neo4j Documentation: https://neo4j.com/docs/
- Python Documentation: https://docs.python.org/3/
