"""
一键运行所有测试脚本
"""
import subprocess
import sys
from pathlib import Path

# 测试脚本列表（按执行顺序）
TEST_SCRIPTS = [
    "01_test_basic_api.py",
    "02_test_conversation.py",
    "03_test_pin_and_tags.py",
    "04_test_full_flow.py",
    "05_test_new_features.py"
]

# 颜色输出
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    ENDC = '\033[0m'

def print_header(text):
    print(f"\n{Colors.BLUE}{'='*50}{Colors.ENDC}")
    print(f"{Colors.BLUE}{text:^50}{Colors.ENDC}")
    print(f"{Colors.BLUE}{'='*50}{Colors.ENDC}\n")

def run_test(script_path):
    """运行单个测试脚本"""
    print(f"{Colors.YELLOW}运行: {script_path.name}{Colors.ENDC}")
    print("-" * 40)

    result = subprocess.run(
        [sys.executable, str(script_path)],
        capture_output=False,
        text=True
    )

    if result.returncode == 0:
        print(f"{Colors.GREEN}[PASS] {script_path.name} 通过{Colors.ENDC}\n")
        return True
    else:
        print(f"{Colors.RED}[FAIL] {script_path.name} 失败{Colors.ENDC}\n")
        return False

def main():
    print_header("聊天模块测试套件")

    # 检查服务器是否运行
    print(f"{Colors.YELLOW}检查服务器状态...{Colors.ENDC}")
    try:
        import httpx
        httpx.get("http://localhost:9099/login", timeout=2)
        print(f"{Colors.GREEN}[PASS] 服务器运行中{Colors.ENDC}\n")
    except:
        print(f"{Colors.RED}[FAIL] 服务器未启动！{Colors.ENDC}")
        print(f"请先运行: python start_server.py\n")
        return

    # 获取测试目录
    test_dir = Path(__file__).parent

    # 运行所有测试
    results = []
    for script_name in TEST_SCRIPTS:
        script_path = test_dir / script_name
        if script_path.exists():
            passed = run_test(script_path)
            results.append((script_name, passed))
        else:
            print(f"{Colors.RED}[WARN] 文件不存在: {script_name}{Colors.ENDC}\n")
            results.append((script_name, False))

    # 汇总结果
    print_header("测试结果汇总")

    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)

    for script_name, passed in results:
        status = f"{Colors.GREEN}[PASS]{Colors.ENDC}" if passed else f"{Colors.RED}[FAIL]{Colors.ENDC}"
        print(f"  {script_name:<30} {status}")

    print(f"\n总计: {passed_count}/{total_count} 通过")

    if passed_count == total_count:
        print(f"{Colors.GREEN}[SUCCESS] 所有测试通过！{Colors.ENDC}")
    else:
        print(f"{Colors.RED}[WARNING] 部分测试失败，请检查日志{Colors.ENDC}")

if __name__ == "__main__":
    main()
