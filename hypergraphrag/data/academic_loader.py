"""Academic dataset loader for PubMed and AMiner datasets.

This module provides functionality to load, clean, and prepare academic datasets
(PubMed and AMiner) for use with DynHyperRAG.

Supported datasets:
- PubMed: Medical literature with paper-author-institution-keyword relationships
- AMiner: Computer science papers with author-venue-keyword relationships

The loader extracts multi-relational data including:
- Papers (title, abstract, keywords)
- Authors (name, affiliation)
- Institutions/Venues (name, location)
- Keywords/Topics (research areas)
"""

import json
import logging
import os
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set
import random
from datetime import datetime

logger = logging.getLogger(__name__)


class AcademicLoader:
    """Academic dataset loader for PubMed and AMiner datasets.
    
    This class handles:
    1. Loading data from various formats (JSON, XML, TSV)
    2. Extracting paper-author-institution-keyword relationships
    3. Cleaning and normalizing academic text
    4. Creating query tasks for evaluation
    5. Generating gold standard answers
    6. Splitting data into train/validation/test sets
    
    Attributes:
        data_path: Path to the academic dataset file or directory
        dataset_type: Type of dataset ('pubmed' or 'aminer')
        entity_types: List of academic entity types
    """
    
    # Academic entity types
    ENTITY_TYPES = ['paper', 'author', 'institution', 'keyword', 'conference', 'journal']
    
    def __init__(self, data_path: str, dataset_type: str = 'pubmed'):
        """Initialize the academic loader.
        
        Args:
            data_path: Path to academic dataset file or directory
            dataset_type: Type of dataset ('pubmed' or 'aminer')
        """
        self.data_path = Path(data_path)
        self.dataset_type = dataset_type.lower()
        self.entity_types = self.ENTITY_TYPES
        
        if self.dataset_type not in ['pubmed', 'aminer']:
            raise ValueError(f"Unsupported dataset type: {dataset_type}. Must be 'pubmed' or 'aminer'")
        
        if not self.data_path.exists():
            raise FileNotFoundError(f"Data path not found: {data_path}")
    
    def load_and_clean(self, output_dir: Optional[str] = None) -> Dict[str, any]:
        """Load and clean the academic dataset.
        
        This is the main entry point that orchestrates the entire pipeline:
        1. Load data files based on dataset type
        2. Extract paper-author-institution-keyword relationships
        3. Clean and validate records
        4. Create query tasks
        5. Generate gold standard answers
        6. Split into train/val/test sets
        7. Generate statistics
        
        Args:
            output_dir: Optional directory to save cleaned data
            
        Returns:
            Dictionary containing:
                - train: List of training papers
                - val: List of validation papers
                - test: List of test papers
                - entity_types: List of entity types for academic domain
                - query_tasks: List of query tasks for evaluation
                - gold_answers: Dictionary of gold standard answers
                - statistics: Dataset statistics
        """
        logger.info(f"Loading {self.dataset_type.upper()} dataset from {self.data_path}")
        
        # Step 1: Load data files based on dataset type
        if self.dataset_type == 'pubmed':
            raw_papers = self._load_pubmed_data()
        elif self.dataset_type == 'aminer':
            raw_papers = self._load_aminer_data()
        else:
            raise ValueError(f"Unsupported dataset type: {self.dataset_type}")
        
        logger.info(f"Loaded {len(raw_papers)} raw papers")
        
        # Step 2: Clean and validate
        logger.info("Cleaning and validating papers...")
        cleaned_papers = self._clean_and_validate(raw_papers)
        logger.info(f"Cleaned papers: {len(cleaned_papers)} (filtered {len(raw_papers) - len(cleaned_papers)})")
        
        # Step 3: Create query tasks
        logger.info("Creating query tasks...")
        query_tasks, gold_answers = self._create_query_tasks(cleaned_papers)
        logger.info(f"Created {len(query_tasks)} query tasks")
        
        # Step 4: Split dataset
        logger.info("Splitting dataset...")
        train, val, test = self._split_dataset(cleaned_papers, [0.7, 0.15, 0.15])
        logger.info(f"Split: train={len(train)}, val={len(val)}, test={len(test)}")
        
        # Step 5: Generate statistics
        statistics = self._generate_statistics(cleaned_papers, train, val, test, query_tasks)
        
        # Step 6: Save if output directory specified
        if output_dir:
            self._save_cleaned_data(output_dir, train, val, test, query_tasks, gold_answers, statistics)
        
        result = {
            'train': train,
            'val': val,
            'test': test,
            'entity_types': self.entity_types,
            'query_tasks': query_tasks,
            'gold_answers': gold_answers,
            'statistics': statistics
        }
        
        logger.info(f"{self.dataset_type.upper()} dataset loading complete")
        return result
    
    def _load_pubmed_data(self) -> List[Dict]:
        """Load PubMed dataset from XML or JSON files.
        
        Returns:
            List of raw paper dictionaries
        """
        papers = []
        
        if self.data_path.is_dir():
            # Load from directory containing multiple files
            for file_path in self.data_path.rglob('*'):
                if file_path.suffix.lower() in ['.xml', '.json']:
                    papers.extend(self._load_single_pubmed_file(file_path))
        else:
            # Load from single file
            papers = self._load_single_pubmed_file(self.data_path)
        
        return papers
    
    def _load_single_pubmed_file(self, file_path: Path) -> List[Dict]:
        """Load a single PubMed file (XML or JSON).
        
        Args:
            file_path: Path to the file
            
        Returns:
            List of paper dictionaries
        """
        papers = []
        
        try:
            if file_path.suffix.lower() == '.xml':
                papers = self._parse_pubmed_xml(file_path)
            elif file_path.suffix.lower() == '.json':
                papers = self._parse_pubmed_json(file_path)
            else:
                logger.warning(f"Unsupported file format: {file_path}")
        except Exception as e:
            logger.error(f"Error loading {file_path}: {e}")
        
        return papers
    
    def _parse_pubmed_xml(self, file_path: Path) -> List[Dict]:
        """Parse PubMed XML file.
        
        Args:
            file_path: Path to XML file
            
        Returns:
            List of paper dictionaries
        """
        papers = []
        
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            # Handle different XML structures
            articles = root.findall('.//PubmedArticle') or root.findall('.//Article')
            
            for article in articles:
                paper = self._extract_pubmed_article_info(article)
                if paper:
                    papers.append(paper)
                    
        except ET.ParseError as e:
            logger.error(f"XML parsing error in {file_path}: {e}")
        
        return papers
    
    def _extract_pubmed_article_info(self, article_elem) -> Optional[Dict]:
        """Extract information from a PubMed article XML element.
        
        Args:
            article_elem: XML element representing an article
            
        Returns:
            Dictionary with paper information or None if invalid
        """
        try:
            # Extract basic information
            pmid_elem = article_elem.find('.//PMID')
            pmid = pmid_elem.text if pmid_elem is not None else None
            
            title_elem = article_elem.find('.//ArticleTitle')
            title = title_elem.text if title_elem is not None else ""
            
            abstract_elem = article_elem.find('.//AbstractText')
            abstract = abstract_elem.text if abstract_elem is not None else ""
            
            # Extract authors
            authors = []
            author_elems = article_elem.findall('.//Author')
            for author_elem in author_elems:
                lastname_elem = author_elem.find('LastName')
                forename_elem = author_elem.find('ForeName')
                
                if lastname_elem is not None and forename_elem is not None:
                    author_name = f"{forename_elem.text} {lastname_elem.text}"
                    
                    # Extract affiliation
                    affiliation_elem = author_elem.find('.//Affiliation')
                    affiliation = affiliation_elem.text if affiliation_elem is not None else ""
                    
                    authors.append({
                        'name': author_name,
                        'affiliation': affiliation
                    })
            
            # Extract keywords
            keywords = []
            keyword_elems = article_elem.findall('.//Keyword')
            for keyword_elem in keyword_elems:
                if keyword_elem.text:
                    keywords.append(keyword_elem.text)
            
            # Extract MeSH terms as additional keywords
            mesh_elems = article_elem.findall('.//DescriptorName')
            for mesh_elem in mesh_elems:
                if mesh_elem.text:
                    keywords.append(mesh_elem.text)
            
            # Extract journal information
            journal_elem = article_elem.find('.//Journal/Title')
            journal = journal_elem.text if journal_elem is not None else ""
            
            # Extract publication date
            pub_date_elem = article_elem.find('.//PubDate')
            pub_year = ""
            if pub_date_elem is not None:
                year_elem = pub_date_elem.find('Year')
                pub_year = year_elem.text if year_elem is not None else ""
            
            # Validate required fields
            if not title or not authors:
                return None
            
            return {
                'id': pmid or f"pubmed_{hash(title)}",
                'title': title,
                'abstract': abstract,
                'authors': authors,
                'keywords': keywords,
                'journal': journal,
                'publication_year': pub_year,
                'dataset_type': 'pubmed'
            }
            
        except Exception as e:
            logger.error(f"Error extracting PubMed article info: {e}")
            return None
    
    def _parse_pubmed_json(self, file_path: Path) -> List[Dict]:
        """Parse PubMed JSON file.
        
        Args:
            file_path: Path to JSON file
            
        Returns:
            List of paper dictionaries
        """
        papers = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                # Handle different JSON structures
                if isinstance(data, list):
                    papers_data = data
                elif isinstance(data, dict):
                    papers_data = data.get('papers', data.get('articles', [data]))
                else:
                    logger.warning(f"Unexpected JSON structure in {file_path}")
                    return papers
                
                for paper_data in papers_data:
                    paper = self._extract_pubmed_json_info(paper_data)
                    if paper:
                        papers.append(paper)
                        
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error in {file_path}: {e}")
        
        return papers
    
    def _extract_pubmed_json_info(self, paper_data: Dict) -> Optional[Dict]:
        """Extract information from PubMed JSON data.
        
        Args:
            paper_data: Dictionary with paper information
            
        Returns:
            Dictionary with standardized paper information or None if invalid
        """
        try:
            # Extract basic information
            paper_id = paper_data.get('pmid') or paper_data.get('id') or f"pubmed_{hash(str(paper_data))}"
            title = paper_data.get('title', '').strip()
            abstract = paper_data.get('abstract', '').strip()
            
            # Extract authors
            authors = []
            authors_data = paper_data.get('authors', [])
            for author_data in authors_data:
                if isinstance(author_data, str):
                    authors.append({'name': author_data, 'affiliation': ''})
                elif isinstance(author_data, dict):
                    name = author_data.get('name', '')
                    affiliation = author_data.get('affiliation', '')
                    if name:
                        authors.append({'name': name, 'affiliation': affiliation})
            
            # Extract keywords
            keywords = paper_data.get('keywords', [])
            if isinstance(keywords, str):
                keywords = [kw.strip() for kw in keywords.split(',')]
            
            # Extract journal
            journal = paper_data.get('journal', '')
            
            # Extract publication year
            pub_year = str(paper_data.get('publication_year', ''))
            
            # Validate required fields
            if not title or not authors:
                return None
            
            return {
                'id': paper_id,
                'title': title,
                'abstract': abstract,
                'authors': authors,
                'keywords': keywords,
                'journal': journal,
                'publication_year': pub_year,
                'dataset_type': 'pubmed'
            }
            
        except Exception as e:
            logger.error(f"Error extracting PubMed JSON info: {e}")
            return None
    
    def _load_aminer_data(self) -> List[Dict]:
        """Load AMiner dataset from JSON files.
        
        Returns:
            List of raw paper dictionaries
        """
        papers = []
        
        if self.data_path.is_dir():
            # Load from directory containing multiple files
            for file_path in self.data_path.rglob('*.json'):
                papers.extend(self._load_single_aminer_file(file_path))
        else:
            # Load from single file
            papers = self._load_single_aminer_file(self.data_path)
        
        return papers
    
    def _load_single_aminer_file(self, file_path: Path) -> List[Dict]:
        """Load a single AMiner JSON file.
        
        Args:
            file_path: Path to the JSON file
            
        Returns:
            List of paper dictionaries
        """
        papers = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                # AMiner files can be large, so we might need line-by-line reading
                file_size = file_path.stat().st_size
                
                if file_size > 100 * 1024 * 1024:  # 100MB threshold
                    logger.info(f"Using line-by-line parsing for large AMiner file {file_path.name}")
                    for line in f:
                        line = line.strip()
                        if line:
                            try:
                                paper_data = json.loads(line)
                                paper = self._extract_aminer_info(paper_data)
                                if paper:
                                    papers.append(paper)
                            except json.JSONDecodeError:
                                continue
                else:
                    data = json.load(f)
                    if isinstance(data, list):
                        papers_data = data
                    elif isinstance(data, dict):
                        papers_data = data.get('papers', [data])
                    else:
                        return papers
                    
                    for paper_data in papers_data:
                        paper = self._extract_aminer_info(paper_data)
                        if paper:
                            papers.append(paper)
                            
        except Exception as e:
            logger.error(f"Error loading AMiner file {file_path}: {e}")
        
        return papers
    
    def _extract_aminer_info(self, paper_data: Dict) -> Optional[Dict]:
        """Extract information from AMiner paper data.
        
        Args:
            paper_data: Dictionary with AMiner paper information
            
        Returns:
            Dictionary with standardized paper information or None if invalid
        """
        try:
            # Extract basic information
            paper_id = paper_data.get('id') or f"aminer_{hash(str(paper_data))}"
            title = paper_data.get('title', '').strip()
            abstract = paper_data.get('abstract', '').strip()
            
            # Extract authors
            authors = []
            authors_data = paper_data.get('authors', [])
            for author_data in authors_data:
                if isinstance(author_data, str):
                    authors.append({'name': author_data, 'affiliation': ''})
                elif isinstance(author_data, dict):
                    name = author_data.get('name', '')
                    org = author_data.get('org', '')
                    if name:
                        authors.append({'name': name, 'affiliation': org})
            
            # Extract keywords/topics
            keywords = []
            # AMiner might have different keyword fields
            for key in ['keywords', 'fos', 'topics']:
                if key in paper_data:
                    kw_data = paper_data[key]
                    if isinstance(kw_data, list):
                        keywords.extend([str(kw) for kw in kw_data])
                    elif isinstance(kw_data, str):
                        keywords.extend([kw.strip() for kw in kw_data.split(',')])
            
            # Extract venue (conference/journal)
            venue = paper_data.get('venue', '')
            
            # Extract publication year
            pub_year = str(paper_data.get('year', ''))
            
            # Validate required fields
            if not title or not authors:
                return None
            
            return {
                'id': paper_id,
                'title': title,
                'abstract': abstract,
                'authors': authors,
                'keywords': keywords,
                'venue': venue,
                'publication_year': pub_year,
                'dataset_type': 'aminer'
            }
            
        except Exception as e:
            logger.error(f"Error extracting AMiner info: {e}")
            return None
    def _clean_and_validate(self, raw_papers: List[Dict]) -> List[Dict]:
        """Clean and validate paper records.
        
        Args:
            raw_papers: List of raw paper dictionaries
            
        Returns:
            List of cleaned and validated papers
        """
        cleaned_papers = []
        
        for paper in raw_papers:
            try:
                # Clean text fields
                paper['title'] = self._clean_text(paper.get('title', ''))
                paper['abstract'] = self._clean_text(paper.get('abstract', ''))
                
                # Validate minimum requirements
                if not self._is_valid_paper(paper):
                    continue
                
                # Clean author information
                paper['authors'] = self._clean_authors(paper.get('authors', []))
                
                # Clean and deduplicate keywords
                paper['keywords'] = self._clean_keywords(paper.get('keywords', []))
                
                # Extract institutions from author affiliations
                paper['institutions'] = self._extract_institutions(paper['authors'])
                
                # Add metadata
                paper['processed_at'] = datetime.now().isoformat()
                
                cleaned_papers.append(paper)
                
            except Exception as e:
                logger.error(f"Error cleaning paper {paper.get('id', 'unknown')}: {e}")
                continue
        
        return cleaned_papers
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text.
        
        Args:
            text: Raw text string
            
        Returns:
            Cleaned text string
        """
        if not text:
            return ""
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Remove control characters
        text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
        
        # Remove HTML tags if present
        text = re.sub(r'<[^>]+>', '', text)
        
        # Normalize quotes
        text = re.sub(r'[""''`]', '"', text)
        
        return text
    
    def _is_valid_paper(self, paper: Dict) -> bool:
        """Validate if a paper record is valid.
        
        Args:
            paper: Paper dictionary
            
        Returns:
            True if valid, False otherwise
        """
        # Check required fields
        if not paper.get('title') or len(paper['title']) < 10:
            return False
        
        if not paper.get('authors') or len(paper['authors']) == 0:
            return False
        
        # Check if abstract exists and has reasonable length
        abstract = paper.get('abstract', '')
        if abstract and len(abstract) < 50:
            # Abstract too short, might be incomplete
            return False
        
        return True
    
    def _clean_authors(self, authors: List[Dict]) -> List[Dict]:
        """Clean author information.
        
        Args:
            authors: List of author dictionaries
            
        Returns:
            List of cleaned author dictionaries
        """
        cleaned_authors = []
        seen_names = set()
        
        for author in authors:
            if isinstance(author, str):
                author = {'name': author, 'affiliation': ''}
            
            name = self._clean_text(author.get('name', ''))
            affiliation = self._clean_text(author.get('affiliation', ''))
            
            # Skip if name is empty or duplicate
            if not name or name.lower() in seen_names:
                continue
            
            seen_names.add(name.lower())
            cleaned_authors.append({
                'name': name,
                'affiliation': affiliation
            })
        
        return cleaned_authors
    
    def _clean_keywords(self, keywords: List[str]) -> List[str]:
        """Clean and deduplicate keywords.
        
        Args:
            keywords: List of keyword strings
            
        Returns:
            List of cleaned keywords
        """
        cleaned_keywords = []
        seen_keywords = set()
        
        for keyword in keywords:
            if not keyword:
                continue
            
            # Clean keyword
            keyword = self._clean_text(str(keyword))
            keyword = keyword.lower().strip()
            
            # Skip if empty or duplicate
            if not keyword or keyword in seen_keywords:
                continue
            
            # Skip very short or very long keywords
            if len(keyword) < 2 or len(keyword) > 50:
                continue
            
            seen_keywords.add(keyword)
            cleaned_keywords.append(keyword)
        
        return cleaned_keywords[:20]  # Limit to 20 keywords per paper
    
    def _extract_institutions(self, authors: List[Dict]) -> List[str]:
        """Extract unique institutions from author affiliations.
        
        Args:
            authors: List of author dictionaries
            
        Returns:
            List of unique institution names
        """
        institutions = set()
        
        for author in authors:
            affiliation = author.get('affiliation', '')
            if not affiliation:
                continue
            
            # Extract institution names from affiliation text
            # This is a simplified extraction - could be improved with NER
            affiliation = self._clean_text(affiliation)
            
            # Split by common separators
            parts = re.split(r'[,;]', affiliation)
            
            for part in parts:
                part = part.strip()
                if len(part) > 5:  # Minimum length for institution name
                    institutions.add(part)
        
        return list(institutions)[:10]  # Limit to 10 institutions per paper
    
    def _create_query_tasks(self, papers: List[Dict]) -> Tuple[List[Dict], Dict[str, List[str]]]:
        """Create query tasks for evaluation.
        
        Args:
            papers: List of cleaned paper dictionaries
            
        Returns:
            Tuple of (query_tasks, gold_answers)
        """
        query_tasks = []
        gold_answers = {}
        
        # Collect entities for query generation
        all_authors = set()
        all_keywords = set()
        all_institutions = set()
        
        for paper in papers:
            for author in paper.get('authors', []):
                all_authors.add(author['name'])
            
            for keyword in paper.get('keywords', []):
                all_keywords.add(keyword)
            
            for institution in paper.get('institutions', []):
                all_institutions.add(institution)
        
        # Convert to lists for sampling
        authors_list = list(all_authors)
        keywords_list = list(all_keywords)
        institutions_list = list(all_institutions)
        
        # Generate different types of queries
        query_tasks.extend(self._generate_author_queries(papers, authors_list))
        query_tasks.extend(self._generate_keyword_queries(papers, keywords_list))
        query_tasks.extend(self._generate_institution_queries(papers, institutions_list))
        query_tasks.extend(self._generate_collaboration_queries(papers, authors_list))
        
        # Generate gold answers for each query
        for query_task in query_tasks:
            query_id = query_task['id']
            gold_answers[query_id] = self._find_gold_answers(query_task, papers)
        
        return query_tasks, gold_answers
    
    def _generate_author_queries(self, papers: List[Dict], authors: List[str]) -> List[Dict]:
        """Generate author-based queries.
        
        Args:
            papers: List of papers
            authors: List of author names
            
        Returns:
            List of query dictionaries
        """
        queries = []
        
        # Sample authors who have multiple papers
        author_paper_count = {}
        for paper in papers:
            for author in paper.get('authors', []):
                name = author['name']
                author_paper_count[name] = author_paper_count.get(name, 0) + 1
        
        prolific_authors = [name for name, count in author_paper_count.items() if count >= 2]
        
        # Generate queries
        for i, author in enumerate(random.sample(prolific_authors, min(20, len(prolific_authors)))):
            queries.append({
                'id': f'author_query_{i+1}',
                'type': 'author_papers',
                'query': f"Find papers by author {author}",
                'target_author': author,
                'difficulty': 'easy'
            })
        
        return queries
    
    def _generate_keyword_queries(self, papers: List[Dict], keywords: List[str]) -> List[Dict]:
        """Generate keyword-based queries.
        
        Args:
            papers: List of papers
            keywords: List of keywords
            
        Returns:
            List of query dictionaries
        """
        queries = []
        
        # Sample keywords that appear in multiple papers
        keyword_paper_count = {}
        for paper in papers:
            for keyword in paper.get('keywords', []):
                keyword_paper_count[keyword] = keyword_paper_count.get(keyword, 0) + 1
        
        common_keywords = [kw for kw, count in keyword_paper_count.items() if count >= 2]
        
        # Generate queries
        for i, keyword in enumerate(random.sample(common_keywords, min(15, len(common_keywords)))):
            queries.append({
                'id': f'keyword_query_{i+1}',
                'type': 'keyword_papers',
                'query': f"Find papers about {keyword}",
                'target_keyword': keyword,
                'difficulty': 'medium'
            })
        
        return queries
    
    def _generate_institution_queries(self, papers: List[Dict], institutions: List[str]) -> List[Dict]:
        """Generate institution-based queries.
        
        Args:
            papers: List of papers
            institutions: List of institutions
            
        Returns:
            List of query dictionaries
        """
        queries = []
        
        # Sample institutions with multiple papers
        institution_paper_count = {}
        for paper in papers:
            for institution in paper.get('institutions', []):
                institution_paper_count[institution] = institution_paper_count.get(institution, 0) + 1
        
        active_institutions = [inst for inst, count in institution_paper_count.items() if count >= 2]
        
        # Generate queries
        for i, institution in enumerate(random.sample(active_institutions, min(10, len(active_institutions)))):
            queries.append({
                'id': f'institution_query_{i+1}',
                'type': 'institution_papers',
                'query': f"Find papers from {institution}",
                'target_institution': institution,
                'difficulty': 'medium'
            })
        
        return queries
    
    def _generate_collaboration_queries(self, papers: List[Dict], authors: List[str]) -> List[Dict]:
        """Generate collaboration-based queries.
        
        Args:
            papers: List of papers
            authors: List of authors
            
        Returns:
            List of query dictionaries
        """
        queries = []
        
        # Find author collaborations
        collaborations = {}
        for paper in papers:
            paper_authors = [author['name'] for author in paper.get('authors', [])]
            if len(paper_authors) >= 2:
                for i, author1 in enumerate(paper_authors):
                    for author2 in paper_authors[i+1:]:
                        pair = tuple(sorted([author1, author2]))
                        if pair not in collaborations:
                            collaborations[pair] = []
                        collaborations[pair].append(paper['id'])
        
        # Generate queries for collaborations with multiple papers
        collab_queries = []
        for (author1, author2), paper_ids in collaborations.items():
            if len(paper_ids) >= 2:
                collab_queries.append({
                    'authors': [author1, author2],
                    'paper_count': len(paper_ids)
                })
        
        # Sample collaboration queries
        for i, collab in enumerate(random.sample(collab_queries, min(10, len(collab_queries)))):
            author1, author2 = collab['authors']
            queries.append({
                'id': f'collaboration_query_{i+1}',
                'type': 'author_collaboration',
                'query': f"Find papers co-authored by {author1} and {author2}",
                'target_authors': [author1, author2],
                'difficulty': 'hard'
            })
        
        return queries
    
    def _find_gold_answers(self, query_task: Dict, papers: List[Dict]) -> List[str]:
        """Find gold standard answers for a query task.
        
        Args:
            query_task: Query task dictionary
            papers: List of papers
            
        Returns:
            List of paper IDs that match the query
        """
        matching_papers = []
        query_type = query_task['type']
        
        if query_type == 'author_papers':
            target_author = query_task['target_author']
            for paper in papers:
                author_names = [author['name'] for author in paper.get('authors', [])]
                if target_author in author_names:
                    matching_papers.append(paper['id'])
        
        elif query_type == 'keyword_papers':
            target_keyword = query_task['target_keyword'].lower()
            for paper in papers:
                keywords = [kw.lower() for kw in paper.get('keywords', [])]
                if target_keyword in keywords:
                    matching_papers.append(paper['id'])
        
        elif query_type == 'institution_papers':
            target_institution = query_task['target_institution']
            for paper in papers:
                institutions = paper.get('institutions', [])
                if target_institution in institutions:
                    matching_papers.append(paper['id'])
        
        elif query_type == 'author_collaboration':
            target_authors = query_task['target_authors']
            for paper in papers:
                author_names = [author['name'] for author in paper.get('authors', [])]
                if all(author in author_names for author in target_authors):
                    matching_papers.append(paper['id'])
        
        return matching_papers
    
    def _split_dataset(self, papers: List[Dict], ratios: List[float]) -> Tuple[List[Dict], List[Dict], List[Dict]]:
        """Split dataset into train/validation/test sets.
        
        Args:
            papers: List of paper dictionaries
            ratios: List of ratios [train, val, test] that sum to 1.0
            
        Returns:
            Tuple of (train, val, test) paper lists
        """
        # Shuffle papers for random split
        shuffled_papers = papers.copy()
        random.shuffle(shuffled_papers)
        
        n_total = len(shuffled_papers)
        n_train = int(n_total * ratios[0])
        n_val = int(n_total * ratios[1])
        
        train = shuffled_papers[:n_train]
        val = shuffled_papers[n_train:n_train + n_val]
        test = shuffled_papers[n_train + n_val:]
        
        return train, val, test
    
    def _generate_statistics(self, papers: List[Dict], train: List[Dict], 
                           val: List[Dict], test: List[Dict], 
                           query_tasks: List[Dict]) -> Dict:
        """Generate dataset statistics.
        
        Args:
            papers: All papers
            train: Training papers
            val: Validation papers
            test: Test papers
            query_tasks: Query tasks
            
        Returns:
            Dictionary with statistics
        """
        # Basic counts
        stats = {
            'total_papers': len(papers),
            'train_papers': len(train),
            'val_papers': len(val),
            'test_papers': len(test),
            'total_queries': len(query_tasks)
        }
        
        # Entity counts
        all_authors = set()
        all_keywords = set()
        all_institutions = set()
        
        for paper in papers:
            for author in paper.get('authors', []):
                all_authors.add(author['name'])
            for keyword in paper.get('keywords', []):
                all_keywords.add(keyword)
            for institution in paper.get('institutions', []):
                all_institutions.add(institution)
        
        stats.update({
            'unique_authors': len(all_authors),
            'unique_keywords': len(all_keywords),
            'unique_institutions': len(all_institutions)
        })
        
        # Query type distribution
        query_types = {}
        for query in query_tasks:
            qtype = query['type']
            query_types[qtype] = query_types.get(qtype, 0) + 1
        
        stats['query_type_distribution'] = query_types
        
        # Average statistics
        if papers:
            avg_authors = sum(len(p.get('authors', [])) for p in papers) / len(papers)
            avg_keywords = sum(len(p.get('keywords', [])) for p in papers) / len(papers)
            avg_institutions = sum(len(p.get('institutions', [])) for p in papers) / len(papers)
            
            stats.update({
                'avg_authors_per_paper': round(avg_authors, 2),
                'avg_keywords_per_paper': round(avg_keywords, 2),
                'avg_institutions_per_paper': round(avg_institutions, 2)
            })
        
        # Dataset diversity
        stats['dataset_diversity'] = {
            'years_covered': self._get_year_range(papers),
            'has_abstracts': sum(1 for p in papers if p.get('abstract')) / len(papers) if papers else 0
        }
        
        return stats
    
    def _get_year_range(self, papers: List[Dict]) -> Dict:
        """Get the range of publication years in the dataset.
        
        Args:
            papers: List of papers
            
        Returns:
            Dictionary with year range information
        """
        years = []
        for paper in papers:
            year_str = paper.get('publication_year', '')
            if year_str and year_str.isdigit():
                years.append(int(year_str))
        
        if not years:
            return {'min_year': None, 'max_year': None, 'span': 0}
        
        return {
            'min_year': min(years),
            'max_year': max(years),
            'span': max(years) - min(years) + 1
        }
    
    def _save_cleaned_data(self, output_dir: str, train: List[Dict], val: List[Dict], 
                          test: List[Dict], query_tasks: List[Dict], 
                          gold_answers: Dict[str, List[str]], statistics: Dict):
        """Save cleaned data to output directory.
        
        Args:
            output_dir: Output directory path
            train: Training papers
            val: Validation papers
            test: Test papers
            query_tasks: Query tasks
            gold_answers: Gold standard answers
            statistics: Dataset statistics
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Save data splits
        with open(output_path / 'train.json', 'w', encoding='utf-8') as f:
            json.dump(train, f, ensure_ascii=False, indent=2)
        
        with open(output_path / 'val.json', 'w', encoding='utf-8') as f:
            json.dump(val, f, ensure_ascii=False, indent=2)
        
        with open(output_path / 'test.json', 'w', encoding='utf-8') as f:
            json.dump(test, f, ensure_ascii=False, indent=2)
        
        # Save query tasks and answers
        with open(output_path / 'query_tasks.json', 'w', encoding='utf-8') as f:
            json.dump(query_tasks, f, ensure_ascii=False, indent=2)
        
        with open(output_path / 'gold_answers.json', 'w', encoding='utf-8') as f:
            json.dump(gold_answers, f, ensure_ascii=False, indent=2)
        
        # Save statistics
        with open(output_path / 'statistics.json', 'w', encoding='utf-8') as f:
            json.dump(statistics, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Cleaned data saved to {output_path}")


# Example usage and testing functions
def create_sample_academic_data(output_path: str, dataset_type: str = 'pubmed'):
    """Create sample academic data for testing.
    
    Args:
        output_path: Path to save sample data
        dataset_type: Type of dataset ('pubmed' or 'aminer')
    """
    sample_papers = []
    
    if dataset_type == 'pubmed':
        sample_papers = [
            {
                "pmid": "12345678",
                "title": "Machine Learning Applications in Medical Diagnosis",
                "abstract": "This paper presents a comprehensive review of machine learning techniques applied to medical diagnosis. We examine various algorithms including neural networks, support vector machines, and decision trees in the context of disease prediction and classification.",
                "authors": [
                    {"name": "John Smith", "affiliation": "Harvard Medical School"},
                    {"name": "Jane Doe", "affiliation": "MIT Computer Science"}
                ],
                "keywords": ["machine learning", "medical diagnosis", "neural networks", "healthcare"],
                "journal": "Journal of Medical Informatics",
                "publication_year": "2023"
            },
            {
                "pmid": "87654321",
                "title": "Deep Learning for Cancer Detection in Medical Imaging",
                "abstract": "We propose a novel deep learning approach for automated cancer detection in medical images. Our convolutional neural network achieves 95% accuracy on a dataset of 10,000 medical scans.",
                "authors": [
                    {"name": "Alice Johnson", "affiliation": "Stanford University"},
                    {"name": "Bob Wilson", "affiliation": "UCSF Medical Center"}
                ],
                "keywords": ["deep learning", "cancer detection", "medical imaging", "CNN"],
                "journal": "Nature Medicine",
                "publication_year": "2023"
            }
        ]
    
    elif dataset_type == 'aminer':
        sample_papers = [
            {
                "id": "aminer_001",
                "title": "Attention Is All You Need: Transformer Architecture for NLP",
                "abstract": "We introduce the Transformer, a novel neural network architecture based solely on attention mechanisms. This model achieves state-of-the-art results on machine translation tasks while being more parallelizable than recurrent models.",
                "authors": [
                    {"name": "Ashish Vaswani", "org": "Google Brain"},
                    {"name": "Noam Shazeer", "org": "Google Brain"}
                ],
                "keywords": ["transformer", "attention mechanism", "neural networks", "NLP"],
                "venue": "NIPS",
                "year": "2017"
            },
            {
                "id": "aminer_002", 
                "title": "BERT: Pre-training of Deep Bidirectional Transformers",
                "abstract": "We introduce BERT, a new method for pre-training language representations which obtains state-of-the-art results on eleven natural language processing tasks.",
                "authors": [
                    {"name": "Jacob Devlin", "org": "Google AI Language"},
                    {"name": "Ming-Wei Chang", "org": "Google AI Language"}
                ],
                "keywords": ["BERT", "pre-training", "transformers", "language models"],
                "venue": "NAACL",
                "year": "2019"
            }
        ]
    
    # Save sample data
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(sample_papers, f, ensure_ascii=False, indent=2)
    
    logger.info(f"Sample {dataset_type} data created at {output_path}")


if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python academic_loader.py <data_path> <dataset_type>")
        print("dataset_type: 'pubmed' or 'aminer'")
        sys.exit(1)
    
    data_path = sys.argv[1]
    dataset_type = sys.argv[2]
    
    # Create sample data if path doesn't exist
    if not Path(data_path).exists():
        print(f"Creating sample {dataset_type} data at {data_path}")
        create_sample_academic_data(data_path, dataset_type)
    
    # Load and process data
    loader = AcademicLoader(data_path, dataset_type)
    result = loader.load_and_clean(output_dir=f"expr/{dataset_type}")
    
    print(f"Loaded {result['statistics']['total_papers']} papers")
    print(f"Created {result['statistics']['total_queries']} query tasks")
    print(f"Entity types: {result['entity_types']}")