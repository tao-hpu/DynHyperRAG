"""Query task generator for academic datasets.

This module provides advanced query generation capabilities for academic datasets,
creating diverse and challenging query tasks for evaluation of DynHyperRAG.
"""

import json
import logging
import random
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from collections import defaultdict, Counter

logger = logging.getLogger(__name__)


class AcademicQueryGenerator:
    """Advanced query generator for academic datasets.
    
    This class creates diverse query tasks including:
    1. Simple entity queries (author, keyword, institution)
    2. Complex multi-entity queries (collaborations, cross-domain)
    3. Temporal queries (time-based research trends)
    4. Hierarchical queries (research area relationships)
    5. Comparative queries (comparing authors/institutions)
    """
    
    def __init__(self, papers: List[Dict], entity_types: List[str]):
        """Initialize the query generator.
        
        Args:
            papers: List of paper dictionaries
            entity_types: List of entity types in the dataset
        """
        self.papers = papers
        self.entity_types = entity_types
        self.entity_index = self._build_entity_index()
        
    def _build_entity_index(self) -> Dict[str, Dict[str, Set[str]]]:
        """Build inverted index for entities.
        
        Returns:
            Dictionary mapping entity types to entity values to paper IDs
        """
        index = defaultdict(lambda: defaultdict(set))
        
        for paper in self.papers:
            paper_id = paper['id']
            
            # Index authors
            for author in paper.get('authors', []):
                index['author'][author['name']].add(paper_id)
            
            # Index keywords
            for keyword in paper.get('keywords', []):
                index['keyword'][keyword].add(paper_id)
            
            # Index institutions
            for institution in paper.get('institutions', []):
                index['institution'][institution].add(paper_id)
            
            # Index venues (journals/conferences)
            venue = paper.get('journal') or paper.get('venue', '')
            if venue:
                index['venue'][venue].add(paper_id)
            
            # Index years
            year = paper.get('publication_year', '')
            if year:
                index['year'][year].add(paper_id)
        
        return index
    
    def generate_comprehensive_queries(self, num_queries: int = 100) -> Tuple[List[Dict], Dict[str, List[str]]]:
        """Generate a comprehensive set of query tasks.
        
        Args:
            num_queries: Total number of queries to generate
            
        Returns:
            Tuple of (query_tasks, gold_answers)
        """
        query_tasks = []
        gold_answers = {}
        
        # Distribute queries across different types
        query_distribution = {
            'simple_entity': int(num_queries * 0.3),
            'multi_entity': int(num_queries * 0.2),
            'temporal': int(num_queries * 0.15),
            'comparative': int(num_queries * 0.15),
            'hierarchical': int(num_queries * 0.1),
            'complex': int(num_queries * 0.1)
        }
        
        # Generate each type of query
        for query_type, count in query_distribution.items():
            if count > 0:
                type_queries = self._generate_queries_by_type(query_type, count)
                query_tasks.extend(type_queries)
        
        # Generate gold answers
        for query_task in query_tasks:
            query_id = query_task['id']
            gold_answers[query_id] = self._find_gold_answers(query_task)
        
        # Ensure query diversity
        query_tasks = self._ensure_query_diversity(query_tasks)
        
        return query_tasks, gold_answers
    
    def _generate_queries_by_type(self, query_type: str, count: int) -> List[Dict]:
        """Generate queries of a specific type.
        
        Args:
            query_type: Type of queries to generate
            count: Number of queries to generate
            
        Returns:
            List of query dictionaries
        """
        if query_type == 'simple_entity':
            return self._generate_simple_entity_queries(count)
        elif query_type == 'multi_entity':
            return self._generate_multi_entity_queries(count)
        elif query_type == 'temporal':
            return self._generate_temporal_queries(count)
        elif query_type == 'comparative':
            return self._generate_comparative_queries(count)
        elif query_type == 'hierarchical':
            return self._generate_hierarchical_queries(count)
        elif query_type == 'complex':
            return self._generate_complex_queries(count)
        else:
            logger.warning(f"Unknown query type: {query_type}")
            return []
    
    def _generate_simple_entity_queries(self, count: int) -> List[Dict]:
        """Generate simple entity-based queries.
        
        Args:
            count: Number of queries to generate
            
        Returns:
            List of query dictionaries
        """
        queries = []
        query_templates = {
            'author': [
                "Find papers by {entity}",
                "What papers has {entity} published?",
                "List publications by author {entity}",
                "Show research work by {entity}"
            ],
            'keyword': [
                "Find papers about {entity}",
                "What research exists on {entity}?",
                "Show papers related to {entity}",
                "Find studies on {entity}"
            ],
            'institution': [
                "Find papers from {entity}",
                "What research comes from {entity}?",
                "Show publications by {entity}",
                "List papers affiliated with {entity}"
            ],
            'venue': [
                "Find papers published in {entity}",
                "What papers appeared in {entity}?",
                "Show articles from {entity}",
                "List publications in {entity}"
            ]
        }
        
        generated = 0
        for entity_type in ['author', 'keyword', 'institution', 'venue']:
            if generated >= count:
                break
            
            # Get entities with sufficient papers
            entities = [(entity, len(papers)) for entity, papers in self.entity_index[entity_type].items() 
                       if len(papers) >= 2]
            entities.sort(key=lambda x: x[1], reverse=True)
            
            # Generate queries for this entity type
            type_count = min(count // 4, len(entities))
            for i in range(type_count):
                if generated >= count:
                    break
                
                entity, paper_count = entities[i]
                template = random.choice(query_templates[entity_type])
                
                queries.append({
                    'id': f'simple_{entity_type}_{generated+1}',
                    'type': f'simple_{entity_type}',
                    'query': template.format(entity=entity),
                    'target_entity': entity,
                    'entity_type': entity_type,
                    'difficulty': 'easy' if paper_count > 5 else 'medium',
                    'expected_count': paper_count
                })
                generated += 1
        
        return queries
    
    def _generate_multi_entity_queries(self, count: int) -> List[Dict]:
        """Generate multi-entity queries.
        
        Args:
            count: Number of queries to generate
            
        Returns:
            List of query dictionaries
        """
        queries = []
        
        # Author collaboration queries
        collaborations = self._find_author_collaborations()
        for i, (authors, paper_count) in enumerate(collaborations[:count//3]):
            queries.append({
                'id': f'multi_collaboration_{i+1}',
                'type': 'author_collaboration',
                'query': f"Find papers co-authored by {authors[0]} and {authors[1]}",
                'target_entities': authors,
                'entity_type': 'author',
                'difficulty': 'medium',
                'expected_count': paper_count
            })
        
        # Author-keyword queries
        author_keywords = self._find_author_keyword_pairs()
        for i, ((author, keyword), paper_count) in enumerate(author_keywords[:count//3]):
            queries.append({
                'id': f'multi_author_keyword_{i+1}',
                'type': 'author_keyword',
                'query': f"Find papers by {author} about {keyword}",
                'target_entities': [author, keyword],
                'entity_type': 'mixed',
                'difficulty': 'hard',
                'expected_count': paper_count
            })
        
        # Institution-keyword queries
        inst_keywords = self._find_institution_keyword_pairs()
        for i, ((institution, keyword), paper_count) in enumerate(inst_keywords[:count//3]):
            queries.append({
                'id': f'multi_inst_keyword_{i+1}',
                'type': 'institution_keyword',
                'query': f"Find papers from {institution} about {keyword}",
                'target_entities': [institution, keyword],
                'entity_type': 'mixed',
                'difficulty': 'hard',
                'expected_count': paper_count
            })
        
        return queries
    
    def _generate_temporal_queries(self, count: int) -> List[Dict]:
        """Generate temporal queries.
        
        Args:
            count: Number of queries to generate
            
        Returns:
            List of query dictionaries
        """
        queries = []
        
        # Get year range
        years = [int(year) for year in self.entity_index['year'].keys() if year.isdigit()]
        if not years:
            return queries
        
        min_year, max_year = min(years), max(years)
        
        # Recent papers queries
        recent_years = [str(year) for year in range(max_year-2, max_year+1)]
        for i, year in enumerate(recent_years[:count//3]):
            queries.append({
                'id': f'temporal_recent_{i+1}',
                'type': 'temporal_recent',
                'query': f"Find papers published in {year}",
                'target_year': year,
                'difficulty': 'easy',
                'expected_count': len(self.entity_index['year'][year])
            })
        
        # Year range queries
        for i in range(count//3):
            start_year = random.randint(min_year, max_year-2)
            end_year = start_year + random.randint(1, 3)
            
            queries.append({
                'id': f'temporal_range_{i+1}',
                'type': 'temporal_range',
                'query': f"Find papers published between {start_year} and {end_year}",
                'target_year_range': [start_year, end_year],
                'difficulty': 'medium'
            })
        
        # Trend queries (author over time)
        prolific_authors = [(author, papers) for author, papers in self.entity_index['author'].items() 
                           if len(papers) >= 5]
        for i, (author, _) in enumerate(prolific_authors[:count//3]):
            queries.append({
                'id': f'temporal_trend_{i+1}',
                'type': 'temporal_trend',
                'query': f"Show the research timeline of {author}",
                'target_entity': author,
                'entity_type': 'author',
                'difficulty': 'hard'
            })
        
        return queries
    
    def _generate_comparative_queries(self, count: int) -> List[Dict]:
        """Generate comparative queries.
        
        Args:
            count: Number of queries to generate
            
        Returns:
            List of query dictionaries
        """
        queries = []
        
        # Compare authors
        prolific_authors = [(author, len(papers)) for author, papers in self.entity_index['author'].items() 
                           if len(papers) >= 3]
        prolific_authors.sort(key=lambda x: x[1], reverse=True)
        
        for i in range(count//2):
            if i*2+1 < len(prolific_authors):
                author1, count1 = prolific_authors[i*2]
                author2, count2 = prolific_authors[i*2+1]
                
                queries.append({
                    'id': f'comparative_authors_{i+1}',
                    'type': 'comparative_authors',
                    'query': f"Compare the research output of {author1} and {author2}",
                    'target_entities': [author1, author2],
                    'entity_type': 'author',
                    'difficulty': 'hard'
                })
        
        # Compare institutions
        active_institutions = [(inst, len(papers)) for inst, papers in self.entity_index['institution'].items() 
                              if len(papers) >= 3]
        active_institutions.sort(key=lambda x: x[1], reverse=True)
        
        for i in range(count//2):
            if i*2+1 < len(active_institutions):
                inst1, count1 = active_institutions[i*2]
                inst2, count2 = active_institutions[i*2+1]
                
                queries.append({
                    'id': f'comparative_institutions_{i+1}',
                    'type': 'comparative_institutions',
                    'query': f"Compare research from {inst1} and {inst2}",
                    'target_entities': [inst1, inst2],
                    'entity_type': 'institution',
                    'difficulty': 'hard'
                })
        
        return queries
    
    def _generate_hierarchical_queries(self, count: int) -> List[Dict]:
        """Generate hierarchical queries (research area relationships).
        
        Args:
            count: Number of queries to generate
            
        Returns:
            List of query dictionaries
        """
        queries = []
        
        # Find related keywords (co-occurring keywords)
        keyword_cooccurrence = self._find_keyword_cooccurrence()
        
        for i, ((kw1, kw2), cooccur_count) in enumerate(keyword_cooccurrence[:count]):
            queries.append({
                'id': f'hierarchical_keywords_{i+1}',
                'type': 'hierarchical_keywords',
                'query': f"Find papers that discuss both {kw1} and {kw2}",
                'target_entities': [kw1, kw2],
                'entity_type': 'keyword',
                'difficulty': 'medium',
                'expected_count': cooccur_count
            })
        
        return queries
    
    def _generate_complex_queries(self, count: int) -> List[Dict]:
        """Generate complex multi-constraint queries.
        
        Args:
            count: Number of queries to generate
            
        Returns:
            List of query dictionaries
        """
        queries = []
        
        # Complex queries with multiple constraints
        for i in range(count):
            # Select random constraints
            constraints = []
            
            # Add author constraint (50% chance)
            if random.random() < 0.5:
                authors = list(self.entity_index['author'].keys())
                if authors:
                    author = random.choice(authors)
                    constraints.append(('author', author))
            
            # Add keyword constraint (70% chance)
            if random.random() < 0.7:
                keywords = list(self.entity_index['keyword'].keys())
                if keywords:
                    keyword = random.choice(keywords)
                    constraints.append(('keyword', keyword))
            
            # Add year constraint (30% chance)
            if random.random() < 0.3:
                years = list(self.entity_index['year'].keys())
                if years:
                    year = random.choice(years)
                    constraints.append(('year', year))
            
            # Add institution constraint (40% chance)
            if random.random() < 0.4:
                institutions = list(self.entity_index['institution'].keys())
                if institutions:
                    institution = random.choice(institutions)
                    constraints.append(('institution', institution))
            
            if len(constraints) >= 2:
                query_parts = []
                for constraint_type, value in constraints:
                    if constraint_type == 'author':
                        query_parts.append(f"by {value}")
                    elif constraint_type == 'keyword':
                        query_parts.append(f"about {value}")
                    elif constraint_type == 'year':
                        query_parts.append(f"from {value}")
                    elif constraint_type == 'institution':
                        query_parts.append(f"from {value}")
                
                query_text = f"Find papers {' and '.join(query_parts)}"
                
                queries.append({
                    'id': f'complex_multi_{i+1}',
                    'type': 'complex_multi_constraint',
                    'query': query_text,
                    'constraints': constraints,
                    'difficulty': 'very_hard'
                })
        
        return queries
    
    def _find_author_collaborations(self) -> List[Tuple[List[str], int]]:
        """Find author collaborations.
        
        Returns:
            List of (author_pair, paper_count) tuples
        """
        collaborations = defaultdict(int)
        
        for paper in self.papers:
            authors = [author['name'] for author in paper.get('authors', [])]
            if len(authors) >= 2:
                for i in range(len(authors)):
                    for j in range(i+1, len(authors)):
                        pair = tuple(sorted([authors[i], authors[j]]))
                        collaborations[pair] += 1
        
        # Return collaborations with at least 2 papers
        result = [(list(pair), count) for pair, count in collaborations.items() if count >= 2]
        result.sort(key=lambda x: x[1], reverse=True)
        return result
    
    def _find_author_keyword_pairs(self) -> List[Tuple[Tuple[str, str], int]]:
        """Find author-keyword pairs.
        
        Returns:
            List of ((author, keyword), paper_count) tuples
        """
        pairs = defaultdict(int)
        
        for paper in self.papers:
            authors = [author['name'] for author in paper.get('authors', [])]
            keywords = paper.get('keywords', [])
            
            for author in authors:
                for keyword in keywords:
                    pairs[(author, keyword)] += 1
        
        # Return pairs with at least 2 papers
        result = [(pair, count) for pair, count in pairs.items() if count >= 2]
        result.sort(key=lambda x: x[1], reverse=True)
        return result
    
    def _find_institution_keyword_pairs(self) -> List[Tuple[Tuple[str, str], int]]:
        """Find institution-keyword pairs.
        
        Returns:
            List of ((institution, keyword), paper_count) tuples
        """
        pairs = defaultdict(int)
        
        for paper in self.papers:
            institutions = paper.get('institutions', [])
            keywords = paper.get('keywords', [])
            
            for institution in institutions:
                for keyword in keywords:
                    pairs[(institution, keyword)] += 1
        
        # Return pairs with at least 2 papers
        result = [(pair, count) for pair, count in pairs.items() if count >= 2]
        result.sort(key=lambda x: x[1], reverse=True)
        return result
    
    def _find_keyword_cooccurrence(self) -> List[Tuple[Tuple[str, str], int]]:
        """Find keyword co-occurrence.
        
        Returns:
            List of ((keyword1, keyword2), cooccurrence_count) tuples
        """
        cooccurrence = defaultdict(int)
        
        for paper in self.papers:
            keywords = paper.get('keywords', [])
            if len(keywords) >= 2:
                for i in range(len(keywords)):
                    for j in range(i+1, len(keywords)):
                        pair = tuple(sorted([keywords[i], keywords[j]]))
                        cooccurrence[pair] += 1
        
        # Return co-occurrences with at least 2 papers
        result = [(pair, count) for pair, count in cooccurrence.items() if count >= 2]
        result.sort(key=lambda x: x[1], reverse=True)
        return result
    
    def _find_gold_answers(self, query_task: Dict) -> List[str]:
        """Find gold standard answers for a query task.
        
        Args:
            query_task: Query task dictionary
            
        Returns:
            List of paper IDs that match the query
        """
        query_type = query_task['type']
        matching_papers = set()
        
        if query_type.startswith('simple_'):
            entity_type = query_task['entity_type']
            target_entity = query_task['target_entity']
            matching_papers = self.entity_index[entity_type][target_entity].copy()
        
        elif query_type == 'author_collaboration':
            target_authors = query_task['target_entities']
            # Find papers with all target authors
            author_papers = [self.entity_index['author'][author] for author in target_authors]
            matching_papers = set.intersection(*author_papers)
        
        elif query_type == 'author_keyword':
            author, keyword = query_task['target_entities']
            author_papers = self.entity_index['author'][author]
            keyword_papers = self.entity_index['keyword'][keyword]
            matching_papers = author_papers.intersection(keyword_papers)
        
        elif query_type == 'institution_keyword':
            institution, keyword = query_task['target_entities']
            inst_papers = self.entity_index['institution'][institution]
            keyword_papers = self.entity_index['keyword'][keyword]
            matching_papers = inst_papers.intersection(keyword_papers)
        
        elif query_type == 'temporal_recent':
            target_year = query_task['target_year']
            matching_papers = self.entity_index['year'][target_year].copy()
        
        elif query_type == 'temporal_range':
            start_year, end_year = query_task['target_year_range']
            for year in range(start_year, end_year + 1):
                year_str = str(year)
                if year_str in self.entity_index['year']:
                    matching_papers.update(self.entity_index['year'][year_str])
        
        elif query_type == 'temporal_trend':
            target_author = query_task['target_entity']
            matching_papers = self.entity_index['author'][target_author].copy()
        
        elif query_type == 'comparative_authors':
            authors = query_task['target_entities']
            for author in authors:
                matching_papers.update(self.entity_index['author'][author])
        
        elif query_type == 'comparative_institutions':
            institutions = query_task['target_entities']
            for institution in institutions:
                matching_papers.update(self.entity_index['institution'][institution])
        
        elif query_type == 'hierarchical_keywords':
            keywords = query_task['target_entities']
            keyword_papers = [self.entity_index['keyword'][kw] for kw in keywords]
            matching_papers = set.intersection(*keyword_papers)
        
        elif query_type == 'complex_multi_constraint':
            constraints = query_task['constraints']
            constraint_papers = []
            
            for constraint_type, value in constraints:
                if constraint_type in self.entity_index and value in self.entity_index[constraint_type]:
                    constraint_papers.append(self.entity_index[constraint_type][value])
            
            if constraint_papers:
                matching_papers = set.intersection(*constraint_papers)
        
        return list(matching_papers)
    
    def _ensure_query_diversity(self, queries: List[Dict]) -> List[Dict]:
        """Ensure query diversity by filtering similar queries.
        
        Args:
            queries: List of query dictionaries
            
        Returns:
            List of diverse queries
        """
        # Group queries by type and difficulty
        query_groups = defaultdict(list)
        for query in queries:
            key = (query['type'], query.get('difficulty', 'medium'))
            query_groups[key].append(query)
        
        # Ensure balanced distribution
        diverse_queries = []
        for (qtype, difficulty), group_queries in query_groups.items():
            # Shuffle and take a reasonable number from each group
            random.shuffle(group_queries)
            max_per_group = max(1, len(queries) // len(query_groups))
            diverse_queries.extend(group_queries[:max_per_group])
        
        return diverse_queries


def save_query_tasks(query_tasks: List[Dict], gold_answers: Dict[str, List[str]], 
                    output_dir: str, dataset_name: str):
    """Save query tasks and gold answers to files.
    
    Args:
        query_tasks: List of query task dictionaries
        gold_answers: Dictionary of gold standard answers
        output_dir: Output directory
        dataset_name: Name of the dataset
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Save query tasks
    query_file = output_path / f'{dataset_name}_query_tasks.json'
    with open(query_file, 'w', encoding='utf-8') as f:
        json.dump(query_tasks, f, ensure_ascii=False, indent=2)
    
    # Save gold answers
    answers_file = output_path / f'{dataset_name}_gold_answers.json'
    with open(answers_file, 'w', encoding='utf-8') as f:
        json.dump(gold_answers, f, ensure_ascii=False, indent=2)
    
    # Generate query statistics
    stats = generate_query_statistics(query_tasks, gold_answers)
    stats_file = output_path / f'{dataset_name}_query_statistics.json'
    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    
    logger.info(f"Query tasks saved to {output_dir}")


def generate_query_statistics(query_tasks: List[Dict], gold_answers: Dict[str, List[str]]) -> Dict:
    """Generate statistics about query tasks.
    
    Args:
        query_tasks: List of query task dictionaries
        gold_answers: Dictionary of gold standard answers
        
    Returns:
        Dictionary with query statistics
    """
    stats = {
        'total_queries': len(query_tasks),
        'query_types': Counter(q['type'] for q in query_tasks),
        'difficulty_distribution': Counter(q.get('difficulty', 'medium') for q in query_tasks),
        'answer_count_distribution': {}
    }
    
    # Analyze answer counts
    answer_counts = [len(gold_answers.get(q['id'], [])) for q in query_tasks]
    if answer_counts:
        stats['answer_count_distribution'] = {
            'min': min(answer_counts),
            'max': max(answer_counts),
            'mean': sum(answer_counts) / len(answer_counts),
            'zero_answers': sum(1 for count in answer_counts if count == 0)
        }
    
    return stats


if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python query_generator.py <papers_file>")
        sys.exit(1)
    
    papers_file = sys.argv[1]
    
    # Load papers
    with open(papers_file, 'r', encoding='utf-8') as f:
        papers = json.load(f)
    
    # Generate queries
    entity_types = ['paper', 'author', 'institution', 'keyword', 'conference', 'journal']
    generator = AcademicQueryGenerator(papers, entity_types)
    query_tasks, gold_answers = generator.generate_comprehensive_queries(num_queries=50)
    
    # Save results
    output_dir = Path(papers_file).parent / 'queries'
    dataset_name = Path(papers_file).stem
    save_query_tasks(query_tasks, gold_answers, str(output_dir), dataset_name)
    
    print(f"Generated {len(query_tasks)} query tasks")
    print(f"Query types: {Counter(q['type'] for q in query_tasks)}")