"""
查询知识超图的脚本 - 使用 .env 配置文件
"""
from functools import partial
from hypergraphrag import HyperGraphRAG, QueryParam
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

    # 初始化 RAG 系统（使用已存在的工作目录）
    print("\n🚀 Initializing HyperGraphRAG...")
    rag = HyperGraphRAG(
        working_dir="expr/example",
        embedding_func=custom_embedding,
        llm_model_kwargs=config.get_llm_kwargs(),
        log_level=config.log_level
    )

    # 定义查询
    query_text = '''How strong is the evidence supporting a systolic BP target
of 120–129 mmHg in elderly or frail patients, considering potential risks
like orthostatic hypotension, the balance between cardiovascular benefits
and adverse effects, and the feasibility of implementation in diverse
healthcare settings?'''

    print("\n🔍 Querying knowledge base...")
    print(f"   Query: {query_text[:100]}...")

    # 执行查询
    result = rag.query(query_text, param=QueryParam(
        mode="hybrid",  # 可选: local, global, hybrid, naive
        top_k=60,
        max_token_for_text_unit=4000,
        max_token_for_local_context=4000,
        max_token_for_global_context=4000
    ))

    # 输出结果
    print("\n📝 Query Result:")
    print("=" * 80)
    print(result)
    print("=" * 80)


if __name__ == "__main__":
    main()
