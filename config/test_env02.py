import os
from dotenv import load_dotenv
from openai import OpenAI

# 加载 .env 配置
load_dotenv()

# 初始化通义千问客户端
client = OpenAI(
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL")
)

# 1. 测试 LLM 对话
print("=== 测试 LLM 对话 ===")
try:
    chat_resp = client.chat.completions.create(
        model=os.getenv("LLM_MODEL"),
        messages=[{"role": "user", "content": "你好，请介绍一下自己"}]
    )
    print("✅ LLM 调用成功：")
    print(chat_resp.choices[0].message.content)
except Exception as e:
    print("❌ LLM 调用失败：", str(e))

print("\n=== 测试 Embedding 向量 ===")
# 2. 测试 Embedding
try:
    embed_resp = client.embeddings.create(
        model=os.getenv("EMBEDDING_MODEL"),
        input=["测试文本向量化"]
    )
    vec = embed_resp.data[0].embedding
    print(f"✅ Embedding 调用成功，向量维度：{len(vec)}")
except Exception as e:
    print("❌ Embedding 调用失败：", str(e))