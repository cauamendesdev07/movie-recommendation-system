
from neo4j import GraphDatabase
from src.graph_queries import URI, USER, PASSWORD

def predict_rating(user_id, movie_id, k=20):
    query = """
    MATCH (u:User {userId: $user_id})-[r:RATED_TRAIN]->(neighbor:Movie)
    MATCH (neighbor)-[s:SIMILAR_TO]-(target:Movie {movieId: $movie_id})
    WHERE NOT EXISTS {
        MATCH (u)-[:RATED_TRAIN]->(target)
    }
    WITH neighbor, r.rating AS rating, s.similarity AS similarity
    ORDER BY abs(similarity) DESC
    LIMIT $k
    WITH collect({
        rating: rating,
        similarity: similarity
    }) AS neighbors
    WITH neighbors,
         reduce(total = 0.0, n IN neighbors |
             total + n.similarity * n.rating
         ) AS weighted_sum,
         reduce(total = 0.0, n IN neighbors |
             total + abs(n.similarity)
         ) AS similarity_sum
    RETURN
        CASE
            WHEN similarity_sum = 0 THEN null
            ELSE weighted_sum / similarity_sum
        END AS prediction,
        size(neighbors) AS neighbors_used
    """

    driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))

    try:
        with driver.session() as session:
            result = session.run(
                query,
                user_id=user_id,
                movie_id=movie_id,
                k=k
            )
            record = result.single()
            return dict(record) if record else {
                "prediction": None,
                "neighbors_used": 0
            }
    finally:
        driver.close()



def recommend_movies(user_id, limit=10):
    query = """
    MATCH (u:User {userId: $user_id})-[r:RATED_TRAIN]->(neighbor:Movie)
    MATCH (neighbor)-[s:SIMILAR_TO]-(candidate:Movie)
    WHERE NOT EXISTS {
        MATCH (u)-[:RATED_TRAIN]->(candidate)
    }
    WITH candidate, neighbor, r.rating AS rating,
        s.similarity AS similarity
    ORDER BY candidate.movieId, abs(similarity) DESC
    WITH candidate,
        collect({
            rating: rating,
            similarity: similarity
        })[..20] AS neighbors
    WITH candidate, neighbors,
         reduce(total = 0.0, n IN neighbors |
             total + n.similarity * n.rating
         ) AS weighted_sum,
         reduce(total = 0.0, n IN neighbors |
             total + abs(n.similarity)
         ) AS similarity_sum
         WHERE size(neighbors) >= 5
    WITH candidate,
         CASE
             WHEN similarity_sum = 0 THEN null
             ELSE weighted_sum / similarity_sum
         END AS prediction
    WHERE prediction IS NOT NULL
    RETURN candidate.movieId AS movie_id,
           candidate.title AS title,
           prediction AS predicted_rating
    ORDER BY predicted_rating DESC
    LIMIT $limit
    """

    driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))

    try:
        with driver.session() as session:
            result = session.run(
                query,
                user_id=user_id,
                limit=limit
            )
            return [dict(record) for record in result]
    finally:
        driver.close()

