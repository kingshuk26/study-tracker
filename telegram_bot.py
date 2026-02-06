from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from models import db, User

TOKEN = "8535483656:AAFvRV9qcUWUQ1mkHBKrHzbgWFc_D2lOCBE"


def run_bot(flask_app):

    async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

        with flask_app.app_context():

            chat_id = str(update.effective_chat.id)

            if not context.args:
                await update.message.reply_text(
                    "Use:\n/start your_email@gmail.com"
                )
                return

            email = context.args[0]

            user = User.query.filter_by(email=email).first()

            if not user:
                await update.message.reply_text("❌ Email not found in StudyOS")
                return

            user.telegram_id = chat_id
            db.session.commit()

            await update.message.reply_text("✅ Telegram connected successfully!")

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.run_polling()
