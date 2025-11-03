"""
构建知识超图的脚本 - 使用 .env 配置文件
"""
import json
from functools import partial
from hypergraphrag import HyperGraphRAG
from hypergraphrag.llm import openai_embedding
from hypergraphrag.utils import EmbeddingFunc
from config import setup_environment


def main():
    # 加载并验证配置
    print("🔧 Loading configuration...")
    config = setup_environment()

    # 创建自定义 embedding 函数
    # 使用 partial 创建带参数的函数
    embedding_func = partial(
        openai_embedding.func,  # 获取原始函数
        **config.get_embedding_kwargs()
    )

    # 用 EmbeddingFunc 包装，保留 embedding_dim 属性
    custom_embedding = EmbeddingFunc(
        embedding_dim=openai_embedding.embedding_dim,
        max_token_size=openai_embedding.max_token_size,
        func=embedding_func
    )

    # 初始化 RAG 系统
    print("\n🚀 Initializing HyperGraphRAG...")
    rag = HyperGraphRAG(
        working_dir="expr/example",
        embedding_func=custom_embedding,
        llm_model_kwargs=config.get_llm_kwargs(),
        log_level=config.log_level
    )

    # 加载文档数据
    print("\n📚 Loading documents...")
    with open("example_contexts.json", mode="r", encoding="utf-8") as f:
        unique_contexts = json.load(f)

    print(f"   Found {len(unique_contexts)} documents")

    # 插入文档并构建知识图谱
    print("\n⚙️  Building knowledge hypergraph...")
    print("   This may take a while depending on the size of your documents...")
    rag.insert(unique_contexts)

    print("\n✅ Knowledge hypergraph construction completed!")
    print(f"   Working directory: expr/example")


if __name__ == "__main__":
    main()
