import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from collections import defaultdict

# 从环境变量中获取 Telegram Bot API Token
TOKEN = os.getenv('BOT_API_TOKEN')

# 存储收到的消息
message_dict = defaultdict(list)

# 定义启动命令的函数
async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("你好！我是自动回复机器人，发送消息让我看看吧。")

# 定义自动回复的函数
async def auto_reply(update: Update, context: CallbackContext):
    user_message = update.message.text  # 获取用户发送的消息
    user_id = update.message.from_user.id  # 获取用户 ID

    # 将用户 ID 和对应的消息存储在字典中
    message_dict[user_message].append(user_id)

    # 如果同样的消息来自不同用户，发送自动回复
    if len(message_dict[user_message]) > 1:
        await update.message.reply_text(f"有多人发送了相同的消息：'{user_message}'，这是系统的自动回复。")

# 定义错误处理函数
async def error(update: Update, context: CallbackContext):
    print(f"Error occurred: {context.error}")

def main():
    # 创建 Application 对象，并传入 Bot API Token
    if not TOKEN:
        print("No TOKEN provided! Please set the BOT_API_TOKEN environment variable.")
        return

    # 使用 Application 代替 Updater
    application = Application.builder().token(TOKEN).build()

    # 注册启动命令处理器
    application.add_handler(CommandHandler("start", start))

    # 注册消息处理器（处理所有文本消息）
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, auto_reply))

    # 错误处理
    application.add_error_handler(error)

    # 启动机器人
    print("Bot is starting...")
    application.run_polling()

if __name__ == '__main__':
    main()
