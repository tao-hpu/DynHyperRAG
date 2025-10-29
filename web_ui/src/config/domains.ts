/**
 * 领域配置 - 支持多个数据集的可视化
 */

export interface DomainConfig {
  name: string;
  displayName: string;
  entityTypes: string[];
  colors: Record<string, string>;
  description: string;
}

export const DOMAIN_CONFIGS: Record<string, DomainConfig> = {
  medical: {
    name: 'medical',
    displayName: '医疗领域',
    entityTypes: ['disease', 'symptom', 'treatment', 'drug', 'test'],
    colors: {
      disease: '#ef4444',
      symptom: '#f59e0b',
      treatment: '#10b981',
      drug: '#3b82f6',
      test: '#8b5cf6',
    },
    description: '医疗健康知识图谱（示例数据）',
  },
  
  legal: {
    name: 'legal',
    displayName: '法律领域',
    entityTypes: ['law', 'article', 'court', 'party', 'crime', 'penalty'],
    colors: {
      law: '#dc2626',
      article: '#ea580c',
      court: '#ca8a04',
      party: '#16a34a',
      crime: '#0891b2',
      penalty: '#7c3aed',
    },
    description: 'CAIL2019 法律案例知识图谱',
  },
  
  academic: {
    name: 'academic',
    displayName: '学术领域',
    entityTypes: ['paper', 'author', 'institution', 'keyword', 'conference'],
    colors: {
      paper: '#2563eb',
      author: '#7c3aed',
      institution: '#db2777',
      keyword: '#059669',
      conference: '#d97706',
    },
    description: 'PubMed/AMiner 学术论文知识图谱',
  },
};

/**
 * 默认领域（可通过环境变量配置）
 */
export const DEFAULT_DOMAIN = process.env.REACT_APP_DEFAULT_DOMAIN || 'legal';

/**
 * 获取当前领域配置
 */
export function getCurrentDomainConfig(): DomainConfig {
  return DOMAIN_CONFIGS[DEFAULT_DOMAIN] || DOMAIN_CONFIGS.legal;
}

/**
 * 获取实体类型颜色
 */
export function getEntityTypeColor(entityType: string, domain?: string): string {
  const domainConfig = domain ? DOMAIN_CONFIGS[domain] : getCurrentDomainConfig();
  return domainConfig.colors[entityType.toLowerCase()] || '#6b7280';
}
