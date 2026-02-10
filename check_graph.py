import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

uri = os.getenv("NEO4J_URI")
user = os.getenv("NEO4J_USER", "neo4j")
password = os.getenv("NEO4J_PASSWORD")

print(f"Connecting to {uri} as {user}...")

try:
    driver = GraphDatabase.driver(uri, auth=(user, password))
    with driver.session() as session:
        print("\n--- Nodes ---")
        result = session.run("MATCH (n) RETURN labels(n) as labels, n.id as id, properties(n) as props")
        nodes = list(result)
        if not nodes:
            print("No nodes found.")
        else:
            for record in nodes:
                print(f"Labels: {record['labels']}, ID: {record['id']}, Props: {record['props']}")
        
        print("\n--- Relationships ---")
        result = session.run("MATCH (a)-[r]->(b) RETURN properties(a).id as source, type(r) as type, properties(b).id as target, properties(r) as props")
        rels = list(result)
        if not rels:
            print("No relationships found.")
        else:
            for record in rels:
                print(f"{record['source']} -[{record['type']}]-> {record['target']} | Props: {record['props']}")

except Exception as e:
    print(f"Error: {e}")
finally:
    if 'driver' in locals():
        driver.close()
