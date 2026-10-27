
import csv
from neo4j import GraphDatabase
import os

URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
USER = os.getenv("NEO4J_USER", "neo4j")
PASSWORD = os.getenv("NEO4J_PASSWORD")

BATCH_SIZE = 5000


def read_csv(file_path):
    with open(file_path, mode="r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def import_movies(session, movies):
    query = """
    UNWIND $rows AS row
    MERGE (m:Movie {movieId: row.movieId})
    SET m.title = row.title,
        m.genres = row.genres
    """

    for start in range(0, len(movies), BATCH_SIZE):
        batch = movies[start:start + BATCH_SIZE]

        rows = [
            {
                "movieId": int(movie["movieId"]),
                "title": movie["title"],
                "genres": movie["genres"]
            }
            for movie in batch
        ]

        session.run(query, rows=rows).consume()



def import_ratings(session, ratings):
    query = """
    UNWIND $rows AS row
    MERGE (u:User {userId: row.userId})
    MATCH (m:Movie {movieId: row.movieId})
    MERGE (u)-[r:RATED]->(m)
    SET r.rating = row.rating,
        r.timestamp = row.timestamp
    """

    for start in range(0, len(ratings), BATCH_SIZE):
        batch = ratings[start:start + BATCH_SIZE]

        rows = [
            {
                "userId": int(rating["userId"]),
                "movieId": int(rating["movieId"]),
                "rating": float(rating["rating"]),
                "timestamp": int(rating["timestamp"])
            }
            for rating in batch
        ]

        session.run(query, rows=rows).consume()



def main():
    movies = read_csv("movies.csv")
    ratings = read_csv("ratings.csv")

    driver = GraphDatabase.driver(
        URI,
        auth=(USER, PASSWORD)
    )

    try:
        with driver.session() as session:
            import_movies(session, movies)
            print(f"Filmes processados: {len(movies)}")

            import_ratings(session, ratings)
            print(f"Avaliações processadas: {len(ratings)}")

    finally:
        driver.close()


if __name__ == "__main__":
    main()
