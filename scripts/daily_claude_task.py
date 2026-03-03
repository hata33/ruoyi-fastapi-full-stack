#!/usr/bin/env python3
import os
import subprocess
import logging
from datetime import datetime

# ===================== 配置项 =====================
# 目标工作目录
TARGET_DIR = "/data/images/ruoyi-fastapi-full-stack/"
# 要执行的 claude 命令（替换成你实际的 claude 命令，如绝对路径/zhipu）
CLAUDE_CMD = 'claude "介绍python"'  # 若之前重命名为zhipu，改这里为 'zhipu "介绍python"'
# 日志文件路径（记录执行结果，方便排查）
LOG_FILE = "/var/log/daily_claude_task.log"

# ===================== 日志配置 =====================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filename=LOG_FILE,
    filemode="a"  # 追加模式，不覆盖历史日志
)


def execute_claude_task():
    """切换目录并执行 claude 命令"""
    try:
        # 1. 检查目标目录是否存在
        if not os.path.exists(TARGET_DIR):
            logging.error(f"目标目录不存在：{TARGET_DIR}")
            raise FileNotFoundError(f"Directory {TARGET_DIR} not found")

        # 2. 切换到目标目录
        os.chdir(TARGET_DIR)
        logging.info(f"成功切换到目录：{TARGET_DIR}")

        # 3. 执行 claude 命令（捕获输出和错误）
        logging.info(f"开始执行命令：{CLAUDE_CMD}")
        # subprocess 执行命令，捕获stdout/stderr
        result = subprocess.run(
            CLAUDE_CMD,
            shell=True,  # 支持cd/管道等shell语法
            cwd=TARGET_DIR,  # 确保在目标目录执行
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding="utf-8",  # 解决中文乱码
            timeout=300  # 超时时间5分钟，避免卡死
        )

        # 4. 记录执行结果
        if result.returncode == 0:
            logging.info(f"命令执行成功，输出：\n{result.stdout}")
        else:
            logging.error(f"命令执行失败，错误信息：\n{result.stderr}")
        return result.returncode

    except subprocess.TimeoutExpired:
        logging.error("命令执行超时（超过5分钟）")
        return 1
    except Exception as e:
        logging.error(f"任务执行异常：{str(e)}")
        return 1


if __name__ == "__main__":
    # 打印启动信息（手动测试时能看到）
    print(f"[{datetime.now()}] 开始执行每日 claude 任务...")
    logging.info("="*50 + " 任务启动 " + "="*50)
    # 执行核心任务
    exit_code = execute_claude_task()
    # 打印结束信息
    if exit_code == 0:
        print(f"[{datetime.now()}] 任务执行成功！日志见 {LOG_FILE}")
    else:
        print(f"[{datetime.now()}] 任务执行失败！日志见 {LOG_FILE}")
    # 退出脚本（返回码给crontab）
    exit(exit_code)
