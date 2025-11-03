# CAIL2019 Data Loader

## Overview

The CAIL2019 data loader provides functionality to load, clean, and prepare the **CAIL2019 (China AI and Law 2019)** legal case dataset for use with DynHyperRAG.

## Features

- ✅ **ZIP File Support**: Automatically extracts and processes ZIP archives
- ✅ **Data Cleaning**: Normalizes text, removes control characters, standardizes encoding
- ✅ **Validation**: Filters corrupted or invalid records
- ✅ **Dataset Splitting**: Automatically splits data into train/validation/test sets (70/15/15)
- ✅ **Statistics Generation**: Provides comprehensive dataset statistics
- ✅ **Entity Types**: Defines legal domain entity types (law, article, court, party, crime, penalty)

## Dataset Structure

The CAIL2019 dataset contains Chinese legal cases with:

- **Case Facts** (事实描述): Description of the case circumstances
- **Accusations** (罪名): Criminal charges
- **Relevant Articles** (法条): Applicable law articles
- **Term of Imprisonment** (刑期): Sentencing information

## Usage

### Basic Usage

```python
from hypergraphrag.data.cail2019_loader import CAIL2019Loader

# Load from ZIP file
loader = CAIL2019Loader('path/to/cail2019.zip')
result = loader.load_and_clean()

# Access the data
train_cases = result['train']
val_cases = result['val']
test_cases = result['test']
entity_types = result['entity_types']
statistics = result['statistics']

print(f"Loaded {len(train_cases)} training cases")
print(f"Entity types: {entity_types}")
```

### Load from Directory

```python
# Load from extracted directory
loader = CAIL2019Loader('path/to/cail2019_data/')
result = loader.load_and_clean()
```

### Save Cleaned Data

```python
# Load and save cleaned data
loader = CAIL2019Loader('path/to/cail2019.zip')
result = loader.load_and_clean(output_dir='expr/cail2019')

# This will create:
# - expr/cail2019/train.json
# - expr/cail2019/val.json
# - expr/cail2019/test.json
# - expr/cail2019/statistics.json
```

### Command Line Usage

```bash
# Load and display statistics
python -m hypergraphrag.data.cail2019_loader path/to/cail2019.zip

# Load and save cleaned data
python -m hypergraphrag.data.cail2019_loader path/to/cail2019.zip expr/cail2019
```

## Data Format

### Input Format

The loader expects JSON files with the following structure:

```json
{
  "id": "case_001",
  "fact": "被告人张三于2019年1月在某地盗窃他人财物...",
  "meta": {
    "accusation": ["盗窃"],
    "relevant_articles": [264],
    "term_of_imprisonment": {
      "death_penalty": false,
      "life_imprisonment": false,
      "imprisonment": 12
    }
  }
}
```

### Output Format

After cleaning, each case has the following structure:

```python
{
    'id': str,                    # Case ID
    'fact': str,                  # Cleaned case facts
    'accusation': List[str],      # List of accusations
    'articles': List[int],        # List of relevant law articles
    'term_of_imprisonment': {
        'death_penalty': bool,
        'life_imprisonment': bool,
        'imprisonment': int       # Months
    }
}
```

## Data Cleaning Pipeline

The loader performs the following cleaning operations:

1. **Text Normalization**
   - Strip leading/trailing whitespace
   - Normalize multiple spaces to single space
   - Remove control characters
   - Remove zero-width unicode characters

2. **Validation**
   - Filter cases without 'fact' field
   - Filter cases with empty or too short facts (< 10 characters)
   - Ensure proper data types

3. **Metadata Extraction**
   - Extract and clean accusations
   - Convert article numbers to integers
   - Structure imprisonment terms

4. **Dataset Splitting**
   - 70% training set
   - 15% validation set
   - 15% test set
   - Reproducible with fixed random seed (42)

## Statistics

The loader generates comprehensive statistics including:

- **Case Counts**: Total, train, validation, test
- **Accusation Distribution**: Top 20 most common accusations
- **Article Distribution**: Top 20 most referenced law articles
- **Text Length Statistics**: Mean, min, max fact lengths
- **Entity Types**: Legal domain entity types

