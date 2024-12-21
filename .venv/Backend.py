import os
import tempfile
import openpyxl
import pandas as pd
import aiosqlite
import asyncio

class DataBase:
    def __init__(self, db_path='SomeData.db'):
        self.db_path = db_path
        self.loop = asyncio.get_event_loop()
        self.loop.run_until_complete(self.create_tables())

    async def create_tables(self):
        await self.create_users_table()

    async def create_users_table(self):
        async with aiosqlite.connect(self.db_path) as conn:
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS Users_Data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    class_name TEXT DEFAULT '-',
                    photo_mailing INTEGER DEFAULT 0,
                    branch TEXT DEFAULT '-',
                    thread_id INTEGER DEFAULT 0
                )
            ''')
            await conn.commit()

    async def user_exists(self, user_id):
        async with aiosqlite.connect(self.db_path) as conn:
            cursor = await conn.execute('''
                SELECT 1 FROM Users_Data WHERE user_id = ? LIMIT 1
            ''', (user_id,))
            result = await cursor.fetchone()
        return result is not None

    async def get_all_users(self):
        async with aiosqlite.connect(self.db_path) as conn:
            cursor = await conn.execute('SELECT * FROM Users_Data')
            rows = await cursor.fetchall()
        return rows

    async def get_users_by_branch(self, branch):
        async with aiosqlite.connect(self.db_path) as conn:
            cursor = await conn.execute("""
                SELECT user_id, class_name, photo_mailing, branch, thread_id
                FROM Users_Data
                WHERE branch = ?
            """, (branch,))
            rows = await cursor.fetchall()
        return rows

    async def add_user(self, user_id, class_name, branch, thread_id, join_photo_mailing=0):
        async with aiosqlite.connect(self.db_path) as conn:
            if not await self.user_exists(user_id):
                await conn.execute('''
                    INSERT INTO Users_Data (user_id, class_name, photo_mailing, branch, thread_id)
                    VALUES (?, ?, ?, ?, ?)
                ''', (user_id, class_name, join_photo_mailing, branch, thread_id))
                await conn.commit()
            else:
                return

    async def delete_user(self, user_id):
        async with aiosqlite.connect(self.db_path) as conn:
            await conn.execute('''
                DELETE FROM Users_Data WHERE user_id = ?
            ''', (user_id,))
            await conn.commit()

    async def change_class_value(self, user_id, class_name):
        async with aiosqlite.connect(self.db_path) as conn:
            await conn.execute('''
                UPDATE Users_Data
                SET class_name = ?
                WHERE user_id = ?
            ''', (class_name, user_id))
            await conn.commit()

    async def change_photo_value(self, user_id, photo_mailing):
        async with aiosqlite.connect(self.db_path) as conn:
            await conn.execute('''
                UPDATE Users_Data
                SET photo_mailing = ?
                WHERE user_id = ?
            ''', (photo_mailing, user_id))
            await conn.commit()


    async def change_branch_value(self, user_id, branch):
        async with aiosqlite.connect(self.db_path) as conn:
            await conn.execute('''
                UPDATE Users_Data
                SET branch = ?
                WHERE user_id = ?
            ''', (branch, user_id))
            await conn.commit()

    async def change_thread_value(self, user_id, thread_id):
        async with aiosqlite.connect(self.db_path) as conn:
            await conn.execute('''
                UPDATE Users_Data
                SET thread_id = ?
                WHERE user_id = ?
            ''', (thread_id, user_id))
            await conn.commit()

    async def get_user_data(self, user_id):
        async with aiosqlite.connect(self.db_path) as conn:
            cursor = await conn.execute('''
                SELECT user_id, class_name, photo_mailing, branch, thread_id
                FROM Users_Data 
                WHERE user_id = ?
            ''', (user_id,))
            result = await cursor.fetchone()
        return result