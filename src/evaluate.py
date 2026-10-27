
import csv

def split_ratings(csv_path="ratings.csv"):
    training = []
    testing = []

    with open(csv_path, "r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)

        for index, row in enumerate(reader):
            rating = {
                "userId": int(row["userId"]),
                "movieId": int(row["movieId"]),
                "rating": float(row["rating"]),
                "timestamp": int(row["timestamp"])
            }

            if index % 5 == 0:
                testing.append(rating)
            else:
                training.append(rating)

    print(f"Avaliações para treino: {len(training)}")
    print(f"Avaliações para teste: {len(testing)}")

    return training, testing


def precision_recall_at_k(recommended_ids, relevant_ids, k=10):
    recommended = set(recommended_ids[:k])
    relevant = set(relevant_ids)

    if not recommended:
        return 0.0, 0.0

    hits = len(recommended & relevant)

    precision = hits / len(recommended)
    recall = hits / len(relevant) if relevant else 0.0

    return precision, recall


def get_relevant_movies(testing, user_id, min_rating=4.0):
    return [
        rating["movieId"]
        for rating in testing
        if rating["userId"] == user_id
        and rating["rating"] >= min_rating
    ]


def evaluate_user(user_id, training, testing, k=10):
    from src.recommender import recommend_movies

    recommendations = recommend_movies(user_id, limit=k)

    recommended_ids = [
        movie["movie_id"]
        for movie in recommendations
    ]

    relevant_ids = get_relevant_movies(testing, user_id)

    precision, recall = precision_recall_at_k(
        recommended_ids,
        relevant_ids,
        k
    )

    print(f"Usuário avaliado: {user_id}")
    print(f"Filmes recomendados: {len(recommended_ids)}")
    print(f"Filmes relevantes no teste: {len(relevant_ids)}")
    print(f"Precision@{k}: {precision:.4f}")
    print(f"Recall@{k}: {recall:.4f}")

    return precision, recall


def prepare_training_graph(training):
    from neo4j import GraphDatabase
    from src.graph_queries import URI, USER, PASSWORD

    query = """
    UNWIND $rows AS row
    MATCH (u:User {userId: row.userId})
    MATCH (m:Movie {movieId: row.movieId})
    MERGE (u)-[r:RATED_TRAIN]->(m)
    SET r.rating = row.rating,
        r.timestamp = row.timestamp
    """

    driver = GraphDatabase.driver(
        URI,
        auth=(USER, PASSWORD)
    )

    try:
        with driver.session() as session:
            session.run(
                "MATCH ()-[r:RATED_TRAIN]->() DELETE r"
            ).consume()

            batch_size = 5000

            for start in range(0, len(training), batch_size):
                batch = training[start:start + batch_size]
                session.run(query, rows=batch).consume()
                print(
                    f"Avaliações de treino preparadas: "
                    f"{min(start + batch_size, len(training))}"
                    f"/{len(training)}"
                )
    finally:
        driver.close()


def evaluate_multiple_users(training, testing, user_ids, k=10):
    from src.recommender import recommend_movies

    total_precision = 0.0
    total_recall = 0.0
    evaluated = 0

    for user_id in user_ids:
        recommendations = recommend_movies(user_id, limit=k)
        recommended_ids = [
            movie["movie_id"] for movie in recommendations
        ]
        relevant_ids = get_relevant_movies(testing, user_id)

        precision, recall = precision_recall_at_k(
            recommended_ids, relevant_ids, k
        )

        total_precision += precision
        total_recall += recall
        evaluated += 1

        print(
            f"Usuário {user_id}: "
            f"Precision@{k}={precision:.4f}, "
            f"Recall@{k}={recall:.4f}"
        )

    if evaluated:
        print(f"Precision média: {total_precision / evaluated:.4f}")
        print(f"Recall médio: {total_recall / evaluated:.4f}")
