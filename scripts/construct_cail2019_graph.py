#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
构建 CAIL2019 知识超图的脚本
"""
import json
import sys
from pathlib import Path
from functools import partial

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def main():
    print("🔧 准备构建 CAIL2019 知识超图...")
    
    # 检查数据文件
    cail2019_dir = project_root / "expr" / "cail2019"
    train_file = cail2019_dir / "train.json"
    
    if not train_file.exists():
        print(f"❌ 训练数据文件不存在: {train_file}")
        print("请先运行数据迁移脚本")
        return False
    
    # 加载配置
    try:
        from config import setup_environment
        config = setup_environment()
        print("✅ 配置加载成功")
    except Exception as e:
        print(f"❌ 配置加载失败: {e}")
        return False
    
    # 加载训练数据
    print(f"\n📚 加载 CAIL2019 训练数据...")
    try:
        with open(train_file, 'r', encoding='utf-8') as f:
            train_data = json.load(f)
        
        print(f"   加载了 {len(train_data)} 个案例")
        
        # 提取文本内容用于构建知识图谱
        contexts = []
        for case in train_data[:100]:  # 先用前100个案例测试
            fact = case.get('fact', '')
            if fact and len(fact) > 50:  # 确保有足够的内容
                contexts.append(fact)
        
        print(f"   提取了 {len(contexts)} 个有效文本")
        
        # 保存为 contexts 文件
        contexts_file = cail2019_dir / "contexts.json"
        with open(contexts_file, 'w', encoding='utf-8') as f:
            json.dump(contexts, f, ensure_ascii=False, indent=2)
        
        print(f"   保存到: {contexts_file}")
        
    except Exception as e:
        print(f"❌ 数据加载失败: {e}")
        return False
    
    # 构建知识图谱
    print(f"\n⚙️  构建知识超图...")
    try:
        # 导入必要的模块
        from hypergraphrag import HyperGraphRAG
        from hypergraphrag.llm import openai_embedding
        from hypergraphrag.utils import EmbeddingFunc
        
        # 创建 embedding 函数
        embedding_func = partial(
            openai_embedding.func,
            **config.get_embedding_kwargs()
        )
        
        custom_embedding = EmbeddingFunc(
            embedding_dim=openai_embedding.embedding_dim,
            max_token_size=openai_embedding.max_token_size,
            func=embedding_func
        )
        
        # 初始化 RAG 系统
        rag = HyperGraphRAG(
            working_dir=str(cail2019_dir),
            embedding_func=custom_embedding,
            llm_model_kwargs=config.get_llm_kwargs(),
            log_level=config.log_level
        )
        
        # 插入文档并构建知识图谱
        print("   开始构建超图（这可能需要一些时间）...")
        rag.insert(contexts)
        
        print("✅ 知识超图构建完成!")
        
    except Exception as e:
        print(f"❌ 知识图谱构建失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 验证构建结果
    print(f"\n🔍 验证构建结果...")
    try:
        # 检查生成的文件
        graph_files = list(cail2019_dir.glob("*.json"))
        print(f"   生成的文件: {[f.name for f in graph_files]}")
        
        # 简单查询测试
        test_query = "什么是集资诈骗罪？"
        print(f"\n🧪 测试查询: {test_query}")
        
        result = rag.query(test_query)
        print(f"   查询结果长度: {len(result)}")
        print(f"   结果预览: {result[:200]}...")
        
    except Exception as e:
        print(f"⚠️  验证过程出现问题: {e}")
        # 不返回 False，因为构建可能已经成功
    
    print(f"\n✅ CAIL2019 知识超图构建完成!")
    print(f"   工作目录: {cail2019_dir}")
    print(f"   可以使用 script_query.py 进行查询测试")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)