#!/usr/bin/env python3
"""Script to construct academic knowledge graphs from PubMed/AMiner datasets.

This script:
1. Loads academic datasets using AcademicLoader
2. Constructs hypergraphs using the existing HyperGraphRAG pipeline
3. Sets up academic entity types and configurations
4. Saves the constructed graph and metadata

Usage:
    python scripts/construct_academic_graph.py <dataset_path> <dataset_type> [output_dir]
    
    dataset_type: 'pubmed' or 'aminer'
    output_dir: Optional output directory (default: expr/<dataset_type>)
"""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from hypergraphrag.data.academic_loader import AcademicLoader, create_sample_academic_data
from hypergraphrag.data.query_generator import AcademicQueryGenerator, save_query_tasks
from hypergraphrag import HyperGraphRAG
from config import global_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def setup_academic_config(dataset_type: str) -> dict:
    """Set up configuration for academic datasets.
    
    Args:
        dataset_type: Type of dataset ('pubmed' or 'aminer')
        
    Returns:
        Configuration dictionary
    """
    # Base configuration from global config
    config = global_config.copy()
    
    # Academic-specific entity types
    academic_entity_types = ['paper', 'author', 'institution', 'keyword', 'conference', 'journal']
    
    # Update configuration for academic domain
    config.update({
        'domain': 'academic',
        'dataset_type': dataset_type,
        'entity_types': academic_entity_types,
        'addon_params': {
            **config.get('addon_params', {}),
            'entity_types': academic_entity_types,
            'domain': 'academic'
        }
    })
    
    # Dataset-specific configurations
    if dataset_type == 'pubmed':
        config.update({
            'extraction_prompt_template': """
            Extract entities and relationships from this medical/biomedical research paper.
            Focus on: authors, institutions, medical keywords, research topics, methodologies.
            
            Text: {text}
            
            Extract:
            1. Authors and their affiliations
            2. Research institutions
            3. Medical/biomedical keywords and topics
            4. Research methodologies
            5. Key findings and relationships
            """,
            'entity_extraction_focus': ['author', 'institution', 'keyword', 'methodology', 'finding']
        })
    
    elif dataset_type == 'aminer':
        config.update({
            'extraction_prompt_template': """
            Extract entities and relationships from this computer science research paper.
            Focus on: authors, institutions, technical keywords, conferences, research areas.
            
            Text: {text}
            
            Extract:
            1. Authors and their affiliations
            2. Research institutions
            3. Technical keywords and research areas
            4. Conference/venue information
            5. Key contributions and relationships
            """,
            'entity_extraction_focus': ['author', 'institution', 'keyword', 'conference', 'contribution']
        })
    
    return config


