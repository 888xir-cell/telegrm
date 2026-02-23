import os
import asyncio
import logging
from threading import Thread
from flask import Flask
from telethon import TelegramClient, events, Button

# --- 1. 端口修复模块 (解决 Render 红色超时报错) ---
server = Flask('')

@server.route('/')
def home():
    return "Bot is running!"

def run_flask():
    # 绑定 Render 要求的 10000 端口
    server.run(host='0.0.0.0', port=10000)

# --- 2. 核心配置 ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

API_ID = int(os.getenv('TG_API_ID', '37132348'))
API_HASH = os.getenv('TG_API_HASH', 'abeefb9d7f75cff36be8052f9519cb5b')
BOT_TOKEN = os.getenv('TG_BOT_TOKEN', '7968296089:AAGknOWEh9q_3JO5DBGrWNPH-C9TlrWHnIA')

config = {
    "source_channels": ["@dashijian09"],
    "target_channel": "@SoutheastAsianrevelations",
    "ad_text": "欢迎关注 @SoutheastAsianrevelations 获取更多精彩内容！",
    "block_words": [],
    "is_running": True
}

client = TelegramClient('ace_final_fix', API_ID, API_HASH)

# --- 3. 菜单与搬运逻辑 ---
async def send_main_menu(chat_id):
    status = "✅ 运行中" if config['is_running'] else "🛑 已暂停"
    text = (f"🤖 **ACE 搬运机器人后台**\n\n"
            f"📈 状态: {status}\n"
            f"📢 监听: `{', '.join(config['source_channels'])}`\n"
            f"🎯 目标: `{config['target_channel']}`")
    
    buttons = [[Button.inline("⏯️ 启动/停止", b"toggle")], [Button.inline("➕ 添加源频道", b"add_src")]]
    await client.send_message(chat_id, text, buttons=buttons)

@client.on(events.NewMessage())
async def handler(event):
    if not config['is_running'] or event.is_private: return
    chat = await event.get_chat()
    chat_username = f"@{chat.username}" if hasattr(chat, 'username') and chat.username else str(event.chat_id)
    
    if chat_username in config['source_channels']:
        text = event.message.text or event.message.caption or ""
        full_text = f"{text}\n\n{config['ad_text']}"
        try:
            if event.message.media:
                await client.send_file(config['target_channel'], event.message.media, caption=full_text)
            else:
                await client.send_message(config['target_channel'], full_text)
            logger.info("📤 搬运成功")
        except Exception as e:
            logger.error(f"❌ 搬运失败: {e}")

@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    if event.is_private: await send_main_menu(event.chat_id)

@client.on(events.CallbackQuery())
async def callback(event):
    if event.data == b"toggle":
        config['is_running'] = not config['is_running']
        await send_main_menu(event.chat_id)

# --- 4. 启动启动 ---
async def main():
    # 启动假窗口线程
    Thread(target=run_flask).start()
    await client.start(bot_token=BOT_TOKEN)
    logger.info("✅ 机器人已上线并监听")
    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
