import os
import asyncio
import logging
import re
from threading import Thread
from flask import Flask
from telethon import TelegramClient, events, Button

# --- 1. Render 健康检查 ---
server = Flask('')
@server.route('/')
def home(): return "Bot is running!"
def run_flask(): server.run(host='0.0.0.0', port=10000)

# --- 2. 配置与初始化 ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

API_ID = int(os.getenv('TG_API_ID', '37132348'))
API_HASH = os.getenv('TG_API_HASH', 'abeefb9d7f75cff36be8052f9519cb5b')
BOT_TOKEN = os.getenv('TG_BOT_TOKEN', '7968296089:AAGknOWEh9q_3JO5DBGrWNPH-C9TlrWHnIA')

# 核心配置存储
config = {
    "source_channels": ["@dashijian09"], 
    "target_channel": "@SoutheastAsianrevelations", 
    "ad_text": "✨ 关注我的频道获取更多资讯！",
    "is_running": True,
    "waiting_action": None 
}

client = TelegramClient('ace_pro_v6', API_ID, API_HASH)

# --- 3. 工具函数 ---
def format_username(input_str):
    """自动将链接或纯文字转换为 @username 格式"""
    name = input_str.strip()
    if 't.me/' in name:
        name = name.split('t.me/')[-1]
    name = name.replace('@', '')
    return f"@{name}"

def clean_message_content(text):
    if not text: return ""
    lines = text.split('\n')
    filtered_lines = [line for line in lines if not any(word in line for word in ["关注", "频道", "投稿", ">>"])]
    text = '\n'.join(filtered_lines)
    text = re.sub(r'@\w+', '', text)
    text = re.sub(r'https?://\S+|t\.me/\S+', '', text)
    return text.strip()

# --- 4. 增强版菜单界面 ---
async def send_main_menu(chat_id):
    status = "✅ 运行中" if config['is_running'] else "🛑 已暂停"
    text = (f"🤖 **ACE 搬运机器人后台**\n\n"
            f"📈 状态: {status}\n"
            f"📡 监听: `{', '.join(config['source_channels'])}`\n"
            f"🎯 目标: `{config['target_channel']}`\n\n"
            f"📝 广告后缀: `{config['ad_text']}`")
    
    buttons = [
        [Button.inline("➕ 添加源频道", b"add_src"), Button.inline("➖ 删除源频道", b"del_src")],
        [Button.inline("🎯 修改目标频道", b"edit_target"), Button.inline("📢 修改广告语", b"edit_ad")],
        [Button.inline("⏯️ 启动/停止", b"toggle")]
    ]
    await client.send_message(chat_id, text, buttons=buttons)

# --- 5. 事件处理逻辑 ---

@client.on(events.CallbackQuery())
async def callback_handler(event):
    if event.data == b"toggle":
        config['is_running'] = not config['is_running']
        await send_main_menu(event.chat_id)
    elif event.data == b"edit_ad":
        config['waiting_action'] = "edit_ad"
        await event.respond("✍️ 请发送新的**广告后缀**：")
    elif event.data == b"add_src":
        config['waiting_action'] = "add_src"
        await event.respond("📡 请发送源频道（支持链接或 @用户名）：")
    elif event.data == b"del_src":
        config['waiting_action'] = "del_src"
        await event.respond("➖ 请发送要删除的源频道用户名：")
    elif event.data == b"edit_target":
        config['waiting_action'] = "edit_target"
        await event.respond("🎯 请发送新的**目标频道**用户名（如 `@my_chan`）：")

@client.on(events.NewMessage())
async def manager_input(event):
    if not event.is_private or event.text.startswith('/'): return
    action = config.get('waiting_action')
    if not action: return

    if action == "edit_ad":
        config['ad_text'] = event.text
        await event.respond("✅ 广告语已更新")
    elif action == "add_src":
        new_channel = format_username(event.text) # 自动识别格式
        if new_channel not in config['source_channels']:
            config['source_channels'].append(new_channel)
            await event.respond(f"✅ 已添加监听: {new_channel}")
        else:
            await event.respond("⚠️ 频道已在列表中")
    elif action == "del_src":
        target = format_username(event.text)
        if target in config['source_channels']:
            config['source_channels'].remove(target)
            await event.respond(f"🗑️ 已删除监听: {target}")
    elif action == "edit_target":
        config['target_channel'] = format_username(event.text)
        await event.respond(f"✅ 目标频道已更换为: {config['target_channel']}")
            
    config['waiting_action'] = None
    await send_main_menu(event.chat_id)

# --- 6. 核心搬运监听 (带诊断功能) ---
@client.on(events.NewMessage())
async def forwarder(event):
    if not config['is_running'] or event.is_private: return
    
    try:
        chat = await event.get_chat()
        # 日志诊断：打印所有听到的消息来源
        current_chat = f"@{chat.username}" if hasattr(chat, 'username') and chat.username else str(event.chat_id)
        logger.info(f"📡 监听到频道消息: {current_chat}") 
        
        if current_chat in config['source_channels']:
            raw_text = event.message.text or event.message.caption or ""
            cleaned = clean_message_content(raw_text)
            final = f"{cleaned}\n\n{config['ad_text']}"
            
            if event.message.media:
                await client.send_file(config['target_channel'], event.message.media, caption=final)
            else:
                await client.send_message(config['target_channel'], final)
            logger.info(f"📤 成功从 {current_chat} 搬运到 {config['target_channel']}")
    except Exception as e:
        logger.error(f"❌ 搬运过程出错: {e}")

@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    if event.is_private: await send_main_menu(event.chat_id)

async def main():
    Thread(target=run_flask).start()
    await client.start(bot_token=BOT_TOKEN)
    logger.info("✅ 机器人全功能增强版已上线")
    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