async def construct_academic_graph(dataset_path: str, dataset_type: str, output_dir: str):
    """Construct academic knowledge graph.
    
    Args:
        dataset_path: Path to academic dataset
        dataset_type: Type of dataset ('pubmed' or 'aminer')
        output_dir: Output directory for results
    """
    logger.info(f"Starting academic graph construction for {dataset_type}")
    
    # Step 1: Set up output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    logger.info(f"Output directory: {output_path}")
    
    # Step 2: Load and clean academic data
    logger.info("Loading academic dataset...")
    loader = AcademicLoader(dataset_path, dataset_type)
    
    try:
        dataset = loader.load_and_clean(output_dir=str(output_path / 'cleaned_data'))
        logger.info(f"Loaded {dataset['statistics']['total_papers']} papers")
    except Exception as e:
        logger.error(f"Failed to load dataset: {e}")
        return
    
    # Step 3: Set up configuration
    config = setup_academic_config(dataset_type)
    
    # Step 4: Initialize HyperGraphRAG
    logger.info("Initializing HyperGraphRAG...")
    rag = HyperGraphRAG(
        working_dir=str(output_path),
        config=config
    )
    
    # Step 5: Process papers and build hypergraph
    logger.info("Building hypergraph from papers...")
    
    # Combine all papers for processing
    all_papers = dataset['train'] + dataset['val'] + dataset['test']
    
    # Convert papers to documents for HyperGraphRAG
    documents = []
    for paper in all_papers:
        # Create document text from paper
        doc_text = f"Title: {paper['title']}\n"
        
        if paper.get('abstract'):
            doc_text += f"Abstract: {paper['abstract']}\n"
        
        # Add author information
        if paper.get('authors'):
            authors_text = ", ".join([author['name'] for author in paper['authors']])
            doc_text += f"Authors: {authors_text}\n"
        
        # Add institution information
        if paper.get('institutions'):
            institutions_text = ", ".join(paper['institutions'])
            doc_text += f"Institutions: {institutions_text}\n"
        
        # Add keywords
        if paper.get('keywords'):
            keywords_text = ", ".join(paper['keywords'])
            doc_text += f"Keywords: {keywords_text}\n"
        
        # Add venue/journal
        venue = paper.get('journal') or paper.get('venue', '')
        if venue:
            doc_text += f"Published in: {venue}\n"
        
        # Add year
        if paper.get('publication_year'):
            doc_text += f"Year: {paper['publication_year']}\n"
        
        documents.append({
            'id': paper['id'],
            'text': doc_text.strip(),
            'metadata': {
                'title': paper['title'],
                'authors': paper.get('authors', []),
                'institutions': paper.get('institutions', []),
                'keywords': paper.get('keywords', []),
                'venue': venue,
                'year': paper.get('publication_year', ''),
                'dataset_type': dataset_type
            }
        })
    
    # Insert documents into HyperGraphRAG
    logger.info(f"Processing {len(documents)} documents...")
    try:
        await rag.ainsert(documents)
        logger.info("Hypergraph construction completed")
    except Exception as e:
        logger.error(f"Failed to build hypergraph: {e}")
        return
    
    # Step 6: Generate enhanced query tasks
    logger.info("Generating query tasks...")
    query_generator = AcademicQueryGenerator(all_papers, dataset['entity_types'])
    query_tasks, gold_answers = query_generator.generate_comprehensive_queries(num_queries=100)
    
    # Save query tasks
    save_query_tasks(query_tasks, gold_answers, str(output_path), dataset_type)
    
    # Step 7: Save configuration and metadata
    logger.info("Saving configuration and metadata...")
    
    # Save configuration
    config_file = output_path / 'config.json'
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    
    # Save dataset metadata
    metadata = {
        'dataset_type': dataset_type,
        'dataset_path': str(dataset_path),
        'output_dir': str(output_path),
        'entity_types': dataset['entity_types'],
        'statistics': dataset['statistics'],
        'construction_completed': True,
        'total_documents': len(documents),
        'total_queries': len(query_tasks)
    }
    
    metadata_file = output_path / 'metadata.json'
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    
    # Step 8: Generate summary report
    generate_construction_report(output_path, metadata, dataset['statistics'])
    
    logger.info(f"Academic graph construction completed successfully!")
    logger.info(f"Results saved to: {output_path}")
    
    return metadata


