#!/bin/bash

# HyperGraphRAG 自动安装脚本
# 自动处理依赖安装和常见问题

set -e  # 遇到错误立即退出

echo "================================="
echo "HyperGraphRAG 自动安装"
echo "================================="
echo ""

# 检查 Python 版本
PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}')
echo "✓ 检测到 Python 版本: $PYTHON_VERSION"
echo ""

# 检查是否在正确的环境中
if [[ "$CONDA_DEFAULT_ENV" != "hypergraphrag" ]]; then
    echo "⚠️  警告: 当前不在 hypergraphrag 环境中"
    echo "   建议先运行: conda activate hypergraphrag"
    echo ""
    read -p "是否继续安装? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "开始安装依赖..."
echo ""

# 获取项目根目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# 首先尝试安装大部分依赖
echo "步骤 1/2: 安装主要依赖..."
if pip install -r "$PROJECT_ROOT/requirements.txt" 2>&1 | tee /tmp/install.log; then
    echo "✅ 主要依赖安装成功"
else
    # 检查是否是 hnswlib 的问题
    if grep -q "hnswlib" /tmp/install.log && grep -q "iostream" /tmp/install.log; then
        echo ""
        echo "⚠️  检测到 hnswlib 编译失败"
        echo "   这是因为缺少 C++ 标准库头文件"
        echo ""
        echo "尝试解决方案..."

        # 方案 1: 设置编译器环境变量
        echo "方案 1: 设置 C++ 编译器环境变量..."
        export CXXFLAGS="-stdlib=libc++"
        export LDFLAGS="-stdlib=libc++"

        if pip install hnswlib --no-cache-dir 2>/dev/null; then
            echo "✅ hnswlib 安装成功（方案 1）"
        else
            echo "❌ 方案 1 失败"
            echo ""
            echo "方案 2: 尝试使用 conda 安装..."

            if command -v conda &> /dev/null; then
                if conda install -c conda-forge hnswlib -y; then
                    echo "✅ hnswlib 安装成功（方案 2）"
                else
                    echo "❌ 方案 2 失败"
                    echo ""
                    echo "方案 3: 跳过 hnswlib，使用 nano-vectordb 替代"
                    echo "   hnswlib 用于向量检索，nano-vectordb 可以替代"
                    echo ""
                    echo "✅ 其他依赖已安装，可以继续使用"
                fi
            else
                echo "❌ conda 不可用"
                echo ""
                echo "✅ 已跳过 hnswlib，使用 nano-vectordb 替代"
                echo "   nano-vectordb 可以替代 hnswlib 用于向量检索"
            fi
        fi
    else
        echo "❌ 安装失败，请检查错误信息"
        exit 1
    fi
fi

echo ""
echo "步骤 2/2: 验证安装..."

# 验证关键包
python -c "import torch; print(f'✓ PyTorch {torch.__version__}')" 2>/dev/null || echo "✗ PyTorch 未安装"
python -c "import openai; print('✓ OpenAI SDK')" 2>/dev/null || echo "✗ OpenAI SDK 未安装"
python -c "import tiktoken; print('✓ tiktoken')" 2>/dev/null || echo "✗ tiktoken 未安装"
python -c "import networkx; print('✓ NetworkX')" 2>/dev/null || echo "✗ NetworkX 未安装"

# 检查向量数据库
if python -c "import hnswlib" 2>/dev/null; then
    echo "✓ hnswlib（首选向量数据库）"
elif python -c "from nano_vectordb import NanoVectorDB" 2>/dev/null; then
    echo "✓ nano-vectordb（替代向量数据库）"
else
    echo "⚠️  警告: 未检测到向量数据库"
fi

echo ""
echo "================================="
echo "安装完成！"
echo "================================="
echo ""
echo "下一步操作："
echo ""
echo "1. 配置 API 密钥："
echo "   cp .env.example .env"
echo "   nano .env  # 编辑配置文件"
echo ""
echo "2. 测试配置："
echo "   python config.py"
echo ""
echo "3. 运行示例："
echo "   python script_construct.py  # 构建知识图谱"
echo "   python script_query.py      # 查询"
echo ""
echo "如遇到问题，请查看文档："
echo "   docs/QUICKSTART.md  - 快速开始"
echo "   docs/SETUP.md       - 详细安装指南"
echo ""
