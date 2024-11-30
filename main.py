import logging
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

result = load_dotenv('params.env')

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s]: %(message)s")

TG_BOT_TOKEN = os.getenv("TG_BOT_TOKEN")
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = os.getenv("SMTP_PORT")
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

user_data = {}

def is_valid_email(email):
    import re
    email_regex = r'^[\w\.-]+@([\w-]+\.)+[\w-]{2,4}$'
    return re.match(email_regex, email)

def send_email(email_to, message):
    smtp_server = SMTP_SERVER
    smtp_port = SMTP_PORT
    email_from = EMAIL_ADDRESS
    password = EMAIL_PASSWORD
    logging.info(f'Отправка сообщения на адрес {email_to}')

    try:
        server = smtplib.SMTP_SSL(smtp_server, smtp_port)
        server.login(email_from, password)

        msg = MIMEMultipart()
        msg['From'] = email_from
        msg['To'] = email_to
        msg['Subject'] = "Сообщение от Telegram-бота"
        msg.attach(MIMEText(message, 'plain'))

        server.sendmail(email_from, email_to, msg.as_string())
        server.quit()
        return True
    
    except Exception as e:
        logging.error(f"Ошибка отправки: {e}")
        return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    logging.info(f'Пользователь с id {user_id} вызвал бота')
    user_data[user_id] = {'email': None, 'message': None}
    await update.message.reply_text("Привет! Пожалуйста, отправьте ваш email.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    if user_id not in user_data:
        await update.message.reply_text("Напишите /start для начала.")
        return

    if user_data[user_id]['email'] is None:
        logging.info('Проверка введённого пользователем email')
        if is_valid_email(text):
            user_data[user_id]['email'] = text
            await update.message.reply_text("Отлично! Теперь отправьте текст сообщения.")
            logging.info(f'Email введён корректно пользователем с id {user_id}')
        else:
            await update.message.reply_text("Это не похоже на правильный email. Попробуйте снова.")
            logging.warning(f'Пользователь с id {user_id} ввёл неверный email: "{text}"')
    elif user_data[user_id]['message'] is None:
        user_data[user_id]['message'] = text
        email = user_data[user_id]['email']
        message = text

        if send_email(email, message):
            await update.message.reply_text("Сообщение успешно отправлено!")
            logging.info(f'Сообщение для пользователя с id {user_id} было успешно отправлено')
        else:
            await update.message.reply_text("Произошла ошибка при отправке сообщения.")
        
        # Очистка данных пользователя
        user_data.pop(user_id)

def main():

    app = Application.builder().token(TG_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logging.info("Бот запущен...")
    app.run_polling()

if __name__ == "__main__":
    main()