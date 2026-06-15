from core.document_parser import parse_file
from core.text_splitter import split_documents
from core.vector_store import VectorStoreManager

# 初始化向量库管理器
vs_manager = VectorStoreManager()
# 解析文档
docs = parse_file("data/documents/test.txt")
# 文本分块
chunks = split_documents(docs)
# 新增文档到向量库
vs_manager.add_documents(chunks)
# 保存向量库
vs_manager.save()
# 打印存储路径
print("入库完成，向量库路径：", vs_manager.store_dir)