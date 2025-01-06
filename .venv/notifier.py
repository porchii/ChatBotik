import asyncio
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot
from aiogram.exceptions import TelegramNotFound, TelegramForbiddenError, TelegramUnauthorizedError, TelegramBadRequest
from Backend import DataBase
class Scheduler:
    def __init__(self, bot_token, db: DataBase):
        self.bot = Bot(token=bot_token)
        self.scheduler = AsyncIOScheduler()
        self.db = db

    async def start(self):
        self.scheduler.start()

    async def send_message(self, user_id, text):
        try:
            await self.bot.send_message(user_id, text)
            await asyncio.sleep(0.05)
        except TelegramNotFound:
            await self.db.delete_user(user_id)
        except TelegramForbiddenError:
            await self.db.delete_user(user_id)
        except TelegramUnauthorizedError:
            await self.db.delete_user(user_id)
        except TelegramBadRequest:
            await self.db.delete_user(user_id)

    def schedule_message(self, user_id, text, hour, minute):
        now = datetime.now()
        if now.weekday() == 6:
            send_time = now + timedelta(days=2)
        else:
            send_time = now + timedelta(days=1)
        send_time = send_time.replace(hour=hour, minute=minute, second=0, microsecond=0)

        self.scheduler.add_job(self.send_message, 'date', run_date=send_time, args=[user_id, text])

    def handle_table(self, lessons, user_id):
        for i in range(1, len(lessons)):
            cur = lessons[i]
            prev = lessons[i - 1]
            time = prev[3]
            hour = int(time[:2]); minute = int(time[3:])
            self.schedule_message(user_id, f'Следующий урок: {cur[1]}.\nНачинается в {cur[2]}', hour, minute)
        print(self.list_scheduled_messages())

    def list_scheduled_messages(self):
        jobs = self.scheduler.get_jobs()
        text = ''
        for job in jobs:
            text += f'Job ID: {job.id}, Next run time: {job.next_run_time}, Trigger: {job.trigger}, Args: {job.args}\n'
        return text


    def clear_scheduled_messages(self):
        self.scheduler.remove_all_jobs()
