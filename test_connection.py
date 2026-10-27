
from neo4j import GraphDatabase
import os

URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
USER = os.getenv("NEO4J_USER", "neo4j")
PASSWORD = os.getenv("NEO4J_PASSWORD")


def main():
    driver = GraphDatabase.driver(
        URI,
        auth=(USER, PASSWORD)
    )

    try:
        with driver.session() as session:
            result = session.run("RETURN 'Conexão funcionando!' AS mensagem")
            record = result.single()
            print(record["mensagem"])
    finally:
        driver.close()


if __name__ == "__main__":
    main()
