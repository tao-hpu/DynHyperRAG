# -*- coding: utf-8 -*-
"""
Legal domain entity types and taxonomy for CAIL2019 dataset.
"""

from typing import Dict, List, Set
import re


class LegalEntityTaxonomy:
    """Legal entity taxonomy for Chinese legal domain (CAIL2019)."""
    
    # Core entity types as defined in CAIL2019Loader
    ENTITY_TYPES = ['law', 'article', 'court', 'party', 'crime', 'penalty']
    
    # Detailed entity type definitions
    ENTITY_DEFINITIONS = {
        'law': 'Legal statutes, regulations, and legal documents',
        'article': 'Specific articles or clauses within laws',
        'court': 'Courts, judicial institutions, and legal authorities',
        'party': 'Parties involved in legal proceedings',
        'crime': 'Criminal charges, accusations, and offense types',
        'penalty': 'Penalties, punishments, and legal sanctions'
    }
    
    # Keyword dictionaries for entity type recognition
    ENTITY_KEYWORDS = {
        'law': [
            '刑法', '民法', '行政法', '商法', '经济法', '劳动法', '婚姻法',
            '合同法', '物权法', '公司法', '证券法', '民事诉讼法', '刑事诉讼法',
            '法律', '法规', '条例', '规定', '办法', '细则'
        ],
        'article': [
            '第.*条', '条款', '款项', '规定', '条文', '法条',
            '第一条', '第二条', '第三条', '前款', '本款',
            '依据', '根据', '按照', '参照', '适用', '违反'
        ],
        'court': [
            '最高人民法院', '高级人民法院', '中级人民法院', '基层人民法院',
            '人民法院', '法院', '法庭', '审判庭', '合议庭',
            '人民检察院', '检察院', '公安机关', '司法机关'
        ],
        'party': [
            '原告', '被告', '第三人', '上诉人', '被上诉人', '申请人',
            '犯罪嫌疑人', '被告人', '被害人', '证人', '当事人',
            '法定代理人', '委托代理人', '辩护人', '债权人', '债务人'
        ],
        'crime': [
            '故意杀人罪', '故意伤害罪', '盗窃罪', '诈骗罪', '抢劫罪',
            '贪污罪', '受贿罪', '危险驾驶罪', '交通肇事罪',
            '犯罪', '罪名', '罪行', '违法行为', '刑事犯罪'
        ],
        'penalty': [
            '死刑', '无期徒刑', '有期徒刑', '拘役', '管制', '罚金',
            '剥夺政治权利', '没收财产', '缓刑', '假释', '减刑',
            '赔偿', '补偿', '违约金', '损害赔偿'
        ]
    }
    
    # Entity type priority for disambiguation
    ENTITY_PRIORITY = {
        'law': 1, 'article': 2, 'crime': 3, 
        'penalty': 4, 'court': 5, 'party': 6
    }
    
    def __init__(self):
        """Initialize the legal entity taxonomy."""
        self.compiled_patterns = {}
        for entity_type, keywords in self.ENTITY_KEYWORDS.items():
            patterns = []
            for keyword in keywords:
                if '.*' in keyword:
                    patterns.append(re.compile(keyword))
                else:
                    patterns.append(re.compile(re.escape(keyword)))
            self.compiled_patterns[entity_type] = patterns
    
    def identify_entity_types(self, text: str) -> Dict[str, float]:
        """Identify entity types in the given text."""
        scores = {entity_type: 0.0 for entity_type in self.ENTITY_TYPES}
        
        for entity_type, patterns in self.compiled_patterns.items():
            matches = 0
            for pattern in patterns:
                if pattern.search(text):
                    matches += 1
            
            if matches > 0:
                base_score = min(matches / len(patterns), 1.0)
                priority_bonus = (7 - self.ENTITY_PRIORITY[entity_type]) * 0.1
                scores[entity_type] = min(base_score + priority_bonus, 1.0)
        
        return scores
    
    def get_primary_entity_type(self, text: str, threshold: float = 0.3) -> str:
        """Get the primary entity type for the given text."""
        scores = self.identify_entity_types(text)
        max_score = max(scores.values())
        
        if max_score < threshold:
            return 'unknown'
        
        candidates = [et for et, score in scores.items() if score == max_score]
        if len(candidates) == 1:
            return candidates[0]
        
        candidates.sort(key=lambda x: self.ENTITY_PRIORITY[x])
        return candidates[0]
    
    def get_statistics(self) -> Dict:
        """Get statistics about the entity taxonomy."""
        return {
            'total_entity_types': len(self.ENTITY_TYPES),
            'total_keywords': sum(len(keywords) for keywords in self.ENTITY_KEYWORDS.values()),
            'keywords_per_type': {
                entity_type: len(keywords) 
                for entity_type, keywords in self.ENTITY_KEYWORDS.items()
            }
        }


# Global taxonomy instance
_taxonomy = None


def get_legal_taxonomy() -> LegalEntityTaxonomy:
    """Get or create global legal taxonomy instance."""
    global _taxonomy
    if _taxonomy is None:
        _taxonomy = LegalEntityTaxonomy()
    return _taxonomy


if __name__ == '__main__':
    # Test entity type identification
    taxonomy = get_legal_taxonomy()
    
    test_cases = [
        "根据刑法第二百三十二条规定，故意杀人的，处死刑、无期徒刑",
        "北京市第一中级人民法院审理认为",
        "被告人张某犯盗窃罪，判处有期徒刑三年",
        "原告李某与被告王某合同纠纷一案"
    ]
    
    print("Legal Entity Type Recognition Test:")
    print("=" * 50)
    
    for i, text in enumerate(test_cases, 1):
        print(f"\nTest case {i}: {text}")
        scores = taxonomy.identify_entity_types(text)
        primary_type = taxonomy.get_primary_entity_type(text)
        
        print(f"Primary type: {primary_type}")
        print("Scores:")
        for entity_type, score in sorted(scores.items(), key=lambda x: x[1], reverse=True):
            if score > 0:
                print(f"  {entity_type}: {score:.3f}")
    
    print(f"\nStatistics: {taxonomy.get_statistics()}")