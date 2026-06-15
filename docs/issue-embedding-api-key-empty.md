# 问题记录：EmbeddingConfig 未读取 ARK_API_KEY

## 发生时间
2026-06-15

## 问题描述

在验证 `core/vector_store.py` 模块时，`EmbeddingConfig.api_key` 始终为空字符串，导致向量库无法初始化。报错信息：

```
❌ Embedding API Key 未配置（请在 .env 中设置 ARK_API_KEY 或 OPENAI_API_KEY）
```

## 排查过程

### 1. 确认 `.env` 文件存在且 Key 正确

```powershell
# 直接用 dotenv 加载，变量能读到
python -c "from dotenv import load_dotenv; import os; load_dotenv('.env'); print(os.getenv('ARK_API_KEY'))"
# 输出：***  ✅
```

### 2. 检查 settings.env dict

```python
s = get_settings(reload=True)
print(s.env)
# 输出：
# {
#     'ARK_API_KEY': '***',  ✅
#     'llm.api_key': 'ark-c0740fd7-...',  ✅
#     'embeddings.api_key': '',           ❌ 为空！
# }
```

### 3. 根因定位

对比两个 dataclass 的 `__post_init__`：

```python
# LLMConfig — ✅ 有 ARK_API_KEY
class LLMConfig:
    def __post_init__(self) -> None:
        self.api_key = os.getenv("ARK_API_KEY", "").strip()  # ✅
        if not self.api_key:
            self.api_key = os.getenv("OPENAI_API_KEY", "").strip()

# EmbeddingConfig — ❌ 漏了 ARK_API_KEY
class EmbeddingConfig:
    def __post_init__(self) -> None:
        self.api_key = os.getenv("DASHSCOPE_API_KEY", "").strip()  # ❌ 写错了！
        or os.getenv("OPENAI_API_KEY", "").strip()
```

**根因**：`EmbeddingConfig` 中的 API Key 读取逻辑只有 `DASHSCOPE_API_KEY` 和 `OPENAI_API_KEY`，漏掉了 `ARK_API_KEY`，导致即使 `.env` 中填写了 `ARK_API_KEY`，向量模型也拿不到。

## 修复方案

在 `core/config_loader.py` 的 `EmbeddingConfig.__post_init__` 中补充 `ARK_API_KEY` 读取：

```python
class EmbeddingConfig:
    def __post_init__(self) -> None:
        if os.getenv("EMBEDDING_MODEL", "").strip():
            self.model = os.getenv("EMBEDDING_MODEL", "").strip()
        # Embedding API Key：火山方舟 ARK > OpenAI
        self.api_key = os.getenv("ARK_API_KEY", "").strip() or os.getenv(
            "OPENAI_API_KEY", ""
        ).strip()
```

## 修复后验证

```powershell
python -m core.vector_store
# 输出：
# INFO: VectorStoreManager 初始化完成
# embeddings_model: text-embedding-v2
# ✅ VectorStoreManager 已初始化
```

## 教训

**配置类字段（如 API Key）的来源必须保持一致。**

新增一个 API Key 来源时（如 `ARK_API_KEY`），需要在所有使用该 Key 的配置类中同步添加，不能只在一个地方加。否则只有 `LLMConfig` 能读到，向量模型 (`EmbeddingConfig`) 始终为空。

建议后续修改配置加载时，用统一方法读取 Key：

```python
def _get_llm_api_key() -> str:
    return os.getenv("ARK_API_KEY", "") or os.getenv("OPENAI_API_KEY", "")

# 所有 Config 共用同一读取函数
```
