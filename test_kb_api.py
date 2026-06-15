#!/usr/bin/env python3
# =========================================
#  知识库 API 测试脚本
#  测试目标：http://127.0.0.1:8000
#  测试接口：kb/list, kb/upload, kb/rebuild
# =========================================
import os
import sys
import json
import tempfile
from datetime import datetime
from typing import Dict, Any, Optional

try:
    import requests
except ImportError:
    print("❌ 请先安装 requests 库：pip install requests")
    sys.exit(1)

# 配置
API_BASE = "http://127.0.0.1:8000"
TEST_FILE_CONTENT = """# 测试文档

这是一个用于测试知识库上传功能的临时文档。

## 第一章：测试内容

知识库系统需要支持以下功能：
1. 文件上传
2. 文档解析
3. 文本分块
4. 向量入库

## 第二章：测试数据

测试数据包含多个段落，用于验证分块功能是否正常工作。

每个段落应该被正确分割，并且能够被向量检索到。

## 第三章：结束

测试完成！
"""

# 测试结果统计
test_results = []


def log_result(name: str, passed: bool, message: str = "", response: Optional[Dict] = None):
    """记录测试结果"""
    test_results.append({
        "name": name,
        "passed": passed,
        "message": message,
        "response": response
    })


def print_request(method: str, url: str, status_code: int, response: Dict = None):
    """打印请求信息"""
    print(f"\n{'='*60}")
    print(f"请求方法: {method}")
    print(f"请求 URL: {url}")
    print(f"状态码: {status_code}")
    if response is not None:
        print(f"响应结果: {json.dumps(response, ensure_ascii=False, indent=2)}")
    print(f"{'='*60}")


def test_kb_list():
    """测试 GET /api/v1/kb/list 接口"""
    url = f"{API_BASE}/api/v1/kb/list"
    print(f"\n📋 测试接口: GET /api/v1/kb/list")
    
    try:
        response = requests.get(url, timeout=30)
        print_request("GET", url, response.status_code, response.json())
        
        if response.status_code == 200:
            data = response.json()
            if "code" in data and data["code"] == 200:
                log_result("kb/list", True, "成功获取文档列表")
                print(f"✅ 测试通过 - 当前文档数: {data.get('data', {}).get('total', 0)}")
            else:
                log_result("kb/list", False, f"接口返回错误码: {data.get('code')}, 消息: {data.get('message')}")
                print(f"❌ 测试失败 - {data.get('message')}")
        else:
            log_result("kb/list", False, f"HTTP 错误码: {response.status_code}")
            print(f"❌ 测试失败 - HTTP 状态码: {response.status_code}")
    
    except requests.exceptions.ConnectionError:
        msg = "连接失败：服务可能未启动或端口不正确"
        log_result("kb/list", False, msg)
        print(f"❌ 测试失败 - {msg}")
    except requests.exceptions.Timeout:
        msg = "请求超时"
        log_result("kb/list", False, msg)
        print(f"❌ 测试失败 - {msg}")
    except Exception as e:
        msg = f"未知错误: {type(e).__name__}: {e}"
        log_result("kb/list", False, msg)
        print(f"❌ 测试失败 - {msg}")


