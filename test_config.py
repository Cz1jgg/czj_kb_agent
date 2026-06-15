# test_config.py
from core.config_loader import settings

print("=== 配置测试 ===")
print("服务端口：", settings.server.port)
print("向量库路径：", settings.vector_store.path)
print("LLM 模型：", settings.llm.model)
print("API_KEY 是否配置：", "是" if settings.llm.api_key else "否")