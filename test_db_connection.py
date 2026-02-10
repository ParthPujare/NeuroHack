import os
import chromadb
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

def test_connections():
    print("Testing Connections...")
    
    # 1. Test ChromaDB
    try:
        print("\n[ChromaDB] Connecting...")
        chroma_client = chromadb.PersistentClient(path="./chroma_db")
        chroma_client.heartbeat()
        print("[ChromaDB] Logic Check: Heartbeat successful.")
        collection = chroma_client.get_or_create_collection(name="test_collection")
        collection.add(documents=["test"], ids=["test_id"])
        results = collection.query(query_texts=["test"], n_results=1)
        print(f"[ChromaDB] Read/Write Check: {results['ids']}")
        chroma_client.delete_collection("test_collection")
        print("[ChromaDB] Success.")
    except Exception as e:
        print(f"[ChromaDB] Failed: {e}")

    # 2. Test Neo4j
    neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    neo4j_user = os.getenv("NEO4J_USER", "neo4j")
    neo4j_password = os.getenv("NEO4J_PASSWORD", "password")

    try:
        print("\n[Neo4j] Connecting...")
        driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
        driver.verify_connectivity()
        print("[Neo4j] Connectivity verified.")
        with driver.session() as session:
            result = session.run("RETURN 1 as val")
            val = result.single()["val"]
            print(f"[Neo4j] Query Check: returned {val}")
        driver.close()
        print("[Neo4j] Success.")
    except Exception as e:
        print(f"[Neo4j] Failed: {e}")

if __name__ == "__main__":
    test_connections()
