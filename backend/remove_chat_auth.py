"""批量移除 chat 模块的 token 校验"""
import os
import re

CHAT_CONTROLLERS = [
    'backend/module_chat/controller/chat_conversation_controller.py',
    'backend/module_chat/controller/chat_message_controller.py',
    'backend/module_chat/controller/chat_model_controller.py',
    'backend/module_chat/controller/chat_file_controller.py',
    'backend/module_chat/controller/chat_setting_controller.py',
]

def fix_controller(file_path):
    """修复单个控制器文件"""
    print(f"处理: {file_path}")

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content

    # 1. 移除路由级别的 token 校验
    # APIRouter(prefix='...', dependencies=[Depends(LoginService.get_current_user)])
    # -> APIRouter(prefix='...')
    content = re.sub(
        r"APIRouter\(prefix='([^']+)',\s*dependencies=\[Depends\(LoginService\.get_current_user\)\]\)",
        r"APIRouter(prefix='\1')  # 移除 token 校验，方便调试",
        content
    )

    # 2. 移除接口级别的权限检查
    # dependencies=[Depends(CheckUserInterfaceAuth('...'))],  -> 删除
    content = re.sub(
        r",\s*dependencies=\[Depends\(CheckUserInterfaceAuth\('[^']+'\)\)\],?",
        "",
        content
    )

    # 3. 移除 current_user 依赖
    # current_user: CurrentUserModel = Depends(LoginService.get_current_user),
    content = re.sub(
        r",\s*current_user:\s*CurrentUserModel\s*=\s*Depends\(LoginService\.get_current_user\),?",
        "",
        content
    )

    # 4. 替换 current_user.user.user_id 为固定值
    content = re.sub(
        r"current_user\.user\.user_id",
        "1",  # 使用固定用户ID 1
        content
    )

    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  ✓ 已修改")
    else:
        print(f"  - 无需修改")

if __name__ == '__main__':
    print("=== 批量移除 chat 模块 token 校验 ===\n")

    for controller in CHAT_CONTROLLERS:
        if os.path.exists(controller):
            fix_controller(controller)
        else:
            print(f"文件不存在: {controller}")

    print("\n=== 完成 ===")
