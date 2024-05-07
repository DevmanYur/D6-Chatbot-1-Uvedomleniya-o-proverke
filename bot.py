import os
import requests
import telegram
from dotenv import load_dotenv


def get_notification(devman_token, telegram_bot, telegram_chat_id):
    headers = {
        'Authorization': f'Token {devman_token}'
    }
    long_polling_url = 'https://dvmn.org/api/long_polling/'
    timestamp = ''
    while True:
        try:
            payload = {'timestamp': timestamp}
            response = requests.get(long_polling_url, headers=headers, params = payload)
            response.raise_for_status()
            notice = response.json()
            status = notice['status']
            if status == 'timeout':
                timestamp = notice['timestamp_to_request']
            if status == 'found':
                timestamp = notice['last_attempt_timestamp']
                new_attempts = notice['new_attempts']
                for attemp in new_attempts:
                    lesson_title = attemp['lesson_title']
                    lesson_url = attemp['lesson_url']
                    if attemp['is_negative']:
                        text = (f'У вас проверили работу: '
                                f'\n"{lesson_title}"\n'
                                f'\nК сожалению, в работе нашлись ошибки.\n'
                                f'\n Ссылка на работу: {lesson_url}')
                        telegram_bot.send_message(chat_id=telegram_chat_id, text=text)
                    else:
                        text = (f'У вас проверили работу: '
                                f'\n"{lesson_title}"\n'
                                f'\nПреподавателю всё понравилось, можно приступать к следующему уроку!\n'
                                f'\nСсылка на работу: {lesson_url}')
                        telegram_bot.send_message(chat_id=telegram_chat_id, text=text)
        except requests.exceptions.ReadTimeout:
            continue
        except requests.exceptions.ConnectionError:
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
