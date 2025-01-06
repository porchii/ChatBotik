import os
import tempfile
import openpyxl
import pandas as pd
import aiosqlite
import asyncio

from converter import Converter

conv = Converter()

class DataBase:
    def __init__(self, db_path='SomeData.db'):
        self.db_path = db_path
        self.loop = asyncio.get_event_loop()
        self.loop.run_until_complete(self.create_tables())

    async def create_tables(self):
        await self.create_users_table()
        await self.create_items()
        await self.create_lesson_tables()

    async def create_items(self):
        async with aiosqlite.connect(self.db_path) as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS items (
                    photo_id TEXT,
                    branch TEXT,
                    shift INTEGER
                )
            """)
            await conn.commit()

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

    async def create_lesson_tables(self):
        async with aiosqlite.connect(self.db_path) as conn:
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS Гидрострой (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    lesson_name TEXT,
                    start TEXT,
                    end TEXT,
                    class_name TEXT
                )
            ''')
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS Сахарова (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    lesson_name TEXT,
                    start TEXT,
                    end TEXT,
                    class_name TEXT
                )
            ''')
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS Макеева (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    lesson_name TEXT,
                    start TEXT,
                    end TEXT,
                    class_name TEXT
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

    async def get_photos(self, branch):
        async with aiosqlite.connect(self.db_path) as conn:
            cursor = await conn.execute('SELECT * FROM items WHERE branch = ?', (branch,))
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

    async def get_user_data(self, user_id):
        async with aiosqlite.connect(self.db_path) as conn:
            cursor = await conn.execute('''
                SELECT user_id, class_name, photo_mailing, branch, thread_id
                FROM Users_Data 
                WHERE user_id = ?
            ''', (user_id,))
            result = await cursor.fetchone()
        return result

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

    async def add_photo(self, photo_id, branch, shift):
        async with aiosqlite.connect(self.db_path) as conn:
            await conn.execute("""
                INSERT INTO items (photo_id, branch, shift)
                VALUES (?, ?, ?)
            """, (photo_id, branch, shift))
            await conn.commit()

    async def delete_photos(self, branch):
        async with aiosqlite.connect(self.db_path) as conn:
            await conn.execute("""
                DELETE FROM items WHERE branch = ?
            """, (branch,))
            await conn.commit()

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





    # Таблицы с расписанием


    async def get_lessons(self, group, branch):
        async with aiosqlite.connect(self.db_path) as conn:
            cursor = await conn.execute(f'''
                SELECT * FROM {branch}
                WHERE class_name = ?
            ''', (group,))
            matching_rows = await cursor.fetchall()
        return matching_rows


    async def clear_lessons_table(self, branch):
        async with aiosqlite.connect(self.db_path) as conn:
            await conn.execute(f'DELETE FROM {branch}')
            await conn.commit()


    async def update_table(self, file_path, branch):
        await self.clear_lessons_table(branch)
        xls = pd.ExcelFile(file_path)
        sheet_names = xls.sheet_names
        first_sheet_name = sheet_names[0]

        wb = openpyxl.load_workbook(file_path)
        ws = wb[first_sheet_name]

        merged_ranges = list(ws.merged_cells.ranges)

        for merged_cell_range in merged_ranges:
            min_col, min_row, max_col, max_row = openpyxl.utils.cell.range_boundaries(str(merged_cell_range))
            top_left_cell_value = ws.cell(row=min_row, column=min_col).value

            ws.unmerge_cells(str(merged_cell_range))

            for row in range(min_row, max_row + 1):
                for col in range(min_col, max_col + 1):
                    ws.cell(row=row, column=col, value=top_left_cell_value)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp_file:
            temp_file_path = tmp_file.name

        wb.save(temp_file_path)

        matrix = conv.convert(pd.read_excel(temp_file_path, sheet_name=first_sheet_name).to_numpy())
        os.remove(temp_file_path)

        async with aiosqlite.connect(self.db_path) as conn:
            for row in matrix:
                await conn.execute(f'''
                    INSERT INTO {branch} (lesson_name, start, end, class_name)
                    VALUES (?, ?, ?, ?)
                ''', (row[0], row[1], row[2], row[3]))
            await conn.commit()