def generate_construction_report(output_path: Path, metadata: dict, statistics: dict):
    """Generate a construction report.
    
    Args:
        output_path: Output directory path
        metadata: Construction metadata
        statistics: Dataset statistics
    """
    report_content = f"""# Academic Knowledge Graph Construction Report

## Dataset Information
- **Dataset Type**: {metadata['dataset_type'].upper()}
- **Source Path**: {metadata['dataset_path']}
- **Output Directory**: {metadata['output_dir']}
- **Construction Date**: {metadata.get('construction_date', 'Unknown')}

## Dataset Statistics
- **Total Papers**: {statistics['total_papers']}
- **Training Papers**: {statistics['train_papers']}
- **Validation Papers**: {statistics['val_papers']}
- **Test Papers**: {statistics['test_papers']}

## Entity Statistics
- **Unique Authors**: {statistics['unique_authors']}
- **Unique Keywords**: {statistics['unique_keywords']}
- **Unique Institutions**: {statistics['unique_institutions']}

## Average Statistics per Paper
- **Authors per Paper**: {statistics.get('avg_authors_per_paper', 'N/A')}
- **Keywords per Paper**: {statistics.get('avg_keywords_per_paper', 'N/A')}
- **Institutions per Paper**: {statistics.get('avg_institutions_per_paper', 'N/A')}

## Query Tasks
- **Total Query Tasks**: {metadata['total_queries']}
- **Query Types**: Multiple types including simple entity, multi-entity, temporal, comparative, and complex queries

## Dataset Diversity
- **Years Covered**: {statistics.get('dataset_diversity', {}).get('years_covered', 'N/A')}
- **Papers with Abstracts**: {statistics.get('dataset_diversity', {}).get('has_abstracts', 'N/A')}

## Entity Types
{chr(10).join(f"- {entity_type}" for entity_type in metadata['entity_types'])}

## Files Generated
- `cleaned_data/`: Cleaned dataset splits (train.json, val.json, test.json)
- `{metadata['dataset_type']}_query_tasks.json`: Generated query tasks
- `{metadata['dataset_type']}_gold_answers.json`: Gold standard answers
- `{metadata['dataset_type']}_query_statistics.json`: Query statistics
- `config.json`: HyperGraphRAG configuration
- `metadata.json`: Construction metadata
- Various HyperGraphRAG files (graph, vectors, etc.)

## Usage
To use this academic knowledge graph:

1. **Query the graph**:
   ```python
   from hypergraphrag import HyperGraphRAG
   
   rag = HyperGraphRAG(working_dir="{output_path}")
   result = await rag.aquery("Your academic query here")
   ```

2. **Load query tasks for evaluation**:
   ```python
   import json
   
   with open("{metadata['dataset_type']}_query_tasks.json") as f:
       query_tasks = json.load(f)
   
   with open("{metadata['dataset_type']}_gold_answers.json") as f:
       gold_answers = json.load(f)
   ```

3. **Access cleaned data**:
   ```python
   with open("cleaned_data/train.json") as f:
       train_papers = json.load(f)
   ```

## Next Steps
1. Run evaluation experiments using the generated query tasks
2. Compare with baseline methods (standard RAG, GraphRAG)
3. Analyze performance on different query types
4. Optimize hyperparameters for academic domain
"""
    
    report_file = output_path / 'CONSTRUCTION_REPORT.md'
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    logger.info(f"Construction report saved to: {report_file}")


def main():
    """Main function."""
    if len(sys.argv) < 3:
        print("Usage: python construct_academic_graph.py <dataset_path> <dataset_type> [output_dir]")
        print("dataset_type: 'pubmed' or 'aminer'")
        print("output_dir: Optional output directory (default: expr/<dataset_type>)")
        sys.exit(1)
    
    dataset_path = sys.argv[1]
    dataset_type = sys.argv[2].lower()
    output_dir = sys.argv[3] if len(sys.argv) > 3 else f"expr/{dataset_type}"
    
    if dataset_type not in ['pubmed', 'aminer']:
        print(f"Error: Unsupported dataset type '{dataset_type}'. Must be 'pubmed' or 'aminer'")
        sys.exit(1)
    
    # Create sample data if dataset doesn't exist
    if not Path(dataset_path).exists():
        print(f"Dataset not found at {dataset_path}")
        print(f"Creating sample {dataset_type} data...")
        
        # Create sample data
        sample_dir = Path(dataset_path).parent
        sample_dir.mkdir(parents=True, exist_ok=True)
        create_sample_academic_data(dataset_path, dataset_type)
        print(f"Sample data created at {dataset_path}")
    
    # Run construction
    try:
        asyncio.run(construct_academic_graph(dataset_path, dataset_type, output_dir))
    except KeyboardInterrupt:
        print("\nConstruction interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Construction failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()