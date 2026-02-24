import os
import asyncio
import logging
import re
from threading import Thread
from flask import Flask
from telethon import TelegramClient, events, Button

# --- 1. Render 心跳接口 ---
server = Flask('')
@server.route('/')
def home(): return "Bot is Active!" # 用于 UptimeRobot 监控
def run_flask(): server.run(host='0.0.0.0', port=10000)

# --- 2. 基础配置 ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

API_ID = int(os.getenv('TG_API_ID', '37132348'))
API_HASH = os.getenv('TG_API_HASH', 'abeefb9d7f75cff36be8052f9519cb5b')
BOT_TOKEN = os.getenv('TG_BOT_TOKEN', '7968296089:AAGknOWEh9q_3JO5DBGrWNPH-C9TlrWHnIA')

config = {
    "source_channels": ["@dashijian09", "@xoxokrk"], 
    "target_channel": "@SoutheastAsianrevelations", 
    "ad_text": "🎀欢迎订阅频道： 投稿/商务@BBGS1688",
    "is_running": True,
    "waiting_action": None 
}

# 媒体组缓冲区：用于存放 grouped_id 消息
album_cache = {}

client = TelegramClient('ace_pro_v10', API_ID, API_HASH)

# --- 3. 工具函数 ---
def format_username(input_str):
    name = input_str.strip().split('t.me/')[-1].replace('@', '')
    return f"@{name}"

def clean_message_content(text):
    if not text: return ""
    lines = text.split('\n')
    filtered = [l for l in lines if not any(w in l for w in ["关注", "频道", "投稿", ">>"])]
    return re.sub(r'https?://\S+|t\.me/\S+', '', '\n'.join(filtered)).strip()

# --- 4. 菜单界面 ---
async def send_main_menu(chat_id):
    status = "✅ 运行中" if config['is_running'] else "🛑 已暂停"
    text = (f"🤖 **ACE 搬运机器人 (媒体组增强版)**\n\n"
            f"📈 状态: {status}\n"
            f"📡 监听: `{', '.join(config['source_channels'])}`\n"
            f"🎯 目标: `{config['target_channel']}`\n\n"
            f"📝 广告: \n{config['ad_text']}")
    buttons = [[Button.inline("➕ 添加源", b"add_src"), Button.inline("➖ 删除源", b"del_src")],
               [Button.inline("🎯 修改目标", b"edit_target"), Button.inline("📢 广告语", b"edit_ad")],
               [Button.inline("⏯️ 启动/停止", b"toggle")]]
    await client.send_message(chat_id, text, buttons=buttons)

# --- 5. 核心搬运逻辑 (处理 Album 媒体组) ---
@client.on(events.NewMessage())
async def forwarder(event):
    if not config['is_running'] or event.is_private: return
    
    try:
        chat = await event.get_chat()
        current_chat = f"@{chat.username}" if hasattr(chat, 'username') and chat.username else str(event.chat_id)
        
        if current_chat in config['source_channels']:
            # 处理媒体组 (Album)
            if event.message.grouped_id:
                gid = event.message.grouped_id
                if gid not in album_cache:
                    album_cache[gid] = []
                    # 开启异步缓冲，等待 2 秒收集所有图片
                    asyncio.create_task(handle_album(gid, event.chat_id))
                album_cache[gid].append(event.message)
                return # 缓冲中，暂时不发送

            # 处理普通单条消息
            raw_text = event.message.message or getattr(event.message, 'caption', "")
            final_text = f"{clean_message_content(raw_text)}\n\n{config['ad_text']}"
            
            if event.message.media:
                await client.send_file(config['target_channel'], event.message.media, caption=final_text, parse_mode='md')
            else:
                await client.send_message(config['target_channel'], final_text, parse_mode='md')
            logger.info(f"📤 单条搬运成功: {current_chat}")
            
    except Exception as e:
        logger.error(f"❌ 搬运报错: {e}")

async def handle_album(gid, chat_id):
    """处理并合并媒体组发送"""
    await asyncio.sleep(2) # 等待 2 秒让消息收齐
    messages = album_cache.pop(gid, [])
    if not messages: return

    # 提取文案：通常媒体组的文案在第一张图
    caption = ""
    for msg in messages:
        if msg.message or getattr(msg, 'caption', ""):
            caption = msg.message or getattr(msg, 'caption', "")
            break
    
    final_text = f"{clean_message_content(caption)}\n\n{config['ad_text']}"
    
    # 合并发送：只有第一张图带文案，其余图片作为组发送
    await client.send_file(config['target_channel'], messages, caption=final_text, parse_mode='md')
    logger.info(f"📤 媒体组(Album)合并搬运成功")

# --- 6. 管理员输入处理 ---
@client.on(events.CallbackQuery())
async def callback_handler(event):
    data = event.data.decode()
    if data == "toggle":
        config['is_running'] = not config['is_running']
        await send_main_menu(event.chat_id)
    elif data in ["edit_ad", "add_src", "del_src", "edit_target"]:
        config['waiting_action'] = data
        await event.respond("✍️ 请输入相应内容：")

@client.on(events.NewMessage())
async def manager_input(event):
    if not event.is_private or event.text.startswith('/'): return
    action = config.get('waiting_action')
    if not action: return

    if action == "edit_ad": config['ad_text'] = event.text
    elif action == "add_src": 
        new_src = format_username(event.text)
        if new_src not in config['source_channels']: config['source_channels'].append(new_src)
    elif action == "edit_target": config['target_channel'] = format_username(event.text)
            
    config['waiting_action'] = None
    await send_main_menu(event.chat_id)

@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    if event.is_private: await send_main_menu(event.chat_id)

async def main():
    Thread(target=run_flask).start()
    await client.start(bot_token=BOT_TOKEN)
    logger.info("✅ v10 媒体组增强版上线")
    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
