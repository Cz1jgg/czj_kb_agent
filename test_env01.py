# 测试 Python 环境 + 文件读写
import sys
import os

# 打印 Python 版本
print("Python 版本:", sys.version)

# 测试文件读写
test_file_path = "test.txt"

# 写入测试
with open(test_file_path, "w", encoding="utf-8") as f:
    f.write("czg_kb_agent 环境测试成功！Python 3.11.9 运行正常。")

# 读取测试
with open(test_file_path, "r", encoding="utf-8") as f:
    content = f.read()

print("文件读取结果:", content)

# 清理测试文件
os.remove(test_file_path)
print("测试文件已删除，环境验证完成 ✅")