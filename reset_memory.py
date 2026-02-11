#!/usr/bin/env python3
"""
RESET MEMORY SCRIPT
WARNING: This script will WIPE ALL DATA from ChromaDB and Neo4j.
Use with caution!
"""

import chromadb
from neo4j import GraphDatabase
from dotenv import load_dotenv
import os
import shutil

load_dotenv()

def clear_chroma_db():
    print("🧹 Cleaning ChromaDB...")
    try:
        # Method 1: Use client to delete collection
        client = chromadb.PersistentClient(path="./chroma_db")
        try:
            client.delete_collection("conversation_memory")
            print("  ✓ Deleted 'conversation_memory' collection.")
        except ValueError:
            print("  ⚠ Collection 'conversation_memory' not found.")
        
        # Method 2: Nuke the directory (if needed, but client delete is safer)
        # if os.path.exists("./chroma_db"):
        #     shutil.rmtree("./chroma_db")
        #     print("  ✓ Removed chroma_db directory.")
            
    except Exception as e:
        print(f"  ❌ Error cleaning ChromaDB: {e}")

def clear_neo4j():
    print("\n🧹 Cleaning Neo4j Graph...")
    
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "password")
    
    if not uri or not password:
        print("  ❌ Missing Neo4j credentials in .env")
        return

    try:
        driver = GraphDatabase.driver(uri, auth=(user, password))
        driver.verify_connectivity()
        
        with driver.session() as session:
            # Delete all nodes and relationships
            result = session.run("MATCH (n) DETACH DELETE n")
            summary = result.consume()
            print(f"  ✓ Deleted {summary.counters.nodes_deleted} nodes and {summary.counters.relationships_deleted} relationships.")
            
        driver.close()
    except Exception as e:
        print(f"  ❌ Error cleaning Neo4j: {e}")

if __name__ == "__main__":
    print("⚠ WARNING: This will DELETE ALL MEMORY (Vector + Graph).")
    confirm = input("Are you sure? (Type 'yes' to proceed): ")
    
    if confirm.lower() == 'yes':
        clear_chroma_db()
        clear_neo4j()
        print("\n✨ Memory Reset Complete.")
    else:
        print("\n❌ Operation cancelled.")
