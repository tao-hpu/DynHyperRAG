"""
Graph Service

Business logic for hypergraph data access and manipulation.
"""

from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


class GraphService:
    """
    Service for accessing hypergraph data
    
    This service wraps HyperGraphRAG and provides methods to:
    - Access nodes (entities) and edges (hyperedges)
    - Search and filter graph data
    - Get graph statistics
    - Extract subgraphs
    """
    
    def __init__(self):
        self.rag = None
        self._initialized = False
    
    async def initialize(self, working_dir: str = "expr/example"):
        """
        Initialize HyperGraphRAG instance
        
        This loads all data from the working directory:
        - vdb_entities.json -> entity vectors
        - vdb_hyperedges.json -> hyperedge vectors
        - graph_chunk_entity_relation.graphml -> graph structure
        - kv_store_text_chunks.json -> text chunks
        
        Args:
            working_dir: Directory containing HyperGraphRAG data files
        
        Raises:
            Exception: If initialization fails
        """
        if self._initialized:
            logger.info("GraphService already initialized")
            return
        
        try:
            logger.info(f"Initializing HyperGraphRAG from {working_dir}...")
            
            # Import here to avoid circular dependencies
            from hypergraphrag import HyperGraphRAG
            from config import setup_environment
            from functools import partial
            from hypergraphrag.llm import openai_embedding
            from hypergraphrag.utils import EmbeddingFunc
            
            # Load configuration
            config = setup_environment()
            
            # Create embedding function
            embedding_func = partial(
                openai_embedding.func,
                **config.get_embedding_kwargs()
            )
            custom_embedding = EmbeddingFunc(
                embedding_dim=openai_embedding.embedding_dim,
                max_token_size=openai_embedding.max_token_size,
                func=embedding_func
            )
            
            # Initialize HyperGraphRAG
            self.rag = HyperGraphRAG(
                working_dir=working_dir,
                embedding_func=custom_embedding,
                llm_model_kwargs=config.get_llm_kwargs(),
                log_level="INFO"
            )
            
            # Verify data loaded
            graph = self.rag.chunk_entity_relation_graph._graph
            num_nodes = graph.number_of_nodes()
            num_edges = graph.number_of_edges()
            
            logger.info(f"✓ Loaded graph: {num_nodes} nodes, {num_edges} edges")
            
            self._initialized = True
            
        except Exception as e:
            logger.error(f"Failed to initialize GraphService: {e}")
            raise
    
    def _ensure_initialized(self):
        """Ensure service is initialized before use"""
        if not self._initialized or self.rag is None:
            raise RuntimeError("GraphService not initialized. Call initialize() first.")
    
    async def get_nodes(
        self,
        limit: int,
        offset: int,
        entity_type: Optional[str] = None
    ) -> List:
        """
        Get entity nodes with pagination and filtering
        
        Args:
            limit: Maximum number of nodes to return
            offset: Number of nodes to skip
            entity_type: Optional filter by entity type
        
        Returns:
            List of Node objects
        """
        self._ensure_initialized()
        
        from api.models.graph import Node
        
        graph = self.rag.chunk_entity_relation_graph._graph
        
        # Get only entity nodes (not hyperedge nodes)
        all_nodes = [
            (node_id, data) for node_id, data in graph.nodes(data=True)
            if data.get("role") == "entity"
        ]
        
        # Filter by entity type if specified
        if entity_type:
            all_nodes = [
                (node_id, data) for node_id, data in all_nodes
                if data.get("entity_type", "").strip('"') == entity_type
            ]
        
        # Apply pagination
        paginated_nodes = all_nodes[offset:offset + limit]
        
        # Convert to Node models
        nodes = []
        for node_id, data in paginated_nodes:
            # Clean entity_type (remove quotes if present)
            entity_type_raw = data.get("entity_type", "")
            entity_type_clean = entity_type_raw.strip('"') if entity_type_raw else "unknown"
            
            nodes.append(Node(
                id=node_id,
                label=node_id.strip('"'),  # Remove quotes from node ID for display
                type=entity_type_clean,
                description=data.get("description", "").strip('"'),
                weight=float(data.get("weight", 1.0))
            ))
        
        logger.info(f"Retrieved {len(nodes)} entity nodes (offset={offset}, limit={limit}, type={entity_type})")
        return nodes
    
    async def get_node_by_id(self, node_id: str) -> Optional:
        """
        Get a single node by ID
        
        Args:
            node_id: Node identifier
        
        Returns:
            Node object or None if not found
        """
        self._ensure_initialized()
        
        from api.models.graph import Node
        
        graph = self.rag.chunk_entity_relation_graph._graph
        
        if not graph.has_node(node_id):
            return None
        
        data = graph.nodes[node_id]
        
        # Only return entity nodes
        if data.get("role") != "entity":
            return None
        
        # Clean entity_type (remove quotes if present)
        entity_type_raw = data.get("entity_type", "")
        entity_type_clean = entity_type_raw.strip('"') if entity_type_raw else "unknown"
        
        return Node(
            id=node_id,
            label=node_id.strip('"'),
            type=entity_type_clean,
            description=data.get("description", "").strip('"'),
            weight=float(data.get("weight", 1.0))
        )
    
    async def get_edges(
        self,
        limit: int,
        offset: int,
        min_weight: Optional[float] = None
    ) -> List:
        """
        Get hyperedges with pagination and filtering
        
        This converts the bipartite graph (Entity-Hyperedge-Entity) into
        direct entity-to-entity edges for visualization.
        
        Args:
            limit: Maximum number of edges to return
            offset: Number of edges to skip
            min_weight: Optional minimum weight threshold
        
        Returns:
            List of Edge objects
        """
        self._ensure_initialized()
        
        from api.models.graph import Edge
        
        graph = self.rag.chunk_entity_relation_graph._graph
        
        # Convert bipartite graph to entity-entity edges
        # For each hyperedge node, create edges between all connected entities
        edges_data = []
        processed_hyperedges = set()
        
        for node_id, node_data in graph.nodes(data=True):
            if node_data.get("role") != "hyperedge":
                continue
            
            if node_id in processed_hyperedges:
                continue
            processed_hyperedges.add(node_id)
            
            # Get all entity neighbors of this hyperedge
            entity_neighbors = [
                n for n in graph.neighbors(node_id)
                if graph.nodes[n].get("role") == "entity"
            ]
            
            if len(entity_neighbors) < 2:
                continue
            
            # Get hyperedge weight
            hyperedge_weight = float(node_data.get("weight", 1.0))
            
            # Apply weight filter
            if min_weight is not None and hyperedge_weight < min_weight:
                continue
            
            # Create edges between all pairs of entities connected by this hyperedge
            for i in range(len(entity_neighbors)):
                for j in range(i + 1, len(entity_neighbors)):
                    src = entity_neighbors[i]
                    tgt = entity_neighbors[j]
                    
                    # Use hyperedge label as relation description
                    hyperedge_label = node_id.strip('"').strip('<hyperedge>')
                    
                    edges_data.append(Edge(
                        id=f"{src}-{tgt}-{node_id}",
                        source=src,
                        target=tgt,
                        relation="connected_via",
                        description=hyperedge_label,
                        weight=hyperedge_weight,
                        entities=entity_neighbors,
                        isHyperedge=len(entity_neighbors) >= 3
                    ))
        
        # Apply pagination
        paginated_edges = edges_data[offset:offset + limit]
        
        logger.info(f"Retrieved {len(paginated_edges)} edges from {len(processed_hyperedges)} hyperedges (offset={offset}, limit={limit}, min_weight={min_weight})")
        return paginated_edges
    
    async def get_edge_by_id(self, edge_id: str) -> Optional:
        """
        Get a single edge by ID
        
        Args:
            edge_id: Edge identifier (format: "source-target-hyperedge")
        
        Returns:
            Edge object or None if not found
        """
        self._ensure_initialized()
        
        from api.models.graph import Edge
        
        graph = self.rag.chunk_entity_relation_graph._graph
        
        try:
            # Parse edge ID (format: source-target-hyperedge_id)
            parts = edge_id.split("-", 2)
            if len(parts) < 3:
                logger.warning(f"Invalid edge ID format: {edge_id}")
                return None
            
            src, tgt, hyperedge_id = parts
            
            # Check if hyperedge exists
            if not graph.has_node(hyperedge_id):
                return None
            
            hyperedge_data = graph.nodes[hyperedge_id]
            if hyperedge_data.get("role") != "hyperedge":
                return None
            
            # Get all entity neighbors
            entity_neighbors = [
                n for n in graph.neighbors(hyperedge_id)
                if graph.nodes[n].get("role") == "entity"
            ]
            
            # Verify src and tgt are in the neighbors
            if src not in entity_neighbors or tgt not in entity_neighbors:
                return None
            
            hyperedge_weight = float(hyperedge_data.get("weight", 1.0))
            hyperedge_label = hyperedge_id.strip('"').strip('<hyperedge>')
            
            return Edge(
                id=edge_id,
                source=src,
                target=tgt,
                relation="connected_via",
                description=hyperedge_label,
                weight=hyperedge_weight,
                entities=entity_neighbors,
                isHyperedge=len(entity_neighbors) >= 3
            )
        except Exception as e:
            logger.warning(f"Error getting edge {edge_id}: {e}")
            return None
    
    async def get_stats(self):
        """
        Get hypergraph statistics
        
        Returns:
            GraphStats object with graph metrics
        """
        self._ensure_initialized()
        
        from api.models.graph import GraphStats
        import networkx as nx
        
        graph = self.rag.chunk_entity_relation_graph._graph
        
        num_nodes = graph.number_of_nodes()
        num_edges = graph.number_of_edges()
        
        # Calculate average degree
        if num_nodes > 0:
            avg_degree = sum(dict(graph.degree()).values()) / num_nodes
        else:
            avg_degree = 0.0
        
        # Count hyperedges (edges with 3+ entities)
        num_hyperedges = self._count_hyperedges(graph)
        
        # Calculate density
        density = nx.density(graph) if num_nodes > 1 else 0.0
        
        stats = GraphStats(
            num_nodes=num_nodes,
            num_edges=num_edges,
            num_hyperedges=num_hyperedges,
            avg_degree=avg_degree,
            density=density
        )
        
        logger.info(f"Graph stats: {num_nodes} nodes, {num_edges} edges, {num_hyperedges} hyperedges")
        return stats
    
    def _count_hyperedges(self, graph) -> int:
        """
        Count hyperedges (edges connecting 3+ entities)
        
        Args:
            graph: NetworkX graph
        
        Returns:
            Number of hyperedges
        """
        count = 0
        for _, _, data in graph.edges(data=True):
            entities = data.get("entities", [])
            if isinstance(entities, str):
                entities = [e.strip() for e in entities.split(",")]
            if len(entities) >= 3:
                count += 1
        return count
    
    async def get_subgraph(self, center_node_id: str, depth: int = 1):
        """
        Get subgraph around a center node using BFS
        
        Args:
            center_node_id: Center node ID
            depth: Number of hops to expand (1-3)
        
        Returns:
            GraphData object with nodes and edges
        """
        self._ensure_initialized()
        
        from api.models.graph import GraphData, Node, Edge
        
        graph = self.rag.chunk_entity_relation_graph._graph
        
        # Check if center node exists
        if center_node_id not in graph:
            logger.warning(f"Center node {center_node_id} not found")
            return GraphData(nodes=[], edges=[])
        
        # BFS to find neighbors up to specified depth
        visited = {center_node_id}
        current_level = {center_node_id}
        
        for _ in range(depth):
            next_level = set()
            for node in current_level:
                neighbors = set(graph.neighbors(node))
                next_level.update(neighbors - visited)
            visited.update(next_level)
            current_level = next_level
            
            if not current_level:  # No more neighbors
                break
        
        # Extract subgraph
        subgraph = graph.subgraph(visited)
        
        # Convert nodes to Node models (only entity nodes)
        nodes = []
        for node_id in subgraph.nodes():
            data = graph.nodes[node_id]
            
            # Only include entity nodes
            if data.get("role") != "entity":
                continue
            
            # Clean entity_type (remove quotes if present)
            entity_type_raw = data.get("entity_type", "")
            entity_type_clean = entity_type_raw.strip('"') if entity_type_raw else "unknown"
            
            nodes.append(Node(
                id=node_id,
                label=node_id.strip('"'),
                type=entity_type_clean,
                description=data.get("description", "").strip('"'),
                weight=float(data.get("weight", 1.0))
            ))
        
        # Convert bipartite graph to entity-entity edges
        edges = []
        for node_id in subgraph.nodes():
            node_data = graph.nodes[node_id]
            
            # Only process hyperedge nodes
            if node_data.get("role") != "hyperedge":
                continue
            
            # Get all entity neighbors of this hyperedge
            entity_neighbors = [
                n for n in graph.neighbors(node_id)
                if n in subgraph.nodes() and graph.nodes[n].get("role") == "entity"
            ]
            
            if len(entity_neighbors) < 2:
                continue
            
            hyperedge_weight = float(node_data.get("weight", 1.0))
            hyperedge_label = node_id.strip('"').strip('<hyperedge>')
            
            # Create edges between all pairs of entities
            for i in range(len(entity_neighbors)):
                for j in range(i + 1, len(entity_neighbors)):
                    src = entity_neighbors[i]
                    tgt = entity_neighbors[j]
                    
                    edges.append(Edge(
                        id=f"{src}-{tgt}-{node_id}",
                        source=src,
                        target=tgt,
                        relation="connected_via",
                        description=hyperedge_label,
                        weight=hyperedge_weight,
                        entities=entity_neighbors,
                        isHyperedge=len(entity_neighbors) >= 3
                    ))
        
        logger.info(f"Extracted subgraph: {len(nodes)} nodes, {len(edges)} edges (center={center_node_id}, depth={depth})")
        return GraphData(nodes=nodes, edges=edges)
    
    async def search_nodes(self, keyword: str, limit: int = 20):
        """
        Search nodes using semantic vector search
        
        Args:
            keyword: Search query
            limit: Maximum number of results
        
        Returns:
            List of Node objects with relevance scores
        """
        self._ensure_initialized()
        
        from api.models.graph import Node
        
        # Use vector search for semantic similarity
        entities_storage = self.rag.entities_vdb
        
        try:
            search_results = await entities_storage.query(keyword, top_k=limit)
            
            nodes = []
            for result in search_results:
                # Clean entity_type (remove quotes if present)
                entity_type_raw = result.get("entity_type", "")
                entity_type_clean = entity_type_raw.strip('"') if entity_type_raw else "unknown"
                
                nodes.append(Node(
                    id=result["id"],
                    label=result["id"].strip('"'),
                    type=entity_type_clean,
                    description=result.get("description", "").strip('"'),
                    weight=float(result.get("weight", 1.0)),
                    relevance_score=float(result.get("distance", 0.0))  # Cosine similarity
                ))
            
            logger.info(f"Search '{keyword}' returned {len(nodes)} results")
            return nodes
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            # Fallback to simple string matching if vector search fails
            return await self._fallback_search(keyword, limit)
    
    async def _fallback_search(self, keyword: str, limit: int):
        """
        Fallback search using simple string matching
        
        Args:
            keyword: Search query
            limit: Maximum number of results
        
        Returns:
            List of Node objects
        """
        from api.models.graph import Node
        
        graph = self.rag.chunk_entity_relation_graph._graph
        keyword_lower = keyword.lower()
        
        matches = []
        for node_id, data in graph.nodes(data=True):
            # Only search entity nodes
            if data.get("role") != "entity":
                continue
            
            entity_name = node_id.lower()
            description = data.get("description", "").lower()
            
            # Simple substring matching
            if keyword_lower in entity_name or keyword_lower in description:
                # Calculate simple relevance score
                score = 1.0 if keyword_lower in entity_name else 0.5
                
                # Clean entity_type (remove quotes if present)
                entity_type_raw = data.get("entity_type", "")
                entity_type_clean = entity_type_raw.strip('"') if entity_type_raw else "unknown"
                
                matches.append((score, Node(
                    id=node_id,
                    label=node_id.strip('"'),
                    type=entity_type_clean,
                    description=data.get("description", "").strip('"'),
                    weight=float(data.get("weight", 1.0)),
                    relevance_score=score
                )))
        
        # Sort by relevance score and limit
        matches.sort(key=lambda x: x[0], reverse=True)
        nodes = [node for _, node in matches[:limit]]
        
        logger.info(f"Fallback search '{keyword}' returned {len(nodes)} results")
        return nodes