def test_kb_upload():
    """测试 POST /api/v1/kb/upload 接口"""
    url = f"{API_BASE}/api/v1/kb/upload"
    print(f"\n📤 测试接口: POST /api/v1/kb/upload")
    
    # 创建临时测试文件
    temp_file = None
    try:
        # 创建临时 .md 文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
            f.write(TEST_FILE_CONTENT)
            temp_file = f.name
        
        print(f"已创建临时测试文件: {temp_file}")
        
        # 读取文件并上传
        with open(temp_file, 'rb') as f:
            files = {'file': ('test_document.md', f, 'text/markdown')}
            response = requests.post(url, files=files, timeout=60)
        
        print_request("POST", url, response.status_code, response.json())
        
        if response.status_code == 200:
            data = response.json()
            if "code" in data and data["code"] == 200:
                log_result("kb/upload", True, "文件上传成功")
                print(f"✅ 测试通过 - 文件名: {data.get('data', {}).get('filename')}, 分块数: {data.get('data', {}).get('chunk_count')}")
            else:
                log_result("kb/upload", False, f"接口返回错误码: {data.get('code')}, 消息: {data.get('message')}")
                print(f"❌ 测试失败 - {data.get('message')}")
        else:
            log_result("kb/upload", False, f"HTTP 错误码: {response.status_code}")
            print(f"❌ 测试失败 - HTTP 状态码: {response.status_code}")
    
    except requests.exceptions.ConnectionError:
        msg = "连接失败：服务可能未启动或端口不正确"
        log_result("kb/upload", False, msg)
        print(f"❌ 测试失败 - {msg}")
    except requests.exceptions.Timeout:
        msg = "请求超时"
        log_result("kb/upload", False, msg)
        print(f"❌ 测试失败 - {msg}")
    except Exception as e:
        msg = f"未知错误: {type(e).__name__}: {e}"
        log_result("kb/upload", False, msg)
        print(f"❌ 测试失败 - {msg}")
    finally:
        # 清理临时文件
        if temp_file and os.path.exists(temp_file):
            os.unlink(temp_file)
            print(f"已清理临时测试文件: {temp_file}")


def test_kb_rebuild():
    """测试 POST /api/v1/kb/rebuild 接口"""
    url = f"{API_BASE}/api/v1/kb/rebuild"
    print(f"\n🔄 测试接口: POST /api/v1/kb/rebuild")
    
    try:
        response = requests.post(url, params={'clear_existing': True}, timeout=120)
        print_request("POST", url, response.status_code, response.json())
        
        if response.status_code == 200:
            data = response.json()
            if "code" in data and data["code"] == 200:
                log_result("kb/rebuild", True, "索引重建成功")
                print(f"✅ 测试通过 - 总文档数: {data.get('data', {}).get('total_docs')}, 总分块数: {data.get('data', {}).get('total_chunks')}")
            else:
                log_result("kb/rebuild", False, f"接口返回错误码: {data.get('code')}, 消息: {data.get('message')}")
                print(f"❌ 测试失败 - {data.get('message')}")
        else:
            log_result("kb/rebuild", False, f"HTTP 错误码: {response.status_code}")
            print(f"❌ 测试失败 - HTTP 状态码: {response.status_code}")
    
    except requests.exceptions.ConnectionError:
        msg = "连接失败：服务可能未启动或端口不正确"
        log_result("kb/rebuild", False, msg)
        print(f"❌ 测试失败 - {msg}")
    except requests.exceptions.Timeout:
        msg = "请求超时（重建索引可能需要较长时间）"
        log_result("kb/rebuild", False, msg)
        print(f"❌ 测试失败 - {msg}")
    except Exception as e:
        msg = f"未知错误: {type(e).__name__}: {e}"
        log_result("kb/rebuild", False, msg)
        print(f"❌ 测试失败 - {msg}")


def print_summary():
    """打印测试结果汇总"""
    print("\n" + "="*70)
    print("📊 测试结果汇总")
    print("="*70)
    
    passed = sum(1 for r in test_results if r["passed"])
    failed = sum(1 for r in test_results if not r["passed"])
    total = len(test_results)
    
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"测试接口: {total} 个")
    print(f"✅ 通过: {passed} 个")
    print(f"❌ 失败: {failed} 个")
    print(f"通过率: {passed/total*100:.1f}%")
    
    print("\n📋 详细结果:")
    for i, result in enumerate(test_results, 1):
        status = "✅" if result["passed"] else "❌"
        print(f"{i}. {status} {result['name']}")
        if not result["passed"]:
            print(f"   失败原因: {result['message']}")
    
    print("="*70)
    
    if failed > 0:
        sys.exit(1)


def main():
    """主函数"""
    print("="*70)
    print("🚀 知识库 API 测试脚本")
    print("="*70)
    print(f"测试目标: {API_BASE}")
    print(f"测试接口: kb/list, kb/upload, kb/rebuild")
    print("="*70)
    
    # 执行测试
    test_kb_list()   # 先获取当前文档列表（上传前）
    test_kb_upload() # 上传测试文件
    test_kb_rebuild() # 重建索引
    test_kb_list()   # 再次获取文档列表（上传后）
    
    # 输出汇总
    print_summary()


if __name__ == "__main__":
    main()
