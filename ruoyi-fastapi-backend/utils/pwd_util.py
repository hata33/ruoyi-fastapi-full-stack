from passlib.context import CryptContext

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')


class PwdUtil:
    """
    密码工具类
    """

    @classmethod
    def verify_password(cls, plain_password, hashed_password):
        """
        工具方法：校验当前输入的密码与数据库存储的密码是否一致

        :param plain_password: 当前输入的密码
        :param hashed_password: 数据库存储的密码
        :return: 校验结果
        """
        return pwd_context.verify(plain_password, hashed_password)

    @classmethod
    def get_password_hash(cls, input_password):
        """
        工具方法：对当前输入的密码进行加密

        :param input_password: 输入的密码
        :return: 加密成功的密码
        """
        # bcrypt 有72字节长度限制，对超过限制的密码进行截断
        if isinstance(input_password, str):
            # 将字符串转换为bytes并截断到72字节
            password_bytes = input_password.encode('utf-8')
            if len(password_bytes) > 72:
                password_bytes = password_bytes[:72]
                # 转换回字符串以保持兼容性
                input_password = password_bytes.decode('utf-8', errors='ignore')

        return pwd_context.hash(input_password)
