import os
import asyncio
import logging
from threading import Thread
from flask import Flask
from telethon import TelegramClient, events, Button

# --- 1. 修复 Render 红色报错的假窗口模块 ---
server = Flask('')

@server.route('/')
def home():
    return "Bot is running!"

def run_flask():
    # 绑定 10000 端口以满足 Render 的健康检查
    server.run(host='0.0.0.0', port=10000)

# --- 2. 基础配置 ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 从环境变量读取凭证
API_ID = int(os.getenv('TG_API_ID', '37132348'))
API_HASH = os.getenv('TG_API_HASH', 'abeefb9d7f75cff36be8052f9519cb5b')
BOT_TOKEN = os.getenv('TG_BOT_TOKEN', '7968296089:AAGknOWEh9q_3JO5DBGrWNPH-C9TlrWHnIA')

# 机器人动态配置
config = {
    "source_channels": ["@dashijian09"], # 初始源频道
    "target_channel": "@SoutheastAsianrevelations", # 目标频道
    "ad_text": "欢迎关注 @SoutheastAsianrevelations 获取更多精彩内容！",
    "block_words": [], 
    "is_running": True
}

client = TelegramClient('ace_final_v2', API_ID, API_HASH)

# --- 3. 菜单界面 ---
async def send_main_menu(chat_id):
    status = "✅ 运行中" if config['is_running'] else "🛑 已暂停"
    text = (f"🤖 **ACE 搬运机器人管理后台**\n\n"
            f"📈 **状态**: {status}\n"
            f"📢 **监听**: `{', '.join(config['source_channels'])}`\n"
            f"🎯 **目标**: `{config['target_channel']}`\n"
            f"🚫 **规则**: 已清空关键词（防止误判）")
    
    buttons = [
        [Button.inline("➕ 增加源频道", b"add_src"), Button.inline("➖ 删除源频道", b"del_src")],
        [Button.inline("📢 修改广告语", b"edit_ad"), Button.inline("🚫 设置屏蔽词", b"edit_block")],
        [Button.inline("⏯️ 启动/停止机器人", b"toggle")]
    ]
    await client.send_message(chat_id, text, buttons=buttons)

# --- 4. 核心搬运逻辑 ---
@client.on(events.NewMessage())
async def handler(event):
    if not config['is_running'] or event.is_private:
        return
    
    chat = await event.get_chat()
    chat_username = f"@{chat.username}" if hasattr(chat, 'username') and chat.username else str(event.chat_id)
    
    if chat_username in config['source_channels']:
        logger.info(f"📩 收到源频道 {chat_username} 消息")
        text = event.message.text or event.message.caption or ""
        
        # 简单过滤：如果设置了屏蔽词
        if config['block_words'] and any(word in text.lower() for word in config['block_words']):
            return
            
        full_text = f"{text}\n\n{config['ad_text']}"
        
        try:
            if event.message.media:
                await client.send_file(config['target_channel'], event.message.media, caption=full_text)
            else:
                await client.send_message(config['target_channel'], full_text)
            logger.info("📤 搬运成功！")
        except Exception as e:
            logger.error(f"❌ 搬运失败: {e}")

# --- 5. 交互指令 ---
@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    if event.is_private:
        await send_main_menu(event.chat_id)

@client.on(events.CallbackQuery())
async def callback_handler(event):
    if event.data == b"toggle":
        config['is_running'] = not config['is_running']
        await event.answer("状态已切换")
        await send_main_menu(event.chat_id)
    elif event.data == b"add_src":
        await event.respond("直接发送频道用户名即可（例如 @abc123）")

# --- 6. 运行程序 ---
async def main():
    # 先启动 Flask 线程解决 Render 报错
    Thread(target=run_flask).start()
    
    # 再启动 Telegram 客户端
    await client.start(bot_token=BOT_TOKEN)
    logger.info("✅ 机器人已上线")
    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
