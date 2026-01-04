import os
import asyncio
import logging
from datetime import datetime
from collections import defaultdict
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# === 配置 ===
TRIGGER_COUNT = 3  # 需要几个不同用户发送相同消息
TIME_WINDOW = 60   # 统计时间窗口（秒）
# === 配置结束 ===

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# 存储消息记录：chat_id -> message_key -> {count, users, first_seen}
message_tracker = defaultdict(lambda: {})

def get_message_key(update: Update):
    """生成消息的唯一标识"""
    if update.message.text:
        return f"text:{update.message.text.strip().lower()}"
    elif update.message.sticker:
        return f"sticker:{update.message.sticker.file_unique_id}"
    elif update.message.photo:
        return f"photo:{update.message.photo[-1].file_unique_id}"
    return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f'🤖 复读机器人已启动！当 {TRIGGER_COUNT} 个不同用户在 {TIME_WINDOW} 秒内发送相同内容时，我会自动复读。')

async def track_and_echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    message_key = get_message_key(update)
    
    if not message_key:
        return
    
    now = datetime.now()
    
    # 初始化或获取该消息的记录
    if message_key not in message_tracker[chat_id]:
        message_tracker[chat_id][message_key] = {
            'count': 1,
            'users': {user_id},
            'first_seen': now
        }
    else:
        record = message_tracker[chat_id][message_key]
        
        # 检查时间窗口
        if (now - record['first_seen']).seconds > TIME_WINDOW:
            # 超时，重置记录
            record['count'] = 1
            record['users'] = {user_id}
            record['first_seen'] = now
        else:
            # 在时间窗口内
            if user_id not in record['users']:
                record['users'].add(user_id)
                record['count'] += 1
    
    # 检查是否达到触发条件
    record = message_tracker[chat_id][message_key]
    if record['count'] >= TRIGGER_COUNT:
        # 复读消息
        if update.message.text:
            await update.message.reply_text(update.message.text)
        elif update.message.sticker:
            await update.message.reply_sticker(update.message.sticker.file_id)
        elif update.message.photo:
            await update.message.reply_photo(update.message.photo[-1].file_id, caption=update.message.caption)
        
        # 触发后清除该条记录，避免重复触发
        del message_tracker[chat_id][message_key]
        logger.info(f"在群组 {chat_id} 触发了复读: {message_key}")

async def cleanup_old_records(app: Application):
    """定时清理过期的记录"""
    while True:
        await asyncio.sleep(TIME_WINDOW)  # 每隔一个时间窗口检查一次
        now = datetime.now()
        for chat_id in list(message_tracker.keys()):
            keys_to_delete = []
            for msg_key, record in message_tracker[chat_id].items():
                if (now - record['first_seen']).seconds > TIME_WINDOW:
                    keys_to_delete.append(msg_key)
            for key in keys_to_delete:
                del message_tracker[chat_id][key]

async def post_init(app: Application):
    """在机器人启动后，启动后台清理任务"""
    # 创建并启动清理任务，但不等待它完成
    app.create_task(cleanup_old_records(app))
    logger.info("后台消息记录清理任务已启动。")

def main() -> None:
    """启动机器人"""
    # 从环境变量获取Token
    token = os.getenv('BOT_TOKEN')
    if not token:
        logger.error("请设置 BOT_TOKEN 环境变量！")
        return
    
    # 创建应用
    application = Application.builder().token(token).build()
    
    # 添加处理器
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, track_and_echo))
    
    # 设置机器人启动后的初始化操作
    application.post_init = post_init
    
    # 启动机器人（这会自动运行事件循环）
    logger.info("机器人开始轮询...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
