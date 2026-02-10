import os
import chromadb
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

class MemoryManager:
    def __init__(self):
        # Initialize ChromaDB
        self.chroma_client = chromadb.PersistentClient(path="./chroma_db")
        self.collection = self.chroma_client.get_or_create_collection(name="conversation_memory")

        # Initialize Neo4j
        self.neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.neo4j_user = os.getenv("NEO4J_USER", "neo4j")
        self.neo4j_password = os.getenv("NEO4J_PASSWORD", "password")
        
        try:
            self.driver = GraphDatabase.driver(
                self.neo4j_uri, 
                auth=(self.neo4j_user, self.neo4j_password)
            )
            # Verify connection
            self.driver.verify_connectivity()
            print("Connected to Neo4j.")
        except Exception as e:
            print(f"Failed to connect to Neo4j: {e}. Running in Mock Mode for Graph DB.")
            self.driver = None

    def close(self):
        if self.driver:
            self.driver.close()

    def add_vector_memory(self, turn_id, text, metadata=None):
        """Adds a conversation turn to ChromaDB."""
        if metadata is None:
            metadata = {}
        self.collection.add(
            documents=[text],
            metadatas=[metadata],
            ids=[str(turn_id)]
        )

    def search_vector_memory(self, query, n_results=3):
        """Retrieves similar past conversations from ChromaDB."""
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        return results

    def run_graph_query(self, cypher_query, parameters=None):
        """Executes a Cypher query on Neo4j."""
        if not self.driver:
            return []
        
        with self.driver.session() as session:
            result = session.run(cypher_query, parameters)
            return [record.data() for record in result]

    def add_graph_node(self, label, properties):
        """Adds a node to the Neo4j graph."""
        if not self.driver:
            print("DEBUG: Neo4j driver not available, skipping node creation")
            return
        
        # Ensure 'id' is in properties - only generate UUID if not provided
        if 'id' not in properties:
            import uuid
            properties['id'] = str(uuid.uuid4())
            print(f"DEBUG: Generated UUID for {label}: {properties['id']}")
        
        # Temporal Metadata Defaults
        import time
        if 'valid_from' not in properties:
            properties['valid_from'] = time.time()
        if 'status' not in properties:
            properties['status'] = 'active'
        
        def _create_node(tx, label, props):
            # Use label-specific MERGE with ID
            query = f"MERGE (n:{label} {{id: $id}}) SET n += $props RETURN n"
            print(f"DEBUG: Executing query: {query} with id={props['id']}")
            result = tx.run(query, id=props['id'], props=props)
            record = result.single()
            return record
        
        try:
            with self.driver.session() as session:
                result = session.execute_write(_create_node, label, properties)
                print(f"DEBUG: Successfully updated/created node: {label} with id={properties['id']}")
        except Exception as e:
            print(f"ERROR: Failed to create node {label}: {e}")

    def supersede_node(self, old_node_id, new_node_id, label):
        """Marks old node as obsolete and links new node to it with SUPERSEDES."""
        if not self.driver: return
        
        import time
        now = time.time()
        
        query = f"""
        MATCH (old:{label} {{id: $old_id}})
        MATCH (new:{label} {{id: $new_id}})
        SET old.status = 'obsolete', old.valid_until = $now
        MERGE (new)-[r:SUPERSEDES]->(old)
        SET r.timestamp = $now
        RETURN new, old
        """
        try:
            with self.driver.session() as session:
                session.run(query, old_id=old_node_id, new_id=new_node_id, now=now)
                print(f"DEBUG: Node {new_node_id} now SUPERSEDES {old_node_id}")
        except Exception as e:
            print(f"ERROR in supersede_node: {e}")

    def create_relationship(self, source_label, source_id, rel_type, target_label, target_id, rel_props=None):
        """Creates a relationship between two nodes."""
        if not self.driver:
            print("DEBUG: Neo4j driver not available, skipping relationship creation")
            return

        if rel_props is None:
            rel_props = {}
        
        def _create_rel(tx, src_label, src_id, r_type, tgt_label, tgt_id, r_props):
            query = (
                f"MATCH (a:{src_label} {{id: $source_id}}), (b:{tgt_label} {{id: $target_id}}) "
                f"MERGE (a)-[r:{r_type}]->(b) "
                f"SET r += $props "
                f"RETURN r"
            )
            print(f"DEBUG: Executing relationship query: {query}")
            result = tx.run(query, source_id=src_id, target_id=tgt_id, props=r_props)
            record = result.single()
            print(f"DEBUG: Relationship creation result: {record}")
            return record
        
        try:
            with self.driver.session() as session:
                result = session.execute_write(_create_rel, source_label, source_id, rel_type, target_label, target_id, rel_props)
                print(f"DEBUG: Successfully created relationship: {source_label}({source_id})-[{rel_type}]->{target_label}({target_id})")
        except Exception as e:
            print(f"ERROR: Failed to create relationship: {e}")
            import traceback
            traceback.print_exc()
