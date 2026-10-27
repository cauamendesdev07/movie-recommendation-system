
from neo4j import GraphDatabase
from math import sqrt
from src.evaluate import split_ratings
import os


URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
USER = os.getenv("NEO4J_USER", "neo4j")
PASSWORD = os.getenv("NEO4J_PASSWORD")

def build_movie_ratings(training):
    ratings_by_movie = {}

    for rating in training:
        movie_id = rating["movieId"]
        user_id = rating["userId"]
        score = rating["rating"]

        if movie_id not in ratings_by_movie:
            ratings_by_movie[movie_id] = {}

        ratings_by_movie[movie_id][user_id] = score

    return ratings_by_movie

def build_user_ratings(training):
    ratings_by_user = {}

    for rating in training:
        user_id = rating["userId"]
        movie_id = rating["movieId"]
        score = rating["rating"]

        if user_id not in ratings_by_user:
            ratings_by_user[user_id] = {}

        ratings_by_user[user_id][movie_id] = score

    return ratings_by_user

def pearson_from_statistics(stats):
    count, sum_1, sum_2, sum_sq_1, sum_sq_2, sum_products = stats

    if count < 5:
        return 0.0

    numerator = sum_products - (sum_1 * sum_2 / count)

    variance_1 = sum_sq_1 - (sum_1 ** 2 / count)
    variance_2 = sum_sq_2 - (sum_2 ** 2 / count)

    if variance_1 <= 0 or variance_2 <= 0:
        return 0.0

    denominator = sqrt(variance_1 * variance_2)

    return numerator / denominator

def calculate_similarities_for_movie(
    movie_id_1,
    ratings_by_user,
    min_common_users=5
):
    statistics = {}

    for movie_ratings in ratings_by_user.values():
        rating_1 = movie_ratings.get(movie_id_1)

        if rating_1 is None:
            continue

        for movie_id_2, rating_2 in movie_ratings.items():
            if movie_id_2 <= movie_id_1:
                continue

            if movie_id_2 not in statistics:
                statistics[movie_id_2] = [
                    0, 0.0, 0.0, 0.0, 0.0, 0.0
                ]

            stats = statistics[movie_id_2]
            stats[0] += 1
            stats[1] += rating_1
            stats[2] += rating_2
            stats[3] += rating_1 ** 2
            stats[4] += rating_2 ** 2
            stats[5] += rating_1 * rating_2

    similarities = []

    for movie_id_2, stats in statistics.items():
        if stats[0] < min_common_users:
            continue

        similarity = pearson_from_statistics(stats)

        if similarity > 0:
            similarities.append({
                "movie_id_1": movie_id_1,
                "movie_id_2": movie_id_2,
                "similarity": similarity,
                "common_users": stats[0]
            })

    return similarities

def main():
    training, testing = split_ratings()
    ratings_by_movie = build_movie_ratings(training)

    print(f"Filmes disponíveis no treino: {len(ratings_by_movie)}")
    print(f"Avaliações de treino: {len(training)}")
    print(f"Avaliações reservadas para teste: {len(testing)}")

    # As similaridades são calculadas separadamente por
    # calculate_and_save_similarities(), usando apenas o treino.

def calculate_and_save_similarities(
    training,
    min_common_users=5,
    batch_size=500
):
    ratings_by_user = build_user_ratings(training)

    movie_ids = sorted({
        rating["movieId"]
        for rating in training
    })

    total_saved = 0
    batch = []

    query = """
    UNWIND $rows AS row
    MATCH (m1:Movie {movieId: row.movie_id_1})
    MATCH (m2:Movie {movieId: row.movie_id_2})
    MERGE (m1)-[s:SIMILAR_TO]->(m2)
    SET s.similarity = row.similarity,
        s.common_users = row.common_users
    """

    driver = GraphDatabase.driver(
        URI,
        auth=(USER, PASSWORD)
    )

    try:
        with driver.session() as session:
            for index, movie_id_1 in enumerate(movie_ids, start=1):
                similarities = calculate_similarities_for_movie(
                    movie_id_1,
                    ratings_by_user,
                    min_common_users
                )

                for similarity in similarities:
                    batch.append(similarity)

                    if len(batch) >= batch_size:
                        session.run(query, rows=batch).consume()
                        total_saved += len(batch)
                        batch.clear()

                if index % 100 == 0:
                    print(
                        f"Filmes processados: {index}/{len(movie_ids)} | "
                        f"Similaridades salvas: {total_saved}"
                    )

            if batch:
                session.run(query, rows=batch).consume()
                total_saved += len(batch)

    finally:
        driver.close()

    print(f"Cálculo concluído. Similaridades salvas: {total_saved}")


if __name__ == "__main__":
    main()