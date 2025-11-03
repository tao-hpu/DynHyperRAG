"""Test CAIL2019 data loader implementation."""

import json
import tempfile
import zipfile
from pathlib import Path

from hypergraphrag.data.cail2019_loader import CAIL2019Loader


def test_cail2019_loader_basic():
    """Test basic CAIL2019 loader functionality with mock data."""
    
    # Create temporary directory with mock data
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Create mock CAIL2019 data
        mock_cases = [
            {
                "id": "case_001",
                "fact": "被告人张三于2019年1月在某地盗窃他人财物价值人民币5000元。",
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
                "id": "case_002",
                "fact": "被告人李四于2019年2月故意伤害他人身体，致人轻伤。",
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
                "id": "case_003",
                "fact": "被告人王五于2019年3月非法持有毒品海洛因10克。",
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
            # Invalid case - missing fact
            {
                "id": "case_004",
                "meta": {
                    "accusation": ["诈骗"]
                }
            },
            # Invalid case - fact too short
            {
                "id": "case_005",
                "fact": "短文本",
                "meta": {}
            }
        ]
        
        # Save mock data to JSON file
        data_file = tmpdir / "cail2019_data.json"
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(mock_cases, f, ensure_ascii=False)
        
        # Test loader
        loader = CAIL2019Loader(str(tmpdir))
        result = loader.load_and_clean()
        
        # Verify results
        print("\n" + "="*60)
        print("Test Results")
        print("="*60)
        
        # Check that invalid cases were filtered
        total_cases = result['statistics']['total_cases']
        print(f"✓ Total valid cases: {total_cases}")
        assert total_cases == 3, f"Expected 3 valid cases, got {total_cases}"
        
        # Check splits
        train_count = result['statistics']['train_cases']
        val_count = result['statistics']['val_cases']
        test_count = result['statistics']['test_cases']
        print(f"✓ Train/Val/Test split: {train_count}/{val_count}/{test_count}")
        assert train_count + val_count + test_count == total_cases
        
        # Check entity types
        entity_types = result['entity_types']
        print(f"✓ Entity types: {entity_types}")
        assert 'law' in entity_types
        assert 'crime' in entity_types
        assert 'penalty' in entity_types
        
        # Check data structure
        sample_case = result['train'][0] if result['train'] else result['val'][0]
        print(f"✓ Sample case ID: {sample_case['id']}")
        assert 'id' in sample_case
        assert 'fact' in sample_case
        assert 'accusation' in sample_case
        assert 'articles' in sample_case
        assert 'term_of_imprisonment' in sample_case
        
        # Check text cleaning
        assert len(sample_case['fact']) > 0
        assert sample_case['fact'].strip() == sample_case['fact']
        
        # Check statistics
        stats = result['statistics']
        print(f"✓ Statistics generated: {list(stats.keys())}")
        assert 'accusation_distribution' in stats
        assert 'article_distribution' in stats
        assert 'fact_length' in stats
        
        print("="*60)
        print("✓ All tests passed!")
        print("="*60)


def test_cail2019_loader_with_zip():
    """Test CAIL2019 loader with ZIP file."""
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Create mock data
        mock_cases = [
            {
                "id": "zip_case_001",
                "fact": "这是一个测试案例，用于验证ZIP文件加载功能。被告人在某地实施了违法行为。",
                "meta": {
                    "accusation": ["测试罪名"],
                    "relevant_articles": [100]
                }
            }
        ]
        
        # Create a temporary directory with JSON file
        data_dir = tmpdir / "cail2019_data"
        data_dir.mkdir()
        
        with open(data_dir / "data.json", 'w', encoding='utf-8') as f:
            json.dump(mock_cases, f, ensure_ascii=False)
        
        # Create ZIP file
        zip_path = tmpdir / "cail2019.zip"
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            zipf.write(data_dir / "data.json", "data.json")
        
        # Test loader with ZIP
        loader = CAIL2019Loader(str(zip_path))
        result = loader.load_and_clean()
        
        print("\n" + "="*60)
        print("ZIP Test Results")
        print("="*60)
        print(f"✓ Loaded {result['statistics']['total_cases']} cases from ZIP")
        assert result['statistics']['total_cases'] == 1
        print("✓ ZIP loading test passed!")
        print("="*60)


def test_text_cleaning():
    """Test text cleaning functionality."""
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Create cases with various text issues
        mock_cases = [
            {
                "id": "clean_001",
                "fact": "  这是一个有多余空格的文本  \n\n  需要清理  ",
                "meta": {
                    "accusation": ["  测试罪名  "],
                    "relevant_articles": ["123"]
                }
            }
        ]
        
        data_file = tmpdir / "data.json"
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(mock_cases, f, ensure_ascii=False)
        
        loader = CAIL2019Loader(str(tmpdir))
        result = loader.load_and_clean()
        
        # Get a case from any split
        if result['train']:
            case = result['train'][0]
        elif result['val']:
            case = result['val'][0]
        else:
            case = result['test'][0]
        
        print("\n" + "="*60)
        print("Text Cleaning Test Results")
        print("="*60)
        
        # Check fact cleaning
        print(f"Original fact had extra whitespace")
        print(f"Cleaned fact: '{case['fact']}'")
        assert case['fact'] == "这是一个有多余空格的文本 需要清理"
        print("✓ Fact text cleaned correctly")
        
        # Check accusation cleaning
        assert case['accusation'][0] == "测试罪名"
        print("✓ Accusation text cleaned correctly")
        
        # Check article conversion
        assert case['articles'][0] == 123
        print("✓ Articles converted to integers")
        
        print("="*60)
        print("✓ Text cleaning test passed!")
        print("="*60)


if __name__ == '__main__':
    print("\n" + "="*60)
    print("Running CAIL2019 Loader Tests")
    print("="*60)
    
    try:
        test_cail2019_loader_basic()
        test_cail2019_loader_with_zip()
        test_text_cleaning()
        
        print("\n" + "="*60)
        print("✓✓✓ ALL TESTS PASSED ✓✓✓")
        print("="*60)
        
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        raise
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        raise
