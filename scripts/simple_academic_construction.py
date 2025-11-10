#!/usr/bin/env python3
"""Simple script to construct academic knowledge graphs using HyperGraphRAG directly."""

import asyncio
import json
import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from hypergraphrag.data.academic_loader import AcademicLoader, create_sample_academic_data
from hypergraphrag import HyperGraphRAG
from config import Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load configuration
config = Config()
config.validate()


async def construct_academic_graph(dataset_type: str, output_dir: str):
    """Construct academic knowledge graph using HyperGraphRAG.
    
    Args:
        dataset_type: 'pubmed' or 'aminer'
        output_dir: Output directory (e.g., 'expr/pubmed')
    """
    logger.info(f"Constructing {dataset_type} academic knowledge graph")
    
    # Step 1: Prepare sample data
    sample_data_path = f"{output_dir}/sample_{dataset_type}_data.json"
    
    if not Path(sample_data_path).exists():
        logger.info(f"Creating sample {dataset_type} data...")
        create_sample_academic_data(sample_data_path, dataset_type)
    
    # Step 2: Load and clean data
    logger.info("Loading academic dataset...")
    loader = AcademicLoader(sample_data_path, dataset_type)
    dataset = loader.load_and_clean(output_dir=f"{output_dir}/cleaned_data")
    
    # Step 3: Prepare documents for HyperGraphRAG
    all_papers = dataset['train'] + dataset['val'] + dataset['test']
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
        
        documents.append(doc_text.strip())
    
    # Step 4: Initialize HyperGraphRAG and insert documents
    logger.info(f"Initializing HyperGraphRAG in {output_dir}")
    rag = HyperGraphRAG(working_dir=output_dir)
    
    logger.info(f"Processing {len(documents)} documents...")
    await rag.ainsert(documents)
    
    # Step 5: Update metadata
    metadata = {
        'dataset_type': dataset_type,
        'output_dir': output_dir,
        'entity_types': dataset['entity_types'],
        'statistics': dataset['statistics'],
        'construction_completed': True,
        'total_documents': len(documents),
        'total_queries': len(dataset['query_tasks'])
    }
    
    metadata_file = Path(output_dir) / 'metadata.json'
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    
    logger.info(f"Academic knowledge graph construction completed!")
    logger.info(f"Results saved to: {output_dir}")
    
    return metadata


async def main():
    """Main function."""
    # Construct PubMed knowledge graph
    logger.info("=== Constructing PubMed Knowledge Graph ===")
    pubmed_metadata = await construct_academic_graph('pubmed', 'expr/pubmed')
    
    # Construct AMiner knowledge graph
    logger.info("\n=== Constructing AMiner Knowledge Graph ===")
    aminer_metadata = await construct_academic_graph('aminer', 'expr/aminer')
    
    # Summary
    print("\n" + "="*50)
    print("ACADEMIC KNOWLEDGE GRAPH CONSTRUCTION SUMMARY")
    print("="*50)
    print(f"PubMed: {pubmed_metadata['total_documents']} documents processed")
    print(f"AMiner: {aminer_metadata['total_documents']} documents processed")
    print("\nBoth academic knowledge graphs are ready for DynHyperRAG evaluation!")


if __name__ == "__main__":
    asyncio.run(main())