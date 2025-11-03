"""Example usage of CAIL2019 data loader.

This script demonstrates how to use the CAIL2019Loader to load and clean
legal case data for use with DynHyperRAG.
"""

import json
import tempfile
from pathlib import Path

from hypergraphrag.data import CAIL2019Loader


def create_sample_data():
    """Create sample CAIL2019 data for demonstration."""
    
    sample_cases = [
        {
            "id": "demo_case_001",
            "fact": "被告人张三于2019年1月15日在某市商场内盗窃他人财物，包括手机一部、现金人民币5000元。经鉴定，被盗物品总价值人民币8000元。",
            "meta": {
                "accusation": ["盗窃"],
                "relevant_articles": [264],
                "term_of_imprisonment": {
                    "death_penalty": False,
                    "life_imprisonment": False,
                    "imprisonment": 12
                }
            }
        },
        {
            "id": "demo_case_002",
            "fact": "被告人李四于2019年2月20日因琐事与被害人王五发生争执，后持刀将王五刺伤，致其轻伤二级。",
            "meta": {
                "accusation": ["故意伤害"],
                "relevant_articles": [234],
                "term_of_imprisonment": {
                    "death_penalty": False,
                    "life_imprisonment": False,
                    "imprisonment": 6
                }
            }
        },
        {
            "id": "demo_case_003",
            "fact": "被告人赵六于2019年3月10日在某地非法持有毒品海洛因10克，被公安机关当场查获。",
            "meta": {
                "accusation": ["非法持有毒品"],
                "relevant_articles": [348],
                "term_of_imprisonment": {
                    "death_penalty": False,
                    "life_imprisonment": False,
                    "imprisonment": 24
                }
            }
        },
        {
            "id": "demo_case_004",
            "fact": "被告人孙七通过虚构事实的方式，骗取被害人钱某人民币50000元，用于个人挥霍。",
            "meta": {
                "accusation": ["诈骗"],
                "relevant_articles": [266],
                "term_of_imprisonment": {
                    "death_penalty": False,
                    "life_imprisonment": False,
                    "imprisonment": 36
                }
            }
        },
        {
            "id": "demo_case_005",
            "fact": "被告人周八在担任某公司会计期间，利用职务便利，挪用公司资金人民币200000元用于炒股，后无法归还。",
            "meta": {
                "accusation": ["挪用资金"],
                "relevant_articles": [272],
                "term_of_imprisonment": {
                    "death_penalty": False,
                    "life_imprisonment": False,
                    "imprisonment": 48
                }
            }
        }
    ]
    
    return sample_cases


def main():
    """Main demonstration function."""
    
    print("="*70)
    print("CAIL2019 Data Loader - Example Usage")
    print("="*70)
    
    # Create temporary directory with sample data
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Create sample data file
        print("\n1. Creating sample CAIL2019 data...")
        sample_cases = create_sample_data()
        data_file = tmpdir / "cail2019_sample.json"
        
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(sample_cases, f, ensure_ascii=False, indent=2)
        
        print(f"   ✓ Created {len(sample_cases)} sample cases")
        
        # Load and clean data
        print("\n2. Loading and cleaning data...")
        loader = CAIL2019Loader(str(tmpdir))
        result = loader.load_and_clean()
        
        print(f"   ✓ Loaded {result['statistics']['total_cases']} cases")
        print(f"   ✓ Train: {result['statistics']['train_cases']}")
        print(f"   ✓ Val: {result['statistics']['val_cases']}")
        print(f"   ✓ Test: {result['statistics']['test_cases']}")
        
        # Display entity types
        print("\n3. Legal Entity Types:")
        for entity_type in result['entity_types']:
            print(f"   - {entity_type}")
        
        # Display statistics
        print("\n4. Dataset Statistics:")
        stats = result['statistics']
        
        print(f"\n   Accusation Distribution:")
        for acc, count in list(stats['accusation_distribution'].items())[:5]:
            print(f"   - {acc}: {count} cases")
        
        print(f"\n   Article Distribution:")
        for art, count in list(stats['article_distribution'].items())[:5]:
            print(f"   - Article {art}: {count} cases")
        
        print(f"\n   Fact Length Statistics:")
        print(f"   - Mean: {stats['fact_length']['mean']:.1f} characters")
        print(f"   - Min: {stats['fact_length']['min']} characters")
        print(f"   - Max: {stats['fact_length']['max']} characters")
        
        # Display sample case
        print("\n5. Sample Case (from training set):")
        if result['train']:
            sample = result['train'][0]
            print(f"\n   ID: {sample['id']}")
            print(f"   Fact: {sample['fact'][:100]}...")
            print(f"   Accusation: {', '.join(sample['accusation'])}")
            print(f"   Articles: {', '.join(map(str, sample['articles']))}")
            print(f"   Imprisonment: {sample['term_of_imprisonment']['imprisonment']} months")
        
        # Integration example
        print("\n6. Integration with DynHyperRAG:")
        print("\n   # Step 1: Load data")
        print("   loader = CAIL2019Loader('data/cail2019.zip')")
        print("   result = loader.load_and_clean()")
        print("\n   # Step 2: Configure entity types")
        print("   config = {")
        print("       'entity_taxonomy': {'legal': result['entity_types']},")
        print("       'domain': 'legal'")
        print("   }")
        print("\n   # Step 3: Build knowledge graph")
        print("   rag = HyperGraphRAG(working_dir='expr/cail2019')")
        print("   for case in result['train']:")
        print("       rag.insert(case['fact'])")
        print("\n   # Step 4: Query")
        print("   answer = rag.query('盗窃罪的量刑标准是什么？')")
        
    print("\n" + "="*70)
    print("✓ Example completed successfully!")
    print("="*70)
    print("\nNext Steps:")
    print("1. Obtain the actual CAIL2019 dataset")
    print("2. Run: python -m hypergraphrag.data.cail2019_loader path/to/cail2019.zip")
    print("3. Use the cleaned data with DynHyperRAG")
    print("="*70)


if __name__ == '__main__':
    main()
