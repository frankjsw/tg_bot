import os
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from collections import defaultdict

# 从环境变量中获取 Telegram Bot API Token
TOKEN = os.getenv('BOT_API_TOKEN')

# 存储收到的消息
message_dict = defaultdict(list)

# 定义启动命令的函数
def start(update: Update, context: CallbackContext):
    update.message.reply_text("你好！我是自动回复机器人，发送消息让我看看吧。")

# 定义自动回复的函数
def auto_reply(update: Update, context: CallbackContext):
    user_message = update.message.text  # 获取用户发送的消息
    user_id = update.message.from_user.id  # 获取用户 ID

    # 将用户 ID 和对应的消息存储在字典中
    message_dict[user_message].append(user_id)

    # 如果同样的消息来自不同用户，发送自动回复
    if len(message_dict[user_message]) > 1:
        update.message.reply_text(f"有多人发送了相同的消息：'{user_message}'，这是系统的自动回复。")

# 定义错误处理函数
def error(update: Update, context: CallbackContext):
    print(f"Error occurred: {context.error}")

def main():
    # 创建 Updater 对象，并传入 Bot API Token
    if not TOKEN:
        print("No TOKEN provided! Please set the BOT_API_TOKEN environment variable.")
        return

    updater = Updater(TOKEN, use_context=True)

    # 获取调度器，用于注册处理器
    dp = updater.dispatcher

    # 注册启动命令处理器
    dp.add_handler(CommandHandler("start", start))

    # 注册消息处理器（处理所有文本消息）
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, auto_reply))

    # 错误处理
    dp.add_error_handler(error)

    # 启动机器人
    print("Bot is starting...")
    updater.start_polling()

    # 保持程序运行直到按 Ctrl+C
    updater.idle()

if __name__ == '__main__':
    main()
