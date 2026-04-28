#!/usr/bin/env python3
"""
Minder AI红娘 - 数据库初始化脚本

用法:
  cd ~/Desktop/婚恋AI && python3 -m minder.scripts.init_db
  cd ~/Desktop/婚恋AI && python3 -m minder.scripts.init_db --demo
  cd ~/Desktop/婚恋AI && python3 -m minder.scripts.init_db --reset
  cd ~/Desktop/婚恋AI && python3 -m minder.scripts.init_db --reset --demo

选项:
  --demo   初始化后自动导入演示数据 (30用户 + 匹配 + 消息 + 健康报告 + 订阅)
  --reset  先删除所有表再重建 (危险! 会清空所有数据)
"""

import asyncio
import sys
import os

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from minder.db.models import Base, engine


async def init_database(reset: bool = False):
    """Initialize the database, optionally drop and recreate all tables."""
    print("=" * 60)
    print("  Minder AI红娘 - 数据库初始化")
    print("=" * 60)
    print()

    if reset:
        print("[1/3] 删除现有表...")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        print("  ✓ 所有表已删除")
    else:
        print("[1/3] 检查数据库...")

    print()
    print("[2/3] 创建数据库表...")
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("  ✓ 数据库表创建成功")
    except Exception as e:
        print(f"  ✗ 数据库表创建失败: {e}")
        return False

    print()
    print("[3/3] 验证数据库...")
    try:
        async with engine.begin() as conn:
            def get_tables(sync_conn):
                from sqlalchemy import inspect
                inspector = inspect(sync_conn)
                return inspector.get_table_names()
            tables = await conn.run_sync(get_tables)
        print(f"  ✓ 数据库连接成功")
        print(f"  ✓ 已创建 {len(tables)} 个表:")
        for table in sorted(tables):
            print(f"    - {table}")
    except Exception as e:
        print(f"  ✗ 数据库验证失败: {e}")
        return False

    print()
    print("=" * 60)
    print("  数据库初始化完成！")
    print("=" * 60)
    print()

    # If --demo flag, run seed data
    if "--demo" in sys.argv:
        print("正在导入演示数据...")
        print()
        from minder.scripts.seed_data import seed_database
        return await seed_database(reset=False)
    else:
        print("提示:")
        print("  - 运行 python3 -m minder.scripts.seed_data      导入演示数据")
        print("  - 运行 python3 -m minder.scripts.init_db --demo  初始化+导入演示数据")
        print("  - 运行 uvicorn minder.main:app --reload          启动服务")
        print()

    return True


def main():
    reset = "--reset" in sys.argv
    success = asyncio.run(init_database(reset=reset))
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
