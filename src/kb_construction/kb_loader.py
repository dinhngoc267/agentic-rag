from neo4j import GraphDatabase
from src.kb_construction.models import OntologyEntity

class Neo4jKBLoader:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def upsert_node(self, label: str, node):

        assert hasattr(node, "to_dict"), "Node must have a `to_dict` method"

        props = node.to_dict()
        cypher = f"MERGE (n:Node:{label} {{id: $id}}) SET n += $props"
        with self.driver.session() as session:
            session.run(cypher, id=props["id"], props=props)


    def upsert_relationship(self, from_id: str, to_id: str, rel_type: str):
        cypher = (
            f"MATCH (a {{id: $from_id}}), (b {{id: $to_id}}) "
            f"MERGE (a)-[r:{rel_type}]->(b)"
        )
        with self.driver.session() as session:
            session.run(cypher, from_id=from_id, to_id=to_id)

    def create_vector_index(self, embedding_dim: int, similarity_metric: str):

        with self.driver.session() as session:
            session.run("DROP INDEX node_embedding_index IF EXISTS")

        create_vector_index_query = f"""
                CREATE VECTOR INDEX node_embedding_index
                FOR (n:Node) ON (n.embedding)
                OPTIONS {{
                    indexConfig: {{
                        `vector.dimensions`: {embedding_dim},
                        `vector.similarity_function`: '{similarity_metric}'
                    }}
                }}
                """

        with self.driver.session() as session:
            session.run(create_vector_index_query)