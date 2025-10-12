# 安装问题解决方案

## hnswlib 编译失败问题

### 问题描述

在 macOS 上使用 pip 安装 hnswlib 时遇到编译错误：

```
fatal error: 'iostream' file not found
error: command '/usr/bin/clang++' failed with exit code 1
```

### 原因

C++ 标准库头文件缺失或路径配置问题。

### 解决方案

✅ **使用 conda 安装（推荐）**

```bash
conda install -c conda-forge hnswlib -y
```

这个方法会安装预编译的二进制包，不需要本地编译。

### 完整安装流程

```bash
# 1. 创建并激活环境
conda create -n hypergraphrag python=3.11
conda activate hypergraphrag

# 2. 先用 conda 安装 hnswlib
conda install -c conda-forge hnswlib -y

# 3. 再安装其他依赖
pip install -r requirements-compatible.txt
```

### 其他可能的解决方案

#### 方案 1：设置编译器环境变量

```bash
export CXXFLAGS="-stdlib=libc++"
export LDFLAGS="-stdlib=libc++"
pip install hnswlib --no-cache-dir
```

#### 方案 2：重新安装 Xcode Command Line Tools

```bash
sudo rm -rf /Library/Developer/CommandLineTools
xcode-select --install
```

#### 方案 3：跳过 hnswlib，使用其他向量数据库

编辑 `requirements-compatible.txt`，删除 `hnswlib` 行，然后配置 HyperGraphRAG 使用其他向量存储：

```python
rag = HyperGraphRAG(
    working_dir="expr/example",
    vector_storage="NanoVectorDBStorage"  # 不需要 hnswlib
)
```

## 验证安装

安装完成后，验证 hnswlib 是否可用：

```bash
python -c "import hnswlib; print('hnswlib version:', hnswlib.__version__)"
```

预期输出：
```
hnswlib version: 0.8.0
```

## 其他常见问题

### numpy 版本冲突

如果遇到 numpy 版本问题，conda 会自动处理依赖关系。

### torch 安装问题

参考主文档 [SETUP.md](./SETUP.md) 中的 torch 安装说明。

## 推荐的完整安装步骤

```bash
# 创建环境
conda create -n hypergraphrag python=3.11
conda activate hypergraphrag

# 安装需要编译的包（使用 conda）
conda install -c conda-forge hnswlib -y

# 安装其他依赖
cd HyperGraphRAG
pip install -r requirements-compatible.txt

# 验证安装
python -c "from hypergraphrag import HyperGraphRAG; print('OK')"
```

## 依赖包说明

通过 conda 安装的包（预编译）：
- hnswlib - 向量相似度搜索库
- numpy - 数值计算（conda 版本可能更稳定）

通过 pip 安装的包：
- torch - 深度学习框架
- transformers - NLP 模型库
- openai - OpenAI API 客户端
- 其他纯 Python 包

## 相关资源

- [QUICKSTART.md](./QUICKSTART.md) - 快速开始指南
- [SETUP.md](./SETUP.md) - 详细安装说明
- hnswlib GitHub: https://github.com/nmslib/hnswlib
