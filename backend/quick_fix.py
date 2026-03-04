"""移除 chat 控制器的 token 校验"""
import re

def fix_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    original = content
    content = content.replace(", dependencies=[Depends(CheckUserInterfaceAuth('chat:",))"], "")
    content = content.replace("dependencies=[Depends(CheckUserInterfaceAuth('chat:",))]\n", "")
    content = content.replace("dependencies=[Depends(CheckUserInterfaceAuth('chat:",))],", "")
    content = content.replace("dependencies=[Depends(CheckUserInterfaceAuth('chat:",))]", "")

    if 'dependencies=[Depends(LoginService.get_current_user)]' in content:
        content = content.replace("APIRouter(prefix='/api/chat/files', dependencies=[Depends(LoginService.get_current_user)])", "APIRouter(prefix='/api/chat/files')  # 移除 token 校验，方便调试")
        content = content.replace("APIRouter(prefix='/api/chat/settings', dependencies=[Depends(LoginService.get_current_user)])", "APIRouter(prefix='/api/chat/settings')  # 移除 token 校验，方便调试")

    if 'current_user: CurrentUserModel = Depends(LoginService.get_current_user)' in content:
        content = content.replace(", current_user: CurrentUserModel = Depends(LoginService.get_current_user)", "")
        content = content.replace("current_user: CurrentUserModel = Depends(LoginService.get_current_user),", "")

    if 'current_user.user.user_id' in content:
        content = content.replace('current_user.user.user_id', '1')

    if content != original:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

fix_file('backend/module_chat/controller/chat_file_controller.py')
print('chat_file_controller.py - OK')

fix_file('backend/module_chat/controller/chat_setting_controller.py')
print('chat_setting_controller.py - OK')