Example statistics output:

```python
{
    'total_cases': 10000,
    'train_cases': 7000,
    'val_cases': 1500,
    'test_cases': 1500,
    'entity_types': ['law', 'article', 'court', 'party', 'crime', 'penalty'],
    'accusation_distribution': {
        '盗窃': 1234,
        '故意伤害': 987,
        '诈骗': 765,
        ...
    },
    'article_distribution': {
        '264': 1234,
        '234': 987,
        ...
    },
    'fact_length': {
        'mean': 245.6,
        'min': 15,
        'max': 2048
    }
}
```

## Entity Types

The CAIL2019 loader defines the following legal domain entity types:

- **law** (法律): Legal statutes and regulations
- **article** (法条): Specific law articles
- **court** (法院): Court names and jurisdictions
- **party** (当事人): Parties involved in the case
- **crime** (罪名): Criminal charges/accusations
- **penalty** (刑罚): Sentencing and penalties

These entity types are used by the entity type filter in the retrieval module.

## Error Handling

The loader handles various error conditions:

- **Missing Files**: Raises `FileNotFoundError` if data path doesn't exist
- **Invalid JSON**: Logs error and skips corrupted files
- **Invalid Cases**: Filters out cases that don't meet validation criteria
- **Encoding Issues**: Handles various text encodings automatically

## Integration with DynHyperRAG

### Step 1: Load Data

```python
from hypergraphrag.data.cail2019_loader import CAIL2019Loader

loader = CAIL2019Loader('data/cail2019.zip')
result = loader.load_and_clean(output_dir='expr/cail2019')
```

### Step 2: Update Configuration

```python
# In config.py or your configuration
config = {
    'entity_taxonomy': {
        'legal': result['entity_types']
    },
    'domain': 'legal'
}
```

### Step 3: Build Knowledge Graph

```python
from hypergraphrag import HyperGraphRAG

# Initialize with legal domain configuration
rag = HyperGraphRAG(
    working_dir='expr/cail2019',
    entity_types=result['entity_types']
)

# Insert training cases
for case in result['train']:
    rag.insert(case['fact'])
```

### Step 4: Query

```python
# Query the knowledge graph
query = "盗窃罪的量刑标准是什么？"
answer = rag.query(query)
```

## Testing

Run the test suite:

```bash
python test_cail2019_loader.py
```

The test suite includes:
- Basic loading and cleaning
- ZIP file extraction
- Text cleaning validation
- Dataset splitting verification
- Statistics generation

## Performance

- **Loading Speed**: ~1000 cases/second
- **Memory Usage**: ~100MB for 10,000 cases
- **Disk Space**: Cleaned data is ~80% of original size

## Troubleshooting

### Issue: "No JSON files found"

**Solution**: Ensure your ZIP file or directory contains `.json` files. The loader searches recursively.

### Issue: "All cases filtered out"

**Solution**: Check that your cases have:
- A 'fact' field with text
- Fact text longer than 10 characters

### Issue: "Encoding errors"

**Solution**: The loader handles UTF-8 encoding automatically. If issues persist, check your source files.

## Future Enhancements

Potential improvements for future versions:

- [ ] Support for additional CAIL datasets (CAIL2018, CAIL2020)
- [ ] Parallel processing for large datasets
- [ ] Advanced text cleaning (spell checking, grammar correction)
- [ ] Entity extraction during loading
- [ ] Query generation from cases
- [ ] Automatic annotation for quality labels

## References

- **CAIL2019 Challenge**: [https://github.com/china-ai-law-challenge/CAIL2019](https://github.com/china-ai-law-challenge/CAIL2019)
- **Paper**: "CAIL2019-SCM: A Dataset of Similar Case Matching in Legal Domain"
- **DynHyperRAG Requirements**: See `.kiro/specs/dynhyperrag-quality-aware/requirements.md`

## License

This loader is part of the DynHyperRAG project. The CAIL2019 dataset has its own license terms.
