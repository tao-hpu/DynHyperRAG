# GitHub Actions 同步配置说明

## ⚠️ 重要提示

**此文件仅供本地参考，不会被同步到朋友的 repo**

## 配置步骤

### 1. 获取朋友的 GitHub Personal Access Token

让你的朋友创建一个 token：
1. 访问 GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
2. 点击 "Generate new token (classic)"
3. 设置权限：勾选 `repo` (完整的仓库访问权限)
4. 生成并复制 token

### 2. 在你的 repo 中添加 Secret

1. 进入你的 repo → Settings → Secrets and variables → Actions
2. 点击 "New repository secret"
3. Name: `FRIEND_REPO_TOKEN`
4. Value: 粘贴朋友提供的 token
5. 点击 "Add secret"

### 3. 修改工作流配置

编辑 `.github/workflows/sync-to-friend-repo.yml`，替换以下内容：

```yaml
repository: friend-username/friend-repo  # 改为朋友的实际 repo 路径
git config user.name "Friend Name"       # 改为朋友的 GitHub 用户名
git config user.email "friend@example.com"  # 改为朋友的 GitHub 邮箱
```

### 4. 测试同步

提交代码到 main 分支，或者手动触发：
1. 进入 Actions 标签页
2. 选择 "Sync Code to Friend Repo"
3. 点击 "Run workflow"

## 同步规则

### ✅ 会被同步的内容
- 所有代码文件
- 配置文件
- 文档
- 数据文件

### ❌ 不会被同步的内容
- `.git/` 目录（Git 历史）
- `.github/` 目录（GitHub Actions 配置）
- `.kiro/` 目录（IDE 配置）
- `.claude/` 目录（IDE 配置）
- `.vscode/` 目录（IDE 配置）
- 其他 `.gitignore` 中的文件

## 工作原理

1. 每次推送到 main 分支时自动触发
2. 使用 rsync 同步代码（排除敏感目录）
3. 以朋友的身份提交到他的 repo
4. 只在有变化时才提交

## 安全性

- 所有提交都显示为朋友的身份
- 你的信息不会出现在朋友的 repo 中
- `.github` 目录不会被同步，朋友看不到这个工作流
- Token 安全存储在 GitHub Secrets 中

## 故障排查

### 同步失败
- 检查 FRIEND_REPO_TOKEN 是否正确设置
- 确认 token 有 repo 权限
- 确认朋友的 repo 路径正确

### 权限错误
- 让朋友重新生成 token 并确保勾选了 `repo` 权限
- 更新 Secret 中的 token

### 提交显示错误的作者
- 检查工作流中的 user.name 和 user.email 是否正确
