1. 创建业务相关的表以 cps_ 开头，如 cps_file、cps_project、cps_task 等。
2. 使用SQLAlchemy ORM 创建对应的模型类，并定义好字段和属性。
3. 使用定义 postgresql 的语法定义表结构，如 VARCHAR、INT、TIMESTAMP 等。
4. 相同的表结构逻辑，例如 file 相关的表定义放在同一个文件下
5. 数据库描述文件 放在 ruoyi-fastapi-backend\module_admin\entity\do\ 目录下
6. 定义表时使用合适的数据类型，对字段添加必要的描述，状态字段使用字符串存储的方式，注释描述详细，布尔字段使用tinyint类型
