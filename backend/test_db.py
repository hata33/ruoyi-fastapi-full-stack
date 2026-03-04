import asyncio
import asyncpg

async def test_postgres():
    try:
        conn = await asyncpg.connect(
            host='localhost',
            port=5432,
            user='postgres',
            password='postgres123'
        )
        version = await conn.fetchval('SELECT version()')
        print(f'PostgreSQL connected: {version[:50]}...')

        # 检查数据库是否存在
        db_exists = await conn.fetchval(
            "SELECT EXISTS(SELECT 1 FROM pg_database WHERE datname = $1)",
            'hata-service-platform'
        )
        print(f'Database "hata-service-platform" exists: {db_exists}')

        # 列出所有数据库
        databases = await conn.fetch("SELECT datname FROM pg_database WHERE NOT datistemplate")
        print(f'Available databases: {[row["datname"] for row in databases]}')

        await conn.close()
        return True
    except Exception as e:
        print(f'PostgreSQL connection failed: {e}')
        return False

if __name__ == '__main__':
    result = asyncio.run(test_postgres())
    if not result:
        print('Failed to connect to PostgreSQL')
