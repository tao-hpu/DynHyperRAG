"""CAIL2019 legal dataset loader with data cleaning pipeline.

This module provides functionality to load, clean, and prepare the CAIL2019
(China AI and Law 2019) legal case dataset for use with DynHyperRAG.

The CAIL2019 dataset contains Chinese legal cases with:
- Case facts (事实描述)
- Accusations/charges (罪名)
- Relevant law articles (法条)
- Term of imprisonment (刑期)
"""

import json
import logging
import os
import re
import zipfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class CAIL2019Loader:
    """CAIL2019 dataset loader with data cleaning and preprocessing.
    
    This class handles:
    1. Extracting data from ZIP archives
    2. Reading and parsing JSON files
    3. Cleaning and normalizing text
    4. Filtering corrupted or invalid records
    5. Splitting data into train/validation/test sets
    
    Attributes:
        data_path: Path to the CAIL2019 ZIP file or directory
        entity_types: List of legal entity types for this domain
    """
    
    # Legal entity types for CAIL2019 domain
    ENTITY_TYPES = ['law', 'article', 'court', 'party', 'crime', 'penalty']
    
    def __init__(self, data_path: str):
        """Initialize the CAIL2019 loader.
        
        Args:
            data_path: Path to CAIL2019 ZIP file or extracted directory
        """
        self.data_path = Path(data_path)
        self.entity_types = self.ENTITY_TYPES
        
        if not self.data_path.exists():
            raise FileNotFoundError(f"Data path not found: {data_path}")
    
    def load_and_clean(self, output_dir: Optional[str] = None) -> Dict[str, any]:
        """Load and clean the CAIL2019 dataset.
        
        This is the main entry point that orchestrates the entire pipeline:
        1. Extract ZIP if needed
        2. Load JSON files
        3. Clean and validate cases
        4. Split into train/val/test sets
        5. Generate statistics
        
        Args:
            output_dir: Optional directory to save cleaned data
            
        Returns:
            Dictionary containing:
                - train: List of training cases
                - val: List of validation cases
                - test: List of test cases
                - entity_types: List of entity types for this domain
                - statistics: Dataset statistics
        """
        logger.info(f"Loading CAIL2019 dataset from {self.data_path}")
        
        # Step 1: Extract or locate data files
        data_dir = self._extract_or_locate_data()
        
        # Step 2: Load JSON files
        logger.info("Loading JSON files...")
        raw_cases = self._load_json_files(data_dir)
        logger.info(f"Loaded {len(raw_cases)} raw cases")
        
        # Step 3: Clean and validate
        logger.info("Cleaning and validating cases...")
        cleaned_cases = self._clean_and_validate(raw_cases)
        logger.info(f"Cleaned cases: {len(cleaned_cases)} (filtered {len(raw_cases) - len(cleaned_cases)})")
        
        # Step 4: Split dataset
        logger.info("Splitting dataset...")
        train, val, test = self._split_dataset(cleaned_cases, [0.7, 0.15, 0.15])
        logger.info(f"Split: train={len(train)}, val={len(val)}, test={len(test)}")
        
        # Step 5: Generate statistics
        statistics = self._generate_statistics(cleaned_cases, train, val, test)
        
        # Step 6: Save if output directory specified
        if output_dir:
            self._save_cleaned_data(output_dir, train, val, test, statistics)
        
        result = {
            'train': train,
            'val': val,
            'test': test,
            'entity_types': self.entity_types,
            'statistics': statistics
        }
        
        logger.info("CAIL2019 dataset loading complete")
        return result
    
    def _extract_or_locate_data(self) -> Path:
        """Extract ZIP file or locate existing data directory.
        
        Returns:
            Path to directory containing JSON files
        """
        if self.data_path.is_dir():
            logger.info(f"Using existing directory: {self.data_path}")
            return self.data_path
        
        if self.data_path.suffix == '.zip':
            logger.info(f"Extracting ZIP file: {self.data_path}")
            extract_dir = self.data_path.parent / 'temp_cail2019'
            extract_dir.mkdir(exist_ok=True)
            
            with zipfile.ZipFile(self.data_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            
            logger.info(f"Extracted to: {extract_dir}")
            return extract_dir
        
        raise ValueError(f"Invalid data path: {self.data_path}. Must be ZIP file or directory.")
    
    def _load_json_files(self, data_dir: Path) -> List[Dict]:
        """Load all JSON files from the data directory.
        
        Args:
            data_dir: Directory containing JSON files
            
        Returns:
            List of raw case dictionaries
        """
        cases = []
        
        # Find all JSON files recursively
        json_files = list(data_dir.rglob('*.json'))
        
        if not json_files:
            logger.warning(f"No JSON files found in {data_dir}")
            return cases
        
        logger.info(f"Found {len(json_files)} JSON files")
        
        for json_file in json_files:
            try:
                # Check if this is a large file that needs streaming
                file_size = json_file.stat().st_size
                use_streaming = file_size > 100 * 1024 * 1024  # 100MB threshold
                
                if use_streaming:
                    logger.info(f"Using streaming parser for large file {json_file.name} ({file_size / 1024 / 1024:.1f}MB)")
                    parsed_cases = self._load_large_json_file(json_file)
                    cases.extend(parsed_cases)
                else:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        
                        # Detect and handle different data formats
                        detected_format = self._detect_data_format(data, json_file)
                        logger.info(f"Detected format '{detected_format}' for {json_file.name}")
                        
                        if detected_format == 'cail2019_reading_comprehension':
                            # Handle CAIL2019 reading comprehension format
                            parsed_cases = self._parse_cail2019_reading_comprehension(data, json_file)
                            cases.extend(parsed_cases)
                        elif detected_format == 'legacy_sample':
                            # Handle legacy sample data format (backward compatibility)
                            parsed_cases = self._parse_legacy_format(data, json_file)
                            cases.extend(parsed_cases)
                        else:
                            logger.warning(f"Unknown data format in {json_file}")
                        
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON file {json_file}: {e}")
                self._log_json_error(json_file, e)
            except Exception as e:
                logger.error(f"Error loading {json_file}: {e}")
                self._log_json_error(json_file, e)
        
        return cases
    
    def _detect_data_format(self, data: Dict, json_file: Path) -> str:
        """Detect the format of the JSON data.
        
        Args:
            data: Parsed JSON data
            json_file: Path to the JSON file
            
        Returns:
            String indicating the detected format
        """
        # Check for CAIL2019 reading comprehension format
        if (isinstance(data, dict) and 
            'version' in data and 
            'data' in data and 
            isinstance(data['data'], list)):
            
            # Further validate the structure
            if data['data'] and isinstance(data['data'][0], dict):
                first_item = data['data'][0]
                if ('paragraphs' in first_item and 
                    'caseid' in first_item and 
                    'domain' in first_item):
                    return 'cail2019_reading_comprehension'
        
        # Check for legacy sample format (existing format)
        if isinstance(data, list):
            if data and isinstance(data[0], dict):
                first_item = data[0]
                if 'fact' in first_item or 'meta' in first_item:
                    return 'legacy_sample'
        elif isinstance(data, dict):
            if 'fact' in data or 'meta' in data:
                return 'legacy_sample'
        
        return 'unknown'
    
    def _parse_cail2019_reading_comprehension(self, data: Dict, json_file: Path) -> List[Dict]:
        """Parse CAIL2019 reading comprehension format data.
        
        The format is: {"version": "1.0", "data": [{"paragraphs": [...], "caseid": "...", "domain": "..."}]}
        
        Args:
            data: Parsed JSON data in CAIL2019 reading comprehension format
            json_file: Path to the JSON file
            
        Returns:
            List of parsed case dictionaries
        """
        cases = []
        
        try:
            version = data.get('version', 'unknown')
            logger.debug(f"Processing CAIL2019 data version {version}")
            
            for case_data in data['data']:
                caseid = case_data.get('caseid', '')
                domain = case_data.get('domain', 'unknown')
                
                # Process each paragraph in the case
                for paragraph in case_data.get('paragraphs', []):
                    casename = paragraph.get('casename', '')
                    context = paragraph.get('context', '')
                    qas = paragraph.get('qas', [])
                    
                    # Extract and structure Q&A metadata
                    structured_qas = self._structure_qas_metadata(qas)
                    
                    # Create a case record
                    case = {
                        'id': caseid,
                        'casename': casename,
                        'fact': context,  # Map context to fact for compatibility
                        'domain': domain,
                        'task_type': 'reading_comprehension',
                        'qas': structured_qas,  # Store structured Q&A pairs as metadata
                        'source_file': json_file.name,
                        'data_format': 'cail2019_reading_comprehension',
                        'version': version
                    }
                    
                    cases.append(case)
                    
        except Exception as e:
            logger.error(f"Error parsing CAIL2019 reading comprehension data from {json_file}: {e}")
        
        return cases
    
    def _structure_qas_metadata(self, qas: List[Dict]) -> List[Dict]:
        """Structure Q&A pairs into metadata format.
        
        Args:
            qas: List of question-answer pairs
            
        Returns:
            List of structured Q&A metadata
        """
        structured = []
        
        for qa in qas:
            question = qa.get('question', '')
            is_impossible = qa.get('is_impossible', 'false')
            qa_id = qa.get('id', '')
            answers = qa.get('answers', [])
            
            # Structure answer information
            structured_answers = []
            for answer in answers:
                structured_answers.append({
                    'text': answer.get('text', ''),
                    'answer_start': answer.get('answer_start', -1)
                })
            
            structured_qa = {
                'id': qa_id,
                'question': question,
                'is_impossible': is_impossible == 'true',
                'answers': structured_answers,
                'answer_count': len(structured_answers)
            }
            
            structured.append(structured_qa)
        
        return structured
    
    def _load_large_json_file(self, json_file: Path) -> List[Dict]:
        """Load large JSON files using streaming approach.
        
        This method handles large files like big_train_data.json by processing
        them in chunks to avoid memory issues.
        
        Args:
            json_file: Path to the large JSON file
            
        Returns:
            List of parsed case dictionaries
        """
        cases = []
        
        try:
            import ijson  # Import here to make it optional
            
            with open(json_file, 'rb') as f:
                # Parse the JSON structure incrementally
                parser = ijson.parse(f)
                
                current_case = {}
                current_paragraph = {}
                current_qa = {}
                current_answer = {}
                
                path_stack = []
                
                for prefix, event, value in parser:
                    if event == 'start_map':
                        if prefix == 'data.item':
                            current_case = {}
                        elif prefix.endswith('.paragraphs.item'):
                            current_paragraph = {}
                        elif prefix.endswith('.qas.item'):
                            current_qa = {}
                        elif prefix.endswith('.answers.item'):
                            current_answer = {}
                    
                    elif event == 'end_map':
                        if prefix == 'data.item':
                            # Process completed case
                            if current_case:
                                processed_case = self._process_streaming_case(current_case, json_file)
                                if processed_case:
                                    cases.extend(processed_case)
                        elif prefix.endswith('.paragraphs.item'):
                            # Add paragraph to current case
                            if 'paragraphs' not in current_case:
                                current_case['paragraphs'] = []
                            current_case['paragraphs'].append(current_paragraph.copy())
                        elif prefix.endswith('.qas.item'):
                            # Add Q&A to current paragraph
                            if 'qas' not in current_paragraph:
                                current_paragraph['qas'] = []
                            current_paragraph['qas'].append(current_qa.copy())
                        elif prefix.endswith('.answers.item'):
                            # Add answer to current Q&A
                            if 'answers' not in current_qa:
                                current_qa['answers'] = []
                            current_qa['answers'].append(current_answer.copy())
                    
                    elif event in ('string', 'number', 'boolean'):
                        # Store primitive values
                        if prefix.startswith('data.item.'):
                            field = prefix.split('.')[-1]
                            if field in ['caseid', 'domain']:
                                current_case[field] = value
                        elif prefix.endswith('.paragraphs.item.casename'):
                            current_paragraph['casename'] = value
                        elif prefix.endswith('.paragraphs.item.context'):
                            current_paragraph['context'] = value
                        elif prefix.endswith('.qas.item.question'):
                            current_qa['question'] = value
                        elif prefix.endswith('.qas.item.is_impossible'):
                            current_qa['is_impossible'] = value
                        elif prefix.endswith('.qas.item.id'):
                            current_qa['id'] = value
                        elif prefix.endswith('.answers.item.text'):
                            current_answer['text'] = value
                        elif prefix.endswith('.answers.item.answer_start'):
                            current_answer['answer_start'] = value
                    
                    # Progress logging for large files
                    if len(cases) % 1000 == 0 and len(cases) > 0:
                        logger.info(f"Processed {len(cases)} cases from {json_file.name}")
                        
        except ImportError:
            logger.warning("ijson not available, falling back to regular JSON loading")
            # Fallback to regular JSON loading
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                detected_format = self._detect_data_format(data, json_file)
                if detected_format == 'cail2019_reading_comprehension':
                    cases = self._parse_cail2019_reading_comprehension(data, json_file)
                    
        except Exception as e:
            logger.error(f"Error in streaming parse of {json_file}: {e}")
            # Fallback to regular JSON loading
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    detected_format = self._detect_data_format(data, json_file)
                    if detected_format == 'cail2019_reading_comprehension':
                        cases = self._parse_cail2019_reading_comprehension(data, json_file)
            except Exception as fallback_e:
                logger.error(f"Fallback parsing also failed for {json_file}: {fallback_e}")
        
        return cases
    
    def _process_streaming_case(self, case_data: Dict, json_file: Path) -> List[Dict]:
        """Process a single case from streaming parser.
        
        Args:
            case_data: Case data from streaming parser
            json_file: Source JSON file
            
        Returns:
            List of processed case dictionaries
        """
        cases = []
        
        try:
            caseid = case_data.get('caseid', '')
            domain = case_data.get('domain', 'unknown')
            
            # Process each paragraph in the case
            for paragraph in case_data.get('paragraphs', []):
                casename = paragraph.get('casename', '')
                context = paragraph.get('context', '')
                qas = paragraph.get('qas', [])
                
                # Extract and structure Q&A metadata
                structured_qas = self._structure_qas_metadata(qas)
                
                # Create a case record
                case = {
                    'id': caseid,
                    'casename': casename,
                    'fact': context,  # Map context to fact for compatibility
                    'domain': domain,
                    'task_type': 'reading_comprehension',
                    'qas': structured_qas,  # Store structured Q&A pairs as metadata
                    'source_file': json_file.name,
                    'data_format': 'cail2019_reading_comprehension'
                }
                
                cases.append(case)
                
        except Exception as e:
            logger.error(f"Error processing streaming case: {e}")
        
        return cases
    
    def _log_json_error(self, json_file: Path, error: Exception):
        """Log detailed information about JSON parsing errors.
        
        Args:
            json_file: Path to the problematic JSON file
            error: The exception that occurred
        """
        try:
            # Try to read first few lines to diagnose the issue
            with open(json_file, 'r', encoding='utf-8') as f:
                first_lines = []
                for i, line in enumerate(f):
                    if i >= 5:  # Read first 5 lines
                        break
                    first_lines.append(line.strip()[:100])  # Truncate long lines
            
            logger.error(f"JSON Error Details for {json_file.name}:")
            logger.error(f"  Error: {error}")
            logger.error(f"  File size: {json_file.stat().st_size} bytes")
            logger.error(f"  First few lines: {first_lines}")
            
        except Exception as log_error:
            logger.error(f"Could not read file details for {json_file}: {log_error}")
    
    def _parse_legacy_format(self, data: Dict, json_file: Path) -> List[Dict]:
        """Parse legacy sample data format for backward compatibility.
        
        Args:
            data: Parsed JSON data in legacy format
            json_file: Path to the JSON file
            
        Returns:
            List of parsed case dictionaries
        """
        cases = []
        
        try:
            # Handle both single object and array formats
            if isinstance(data, list):
                for case in data:
                    case['source_file'] = json_file.name
                    case['data_format'] = 'legacy_sample'
                    cases.append(case)
            elif isinstance(data, dict):
                data['source_file'] = json_file.name
                data['data_format'] = 'legacy_sample'
                cases.append(data)
                
        except Exception as e:
            logger.error(f"Error parsing legacy format data from {json_file}: {e}")
        
        return cases
    
    def _clean_and_validate(self, raw_cases: List[Dict]) -> List[Dict]:
        """Clean and validate case records.
        
        Args:
            raw_cases: List of raw case dictionaries
            
        Returns:
            List of cleaned and validated cases
        """
        cleaned_cases = []
        
        for i, case in enumerate(raw_cases):
            try:
                # Validate case
                if not self._is_valid_case(case):
                    continue
                
                # Clean case
                cleaned = self._clean_case(case)
                
                # Add index if not present
                if 'id' not in cleaned or not cleaned['id']:
                    cleaned['id'] = f"case_{i:06d}"
                
                cleaned_cases.append(cleaned)
                
            except Exception as e:
                logger.debug(f"Error processing case {i}: {e}")
                continue
        
        return cleaned_cases
    
    def _is_valid_case(self, case: Dict) -> bool:
        """Validate if a case record is valid.
        
        A valid case must have:
        - 'fact' field with non-empty text (minimum 50+ characters for CAIL2019)
        - Proper encoding and format
        
        Args:
            case: Case dictionary
            
        Returns:
            True if valid, False otherwise
        """
        try:
            # Check required fields
            if 'fact' not in case:
                return False
            
            # Check fact is non-empty string
            fact = case.get('fact', '')
            if not isinstance(fact, str) or not fact.strip():
                return False
            
            # Enhanced length validation - CAIL2019 cases should have substantial content
            cleaned_fact = fact.strip()
            data_format = case.get('data_format', 'legacy_sample')
            
            if data_format == 'cail2019_reading_comprehension':
                # CAIL2019 reading comprehension requires minimum 50 characters
                if len(cleaned_fact) < 50:
                    logger.debug(f"Case {case.get('id', 'unknown')} rejected: context too short ({len(cleaned_fact)} chars)")
                    return False
            else:
                # Legacy format minimum 10 characters
                if len(cleaned_fact) < 10:
                    return False
            
            # Validate encoding - check for corrupted characters
            if self._has_encoding_issues(cleaned_fact):
                logger.debug(f"Case {case.get('id', 'unknown')} rejected: encoding issues detected")
                return False
            
            # Check for legal entity mentions (basic validation)
            if data_format == 'cail2019_reading_comprehension':
                if not self._has_legal_content(cleaned_fact):
                    logger.debug(f"Case {case.get('id', 'unknown')} rejected: no legal content detected")
                    return False
            
            return True
            
        except Exception as e:
            logger.debug(f"Validation error for case {case.get('id', 'unknown')}: {e}")
            return False
    
    def _has_encoding_issues(self, text: str) -> bool:
        """Check if text has encoding issues.
        
        Args:
            text: Text to check
            
        Returns:
            True if encoding issues detected
        """
        # Check for common encoding issue patterns
        encoding_issues = [
            '\ufffd',  # Replacement character
            '锟斤拷',   # Common Chinese encoding issue
            '烫烫烫',   # Debug pattern
            '屯屯屯',   # Another debug pattern
        ]
        
        for issue in encoding_issues:
            if issue in text:
                return True
        
        # Check for excessive control characters
        control_char_count = sum(1 for c in text if ord(c) < 32 and c not in '\n\t\r')
        if control_char_count > len(text) * 0.01:  # More than 1% control characters
            return True
        
        return False
    
    def _has_legal_content(self, text: str) -> bool:
        """Check if text contains legal content indicators.
        
        Args:
            text: Text to check
            
        Returns:
            True if legal content detected
        """
        # Legal keywords in Chinese
        legal_keywords = [
            '法院', '法官', '判决', '审理', '被告', '原告', '起诉', '诉讼',
            '合同', '协议', '违约', '赔偿', '损失', '责任', '权利', '义务',
            '刑法', '民法', '行政', '犯罪', '罪名', '刑期', '罚金', '缓刑',
            '证据', '事实', '认定', '查明', '当事人', '申请人', '第三人',
            '法条', '条款', '规定', '法律', '法规', '司法', '执行'
        ]
        
        text_lower = text.lower()
        found_keywords = sum(1 for keyword in legal_keywords if keyword in text_lower)
        
        # Require at least 2 legal keywords for validation
        return found_keywords >= 2
    
    def _clean_case(self, case: Dict) -> Dict:
        """Clean a single case record.
        
        Cleaning operations:
        - Normalize whitespace
        - Remove control characters
        - Standardize encoding
        - Extract and structure metadata
        
        Args:
            case: Raw case dictionary
            
        Returns:
            Cleaned case dictionary
        """
        cleaned = {}
        
        # Clean ID
        cleaned['id'] = str(case.get('id', '')).strip()
        
        # Clean fact text
        fact = case.get('fact', '')
        cleaned['fact'] = self._clean_text(fact)
        
        # Extract metadata
        meta = case.get('meta', {})
        if not isinstance(meta, dict):
            meta = {}
        
        # Clean accusation (罪名)
        accusation = meta.get('accusation', [])
        if isinstance(accusation, str):
            accusation = [accusation]
        elif not isinstance(accusation, list):
            accusation = []
        cleaned['accusation'] = [self._clean_text(a) for a in accusation if a]
        
        # Clean relevant articles (法条)
        articles = meta.get('relevant_articles', [])
        if isinstance(articles, (int, str)):
            articles = [articles]
        elif not isinstance(articles, list):
            articles = []
        cleaned['articles'] = [int(a) if isinstance(a, (int, str)) and str(a).isdigit() else str(a) 
                               for a in articles if a]
        
        # Clean term of imprisonment (刑期)
        term = meta.get('term_of_imprisonment', {})
        if isinstance(term, dict):
            cleaned['term_of_imprisonment'] = {
                'death_penalty': term.get('death_penalty', False),
                'life_imprisonment': term.get('life_imprisonment', False),
                'imprisonment': term.get('imprisonment', 0)
            }
        else:
            cleaned['term_of_imprisonment'] = {
                'death_penalty': False,
                'life_imprisonment': False,
                'imprisonment': 0
            }
        
        # Add any additional metadata fields
        for key in ['criminals', 'punish_of_money']:
            if key in meta:
                cleaned[key] = meta[key]
        
        return cleaned
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text with enhanced Chinese text processing.
        
        Operations:
        - Strip whitespace
        - Normalize whitespace (multiple spaces to single)
        - Remove control characters
        - Remove special unicode characters
        - Enhanced Chinese text normalization
        
        Args:
            text: Raw text
            
        Returns:
            Cleaned text
        """
        if not isinstance(text, str):
            return str(text)
        
        # Strip leading/trailing whitespace
        text = text.strip()
        
        # Remove control characters (except newline, tab, and carriage return)
        text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]', '', text)
        
        # Remove zero-width characters and other invisible characters
        text = re.sub(r'[\u200b-\u200f\ufeff\u2060\u180e]', '', text)
        
        # Remove byte order marks
        text = text.replace('\ufeff', '')
        
        # Normalize Chinese punctuation
        chinese_punct_map = {
            '，': '，',  # Full-width comma
            '。': '。',  # Full-width period
            '；': '；',  # Full-width semicolon
            '：': '：',  # Full-width colon
            '？': '？',  # Full-width question mark
            '！': '！',  # Full-width exclamation mark
            '"': '"',   # Left double quotation mark
            '"': '"',   # Right double quotation mark
            '\u2018': '\u2018',   # Left single quotation mark
            '\u2019': '\u2019',   # Right single quotation mark
            '（': '（', # Full-width left parenthesis
            '）': '）', # Full-width right parenthesis
            '【': '【', # Left black lenticular bracket
            '】': '】', # Right black lenticular bracket
        }
        
        for old_punct, new_punct in chinese_punct_map.items():
            text = text.replace(old_punct, new_punct)
        
        # Normalize whitespace (including Chinese spaces)
        text = re.sub(r'[\s\u3000]+', ' ', text)
        
        # Remove HTML entities if present
        import html
        text = html.unescape(text)
        
        # Remove common encoding artifacts
        encoding_artifacts = ['锟斤拷', '烫烫烫', '屯屯屯']
        for artifact in encoding_artifacts:
            text = text.replace(artifact, '')
        
        # Final cleanup
        text = text.strip()
        
        return text
    
    def _split_dataset(self, cases: List[Dict], 
                      ratios: List[float]) -> Tuple[List[Dict], List[Dict], List[Dict]]:
        """Split dataset into train/validation/test sets with stratification.
        
        Args:
            cases: List of case dictionaries
            ratios: List of [train_ratio, val_ratio, test_ratio]
            
        Returns:
            Tuple of (train_cases, val_cases, test_cases)
        """
        import random
        
        # Ensure reproducibility
        random.seed(42)
        
        # Group cases by domain and task type for stratified splitting
        grouped_cases = {}
        for case in cases:
            domain = case.get('domain', 'unknown')
            task_type = case.get('task_type', 'unknown')
            data_format = case.get('data_format', 'legacy_sample')
            
            key = f"{domain}_{task_type}_{data_format}"
            if key not in grouped_cases:
                grouped_cases[key] = []
            grouped_cases[key].append(case)
        
        logger.info(f"Splitting {len(cases)} cases across {len(grouped_cases)} groups")
        
        train, val, test = [], [], []
        
        # Split each group proportionally
        for group_key, group_cases in grouped_cases.items():
            # Shuffle within group
            shuffled = group_cases.copy()
            random.shuffle(shuffled)
            
            # Calculate split indices
            n = len(shuffled)
            train_end = int(n * ratios[0])
            val_end = train_end + int(n * ratios[1])
            
            group_train = shuffled[:train_end]
            group_val = shuffled[train_end:val_end]
            group_test = shuffled[val_end:]
            
            train.extend(group_train)
            val.extend(group_val)
            test.extend(group_test)
            
            logger.debug(f"Group {group_key}: {len(group_train)} train, {len(group_val)} val, {len(group_test)} test")
        
        # Final shuffle to mix groups
        random.shuffle(train)
        random.shuffle(val)
        random.shuffle(test)
        
        return train, val, test
    
    def _generate_statistics(self, all_cases: List[Dict],
                           train: List[Dict],
                           val: List[Dict],
                           test: List[Dict]) -> Dict:
        """Generate comprehensive dataset statistics.
        
        Args:
            all_cases: All cleaned cases
            train: Training cases
            val: Validation cases
            test: Test cases
            
        Returns:
            Dictionary of comprehensive statistics
        """
        stats = {
            'total_cases': len(all_cases),
            'train_cases': len(train),
            'val_cases': len(val),
            'test_cases': len(test),
            'entity_types': self.entity_types,
            'split_ratios': {
                'train': len(train) / len(all_cases) if all_cases else 0,
                'val': len(val) / len(all_cases) if all_cases else 0,
                'test': len(test) / len(all_cases) if all_cases else 0
            }
        }
        
        # Multi-task and domain statistics
        domain_counts = {}
        task_type_counts = {}
        data_format_counts = {}
        
        for case in all_cases:
            domain = case.get('domain', 'unknown')
            task_type = case.get('task_type', 'unknown')
            data_format = case.get('data_format', 'legacy_sample')
            
            domain_counts[domain] = domain_counts.get(domain, 0) + 1
            task_type_counts[task_type] = task_type_counts.get(task_type, 0) + 1
            data_format_counts[data_format] = data_format_counts.get(data_format, 0) + 1
        
        stats['domain_distribution'] = dict(sorted(domain_counts.items(), key=lambda x: x[1], reverse=True))
        stats['task_type_distribution'] = dict(sorted(task_type_counts.items(), key=lambda x: x[1], reverse=True))
        stats['data_format_distribution'] = dict(sorted(data_format_counts.items(), key=lambda x: x[1], reverse=True))
        
        # Legacy format statistics (for backward compatibility)
        if any(case.get('data_format') == 'legacy_sample' for case in all_cases):
            # Accusation distribution
            accusation_counts = {}
            for case in all_cases:
                if case.get('data_format') == 'legacy_sample':
                    for acc in case.get('accusation', []):
                        accusation_counts[acc] = accusation_counts.get(acc, 0) + 1
            
            if accusation_counts:
                stats['accusation_distribution'] = dict(sorted(
                    accusation_counts.items(), 
                    key=lambda x: x[1], 
                    reverse=True
                )[:20])  # Top 20
            
            # Article distribution
            article_counts = {}
            for case in all_cases:
                if case.get('data_format') == 'legacy_sample':
                    for art in case.get('articles', []):
                        article_counts[str(art)] = article_counts.get(str(art), 0) + 1
            
            if article_counts:
                stats['article_distribution'] = dict(sorted(
                    article_counts.items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:20])  # Top 20
        
        # CAIL2019 reading comprehension statistics
        cail2019_cases = [case for case in all_cases if case.get('data_format') == 'cail2019_reading_comprehension']
        if cail2019_cases:
            # Case name distribution
            casename_counts = {}
            for case in cail2019_cases:
                casename = case.get('casename', 'unknown')
                casename_counts[casename] = casename_counts.get(casename, 0) + 1
            
            stats['casename_distribution'] = dict(sorted(
                casename_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:20])  # Top 20
            
            # Q&A statistics
            total_questions = 0
            impossible_questions = 0
            answer_lengths = []
            
            for case in cail2019_cases:
                qas = case.get('qas', [])
                total_questions += len(qas)
                
                for qa in qas:
                    if qa.get('is_impossible', False):
                        impossible_questions += 1
                    
                    for answer in qa.get('answers', []):
                        answer_text = answer.get('text', '')
                        if answer_text:
                            answer_lengths.append(len(answer_text))
            
            stats['qa_statistics'] = {
                'total_questions': total_questions,
                'impossible_questions': impossible_questions,
                'answerable_questions': total_questions - impossible_questions,
                'impossible_rate': impossible_questions / total_questions if total_questions > 0 else 0,
                'avg_questions_per_case': total_questions / len(cail2019_cases) if cail2019_cases else 0
            }
            
            if answer_lengths:
                stats['answer_length_statistics'] = {
                    'mean': sum(answer_lengths) / len(answer_lengths),
                    'min': min(answer_lengths),
                    'max': max(answer_lengths),
                    'total_answers': len(answer_lengths)
                }
        
        # Text length statistics
        fact_lengths = [len(case['fact']) for case in all_cases if case.get('fact')]
        if fact_lengths:
            import statistics
            stats['fact_length_statistics'] = {
                'mean': statistics.mean(fact_lengths),
                'median': statistics.median(fact_lengths),
                'min': min(fact_lengths),
                'max': max(fact_lengths),
                'std_dev': statistics.stdev(fact_lengths) if len(fact_lengths) > 1 else 0
            }
        
        # Split statistics by domain and task type
        stats['split_by_domain'] = {}
        for domain in domain_counts.keys():
            domain_train = len([c for c in train if c.get('domain') == domain])
            domain_val = len([c for c in val if c.get('domain') == domain])
            domain_test = len([c for c in test if c.get('domain') == domain])
            
            stats['split_by_domain'][domain] = {
                'train': domain_train,
                'val': domain_val,
                'test': domain_test,
                'total': domain_train + domain_val + domain_test
            }
        
        stats['split_by_task_type'] = {}
        for task_type in task_type_counts.keys():
            task_train = len([c for c in train if c.get('task_type') == task_type])
            task_val = len([c for c in val if c.get('task_type') == task_type])
            task_test = len([c for c in test if c.get('task_type') == task_type])
            
            stats['split_by_task_type'][task_type] = {
                'train': task_train,
                'val': task_val,
                'test': task_test,
                'total': task_train + task_val + task_test
            }
        
        return stats
    
    def _save_cleaned_data(self, output_dir: str,
                          train: List[Dict],
                          val: List[Dict],
                          test: List[Dict],
                          statistics: Dict):
        """Save cleaned data to output directory.
        
        Args:
            output_dir: Output directory path
            train: Training cases
            val: Validation cases
            test: Test cases
            statistics: Dataset statistics
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Save splits
        with open(output_path / 'train.json', 'w', encoding='utf-8') as f:
            json.dump(train, f, ensure_ascii=False, indent=2)
        
        with open(output_path / 'val.json', 'w', encoding='utf-8') as f:
            json.dump(val, f, ensure_ascii=False, indent=2)
        
        with open(output_path / 'test.json', 'w', encoding='utf-8') as f:
            json.dump(test, f, ensure_ascii=False, indent=2)
        
        # Save statistics
        with open(output_path / 'statistics.json', 'w', encoding='utf-8') as f:
            json.dump(statistics, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Cleaned data saved to {output_path}")
    
    def filter_by_criteria(self, cases: List[Dict], 
                          domain: Optional[str] = None,
                          task_type: Optional[str] = None,
                          data_format: Optional[str] = None) -> List[Dict]:
        """Filter cases by specified criteria.
        
        Args:
            cases: List of case dictionaries
            domain: Filter by domain (e.g., 'civil', 'criminal')
            task_type: Filter by task type (e.g., 'reading_comprehension')
            data_format: Filter by data format (e.g., 'cail2019_reading_comprehension')
            
        Returns:
            Filtered list of cases
        """
        filtered_cases = cases
        
        if domain:
            filtered_cases = [c for c in filtered_cases if c.get('domain') == domain]
            logger.info(f"Filtered by domain '{domain}': {len(filtered_cases)} cases")
        
        if task_type:
            filtered_cases = [c for c in filtered_cases if c.get('task_type') == task_type]
            logger.info(f"Filtered by task_type '{task_type}': {len(filtered_cases)} cases")
        
        if data_format:
            filtered_cases = [c for c in filtered_cases if c.get('data_format') == data_format]
            logger.info(f"Filtered by data_format '{data_format}': {len(filtered_cases)} cases")
        
        return filtered_cases


def main():
    """Example usage of CAIL2019Loader."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python cail2019_loader.py <path_to_cail2019_zip_or_dir> [output_dir]")
        sys.exit(1)
    
    data_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else None
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Load and clean data
    loader = CAIL2019Loader(data_path)
    result = loader.load_and_clean(output_dir)
    
    # Print summary
    print("\n" + "="*60)
    print("CAIL2019 Dataset Loading Summary")
    print("="*60)
    print(f"Total cases: {result['statistics']['total_cases']}")
    print(f"Train: {result['statistics']['train_cases']}")
    print(f"Val: {result['statistics']['val_cases']}")
    print(f"Test: {result['statistics']['test_cases']}")
    print(f"\nEntity types: {', '.join(result['entity_types'])}")
    print(f"\nTop 5 accusations:")
    for acc, count in list(result['statistics']['accusation_distribution'].items())[:5]:
        print(f"  - {acc}: {count}")
    print("="*60)


if __name__ == '__main__':
    main()
