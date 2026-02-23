import os
import asyncio
import logging
from threading import Thread
from flask import Flask
from telethon import TelegramClient, events, Button

# --- 1. 修复 Render 红色报错的“假窗口”模块 ---
server = Flask('')

@server.route('/')
def home():
    return "Bot is running!"

def run_flask():
    # Render 默认检查 10000 端口
    server.run(host='0.0.0.0', port=10000)

# --- 2. 基础配置与日志 ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 从环境变量获取凭证
API_ID = int(os.getenv('TG_API_ID', '37132348'))
API_HASH = os.getenv('TG_API_HASH', 'abeefb9d7f75cff36be8052f9519cb5b')
BOT_TOKEN = os.getenv('TG_BOT_TOKEN', '7968296089:AAGknOWEh9q_3JO5DBGrWNPH-C9TlrWHnIA')

# 机器人运行配置
config = {
    "source_channels": ["@dashijian09"], # 监听频道
    "target_channel": "@SoutheastAsianrevelations", # 目标频道
    "ad_text": "欢迎关注 @SoutheastAsianrevelations 获取更多精彩内容！",
    "block_words": [], # 屏蔽词列表
    "is_running": True
}

client = TelegramClient('ace_final_session', API_ID, API_HASH)

# --- 3. 菜单界面 ---
async def send_main_menu(chat_id):
    status_icon = "✅ 运行中" if config['is_running'] else "🛑 已暂停"
    text = (f"🤖 **ACE 搬运机器人管理后台**\n\n"
            f"📈 **当前状态**: {status_icon}\n"
            f"📢 **监听频道**: `{', '.join(config['source_channels'])}`\n"
            f"🎯 **目标频道**: `{config['target_channel']}`\n"
            f"🚫 **过滤规则**: {len(config['block_words'])} 个关键词")
    
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
        logger.info(f"📩 收到源频道 {chat_username} 的新消息")
        text = event.message.text or event.message.caption or ""
        
        # 关键词过滤
        if config['block_words'] and any(word in text.lower() for word in config['block_words']):
            logger.info("🚫 命中关键词屏蔽，跳过转发")
            return
            
        full_text = f"{text}\n\n{config['ad_text']}"
        
        try:
            if event.message.media:
                await client.send_file(config['target_channel'], event.message.media, caption=full_text)
            else:
                await client.send_message(config['target_channel'], full_text)
            logger.info(f"📤 成功搬运至 {config['target_channel']}")
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
        await event.respond("直接发送频道用户名即可（如 @test123）")

# --- 6. 启动程序 ---
async def main():
    # 启动 Flask 假窗口线程
    Thread(target=run_flask).start()
    
    await client.start(bot_token=BOT_TOKEN)
    logger.info("✅ 机器人已上线，Render 端口检查已绕过")
    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
