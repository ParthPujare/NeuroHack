#!/usr/bin/env python3
"""
Cleanup script: removes duplicate entries from ChromaDB and Neo4j.
Run this once to clean existing data, then the dedup logic in pipeline.py prevents future dupes.
"""

import chromadb
from dotenv import load_dotenv
import os

load_dotenv()

def clean_chroma_db():
    print("🧹 Cleaning ChromaDB duplicates...")
    
    client = chromadb.PersistentClient(path="./chroma_db")
    collection = client.get_or_create_collection(name="conversation_memory")
    
    all_data = collection.get(include=["documents", "metadatas"])
    
    if not all_data or not all_data.get('documents'):
        print("  ChromaDB is empty.")
        return
    
    total = len(all_data['documents'])
    print(f"  Found {total} total entries.")
    
    # Track unique content — keep first occurrence, delete rest
    seen_content = {}
    ids_to_delete = []
    
    for i, doc in enumerate(all_data['documents']):
        doc_id = all_data['ids'][i]
        normalized = doc.strip().lower()
        
        if normalized in seen_content:
            ids_to_delete.append(doc_id)
            print(f"  ❌ Duplicate: [{doc_id}] '{doc[:60]}...'")
        else:
            seen_content[normalized] = doc_id
            print(f"  ✓ Keep:      [{doc_id}] '{doc[:60]}...'")
    
    if ids_to_delete:
        print(f"\n  Deleting {len(ids_to_delete)} duplicates...")
        collection.delete(ids=ids_to_delete)
        print(f"  ✓ Deleted! {total - len(ids_to_delete)} entries remain.")
    else:
        print("  ✓ No duplicates found!")


def clean_neo4j():
    from neo4j import GraphDatabase
    
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "password")
    
    print("\n🧹 Cleaning Neo4j duplicate entities...")
    
    try:
        driver = GraphDatabase.driver(uri, auth=(user, password))
        driver.verify_connectivity()
    except Exception as e:
        print(f"  ⚠ Can't connect to Neo4j: {e}")
        return
    
    with driver.session() as session:
        # Find duplicate entities (same name)
        result = session.run("""
            MATCH (e:Entity {status: 'active'})
            WITH e.name AS name, collect(e) AS entities, count(e) AS cnt
            WHERE cnt > 1
            RETURN name, [e IN entities | {id: e.id, name: e.name, type: e.type}] AS dupes, cnt
        """)
        
        for record in result:
            name = record['name']
            dupes = record['dupes']
            print(f"  Found {record['cnt']} duplicates for Entity '{name}':")
            
            # Keep the first, archive the rest
            keep_id = dupes[0]['id']
            print(f"    ✓ Keep: {keep_id}")
            
            for dupe in dupes[1:]:
                print(f"    ❌ Archive: {dupe['id']}")
                session.run(
                    "MATCH (n:Entity {id: $id}) SET n.status = 'obsolete', n.archived_at = timestamp()",
                    id=dupe['id']
                )
        
        # Also clean duplicate facts (same statement)
        result = session.run("""
            MATCH (f:Fact {status: 'active'})
            WITH f.statement AS stmt, collect(f) AS facts, count(f) AS cnt
            WHERE cnt > 1
            RETURN stmt, [f IN facts | {id: f.id, statement: f.statement}] AS dupes, cnt
        """)
        
        for record in result:
            stmt = record['stmt']
            dupes = record['dupes']
            print(f"  Found {record['cnt']} duplicates for Fact '{stmt[:50]}':")
            
            keep_id = dupes[0]['id']
            print(f"    ✓ Keep: {keep_id}")
            
            for dupe in dupes[1:]:
                print(f"    ❌ Archive: {dupe['id']}")
                session.run(
                    "MATCH (n:Fact {id: $id}) SET n.status = 'obsolete', n.archived_at = timestamp()",
                    id=dupe['id']
                )
    
    driver.close()
    print("  ✓ Neo4j cleanup done!")


if __name__ == "__main__":
    clean_chroma_db()
    clean_neo4j()
    print("\n✅ All cleanup complete!")
