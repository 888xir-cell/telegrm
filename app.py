import os
import asyncio
import logging
import re
from threading import Thread
from flask import Flask
from telethon import TelegramClient, events, Button

# --- 1. 解决 Render 端口报错的假窗口 ---
server = Flask('')

@server.route('/')
def home():
    return "Bot is running!"

def run_flask():
    server.run(host='0.0.0.0', port=10000)

# --- 2. 基础配置与日志 ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

API_ID = int(os.getenv('TG_API_ID', '37132348'))
API_HASH = os.getenv('TG_API_HASH', 'abeefb9d7f75cff36be8052f9519cb5b')
BOT_TOKEN = os.getenv('TG_BOT_TOKEN', '7968296089:AAGknOWEh9q_3JO5DBGrWNPH-C9TlrWHnIA')

# 动态配置中心
config = {
    "source_channels": ["@dashijian09"], 
    "target_channel": "@SoutheastAsianrevelations", 
    "ad_text": "✨ 关注我的频道获取更多资讯！", # 默认广告后缀，可在后台修改
    "block_words": [], 
    "is_running": True
}

client = TelegramClient('ace_cleaner_pro', API_ID, API_HASH)

# --- 3. 核心功能：清理源频道垃圾信息 ---
def clean_message_content(text):
    if not text:
        return ""
    
    # 1. 剔除特定的广告行（如：关注吃瓜频道... 投稿...）
    # 这里匹配包含“关注”、“频道”、“投稿”等关键词的行并整行删除
    lines = text.split('\n')
    filtered_lines = []
    for line in lines:
        if "关注" in line or "频道" in line or "投稿" in line:
            continue
        filtered_lines.append(line)
    text = '\n'.join(filtered_lines)

    # 2. 剔除所有 @用户名 (如 @v123, @ab123)
    text = re.sub(r'@\w+', '', text)
    
    # 3. 剔除所有链接 (http, https, t.me)
    text = re.sub(r'https?://\S+|t\.me/\S+', '', text)
    
    # 4. 去除多余的空白行和空格
    text = re.sub(r'\n\s*\n', '\n', text)
    
    return text.strip()

# --- 4. 菜单界面 ---
async def send_main_menu(chat_id):
    status = "✅ 运行中" if config['is_running'] else "🛑 已暂停"
    text = (f"🤖 **ACE 搬运机器人后台**\n\n"
            f"📈 状态: {status}\n"
            f"📡 监听: `{', '.join(config['source_channels'])}`\n"
            f"🎯 目标: `{config['target_channel']}`\n\n"
            f"📝 当前广告后缀:\n`{config['ad_text']}`")
    
    buttons = [
        [Button.inline("➕ 添加源频道", b"add_src"), Button.inline("⏯️ 启动/停止", b"toggle")],
        [Button.inline("📢 修改广告语", b"edit_ad"), Button.inline("🚫 设置屏蔽词", b"edit_block")]
    ]
    await client.send_message(chat_id, text, buttons=buttons)

# --- 5. 搬运处理器 ---
@client.on(events.NewMessage())
async def handler(event):
    if not config['is_running'] or event.is_private:
        return
    
    chat = await event.get_chat()
    chat_username = f"@{chat.username}" if hasattr(chat, 'username') and chat.username else str(event.chat_id)
    
    if chat_username in config['source_channels']:
        raw_text = event.message.text or event.message.caption or ""
        
        # 执行深度清洗
        cleaned_text = clean_message_content(raw_text)
        
        # 叠加你自由设置的广告后缀
        final_text = f"{cleaned_text}\n\n{config['ad_text']}"
        
        try:
            if event.message.media:
                await client.send_file(config['target_channel'], event.message.media, caption=final_text)
            else:
                await client.send_message(config['target_channel'], final_text)
            logger.info("📤 清洗并搬运成功")
        except Exception as e:
            logger.error(f"❌ 搬运失败: {e}")

# --- 6. 交互逻辑 ---
@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    if event.is_private:
        await send_main_menu(event.chat_id)

@client.on(events.CallbackQuery())
async def callback_handler(event):
    if event.data == b"toggle":
        config['is_running'] = not config['is_running']
        await send_main_menu(event.chat_id)
    elif event.data == b"edit_ad":
        async with client.conversation(event.chat_id) as conv:
            await conv.send_message("请输入你想要设置的**自定义广告后缀**：")
            response = await conv.get_response()
            config['ad_text'] = response.text
            await conv.send_message(f"✅ 广告后缀已修改为：\n{config['ad_text']}")
            await send_main_menu(event.chat_id)

# --- 7. 启动程序 ---
async def main():
    Thread(target=run_flask).start()
    await client.start(bot_token=BOT_TOKEN)
    logger.info("✅ 机器人已上线并开启自动清洗功能")
    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
