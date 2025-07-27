from typing import List, Dict, Any

class KBRetrieval:
    def __init__(self, kb_loader):
        self.kb_loader = kb_loader

    def query_sections_by_embedding(self, query_embedding: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieve the top_k most relevant Section nodes, even if the closest match is a Mention or FigureRef,
        by following relationships back to the Section.
        """
        # """
        #         CALL db.index.vector.queryNodes('node_embedding_index', $topK, $embedding) YIELD node, score
        # // Try to match the parent Section (if node is not already a Section)
        # OPTIONAL MATCH (section:Section)-[:(HAS_MENTION|HAS_FIGURE)*0..1]->(node)
        # WITH node, score, section
        # RETURN
        #     CASE
        #         WHEN section IS NOT NULL THEN section
        #         ELSE node
        #     END AS section_node,
        #     score
        # ORDER BY score DESC
        # LIMIT $topK
        # """
        cypher = """

        CALL db.index.vector.queryNodes('node_embedding_index', $topK, $embedding) YIELD node, score
        OPTIONAL MATCH (section:Section)-[:HAS_MENTION|HAS_FIGURE]->(node)
        WITH node, score, CASE WHEN section IS NOT NULL THEN section ELSE node END AS section_node
        ORDER BY score DESC 
        RETURN DISTINCT section_node, score
        ORDER BY score DESC
        LIMIT $topK

        """
        with self.kb_loader.driver.session() as session:
            result = session.run(
                cypher,
                embedding=query_embedding,
                topK=top_k
            )
            found_sections = set()
            output = []
            for record in result:
                section_node = record["section_node"]
                score = record["score"]
                section_dict = dict(section_node)
                # Avoid duplicates
                section_id = section_dict.get("id")
                if section_id not in found_sections:
                    found_sections.add(section_id)
                    section_dict["similarity_score"] = score
                    output.append(section_dict)
            return output

if __name__ == "__main__":
    from src.kb_construction.kb_loader import Neo4jKBLoader
    import os
    from dotenv import load_dotenv
    load_dotenv()

    from src.kb_construction.utils import get_embedding

    loader = Neo4jKBLoader(os.getenv("NEO4J_URI"), os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD"))

    kb_retrieval = KBRetrieval(loader)

    query_embedding = get_embedding("State two differences between plant and animal cells that are visible under the light microscope?")

    output = kb_retrieval.query_sections_by_embedding(query_embedding=query_embedding, top_k=5)
    print(output)

# Example usage:
# loader = Neo4jKBLoader(uri, user, password)
# kb_retrieval = KBRetrieval(loader)
# results = kb_retrieval.query_sections_by_embedding(query_embedding=[...], top_k=5)