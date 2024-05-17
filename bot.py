import os
import requests
import telegram
from dotenv import load_dotenv
import logging


class TelegramLogsHandler(logging.Handler):

    def __init__(self, tg_bot, chat_id):
        super().__init__()
        self.chat_id = chat_id
        self.tg_bot = tg_bot

    def emit(self, record):
        log_entry = self.format(record)
        self.tg_bot.send_message(chat_id=self.chat_id, text=log_entry)

load_dotenv()
telegram_token = os.environ['TELEGRAM_TOKEN']
telegram_bot = telegram.Bot(token=telegram_token)
telegram_chat_id = telegram_bot.get_updates()[0].message.from_user.id
logger = logging.getLogger('Logger')
logger.setLevel(logging.DEBUG)
logger.addHandler(TelegramLogsHandler(telegram_bot, telegram_chat_id))

def get_notification(devman_token, telegram_bot, telegram_chat_id):
    headers = {
        'Authorization': f'Token {devman_token}'
    }
    long_polling_url = 'https://dvmn.org/api/long_polling/'
    timestamp = ''
    while True:
        try:
            logger.info("Запуск бота")
            payload = {'timestamp': timestamp}
            response = requests.get(long_polling_url, headers=headers, params = payload)
            response.raise_for_status()
            notice = response.json()
            status = notice['status']
            if status == 'timeout':
                logger.info("Истекло время тайм-аута")
                timestamp = notice['timestamp_to_request']
            if status == 'found':
                logger.info("Появилось уведомление о проверки работы")
                timestamp = notice['last_attempt_timestamp']
                new_attempts = notice['new_attempts']
                for attemp in new_attempts:
                    lesson_title = attemp['lesson_title']
                    lesson_url = attemp['lesson_url']
                    if attemp['is_negative']:
                        logger.info(f"Работу не приняли")
                        text = (f'У вас проверили работу: '
                                f'\n"{lesson_title}"\n'
                                f'\nК сожалению, в работе нашлись ошибки.\n'
                                f'\n Ссылка на работу: {lesson_url}')
                        telegram_bot.send_message(chat_id=telegram_chat_id, text=text)
                    else:
                        logger.info(f"Работу приняли")
                        text = (f'У вас проверили работу: '
                                f'\n"{lesson_title}"\n'
                                f'\nПреподавателю всё понравилось, можно приступать к следующему уроку!\n'
                                f'\nСсылка на работу: {lesson_url}')
                        telegram_bot.send_message(chat_id=telegram_chat_id, text=text)
        except requests.exceptions.ReadTimeout:
            logger.info("Истекло время тайм-аута")
            continue
        except requests.exceptions.ConnectionError:
            logger.info("Нет соединения с интернетом")
            continue


def main():
    load_dotenv()
    telegram_token = os.environ['TELEGRAM_TOKEN']
    devman_token = os.environ['DEVMAN_TOKEN']
    telegram_bot = telegram.Bot(token=telegram_token)
    telegram_chat_id = telegram_bot.get_updates()[0].message.from_user.id
    get_notification(devman_token, telegram_bot, telegram_chat_id)


if __name__ == '__main__':
    main()
