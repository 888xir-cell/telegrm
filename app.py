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

# --- 2. 基础配置 ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

API_ID = int(os.getenv('TG_API_ID', '37132348'))
API_HASH = os.getenv('TG_API_HASH', 'abeefb9d7f75cff36be8052f9519cb5b')
BOT_TOKEN = os.getenv('TG_BOT_TOKEN', '7968296089:AAGknOWEh9q_3JO5DBGrWNPH-C9TlrWHnIA')

config = {
    "source_channels": ["@dashijian09"], 
    "target_channel": "@SoutheastAsianrevelations", 
    "ad_text": "🎀欢迎订阅频道： 投稿/商务@BBGS1688",
    "is_running": True,
    "waiting_action": None 
}

client = TelegramClient('ace_final_v7', API_ID, API_HASH)

# --- 3. 工具函数 ---
def format_username(input_str):
    """处理输入：将链接自动转化为 @username 格式"""
    name = input_str.strip()
    if 't.me/' in name:
        name = name.split('t.me/')[-1]
    name = name.replace('@', '')
    return f"@{name}"

def clean_message_content(text):
    """清洗逻辑：剔除原频道的引流信息"""
    if not text: return ""
    lines = text.split('\n')
    filtered_lines = [line for line in lines if not any(word in line for word in ["关注", "频道", "投稿", ">>"])]
    text = '\n'.join(filtered_lines)
    text = re.sub(r'https?://\S+|t\.me/\S+', '', text)
    return text.strip()

# --- 4. 菜单界面 ---
async def send_main_menu(chat_id):
    status = "✅ 运行中" if config['is_running'] else "🛑 已暂停"
    text = (f"🤖 **ACE 搬运机器人后台**\n\n"
            f"📈 状态: {status}\n"
            f"📡 监听: `{', '.join(config['source_channels'])}`\n"
            f"🎯 目标: `{config['target_channel']}`\n\n"
            f"📝 广告后缀: \n{config['ad_text']}")
    
    buttons = [
        [Button.inline("➕ 添加源频道", b"add_src"), Button.inline("➖ 删除源频道", b"del_src")],
        [Button.inline("🎯 修改目标频道", b"edit_target"), Button.inline("📢 修改广告语", b"edit_ad")],
        [Button.inline("⏯️ 启动/停止", b"toggle")]
    ]
    await client.send_message(chat_id, text, buttons=buttons)

# --- 5. 交互处理 ---
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
        await event.respond("📡 请发送源频道链接或 @用户名：")
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
        new_channel = format_username(event.text)
        if new_channel not in config['source_channels']:
            config['source_channels'].append(new_channel)
            await event.respond(f"✅ 已添加监听: {new_channel}")
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

# --- 6. 核心搬运逻辑 (补全 Markdown 解析) ---
@client.on(events.NewMessage())
async def forwarder(event):
    if not config['is_running'] or event.is_private: return
    
    try:
        chat = await event.get_chat()
        current_chat = f"@{chat.username}" if hasattr(chat, 'username') and chat.username else str(event.chat_id)
        
        if current_chat in config['source_channels']:
            raw_text = event.message.text or event.message.caption or ""
            cleaned = clean_message_content(raw_text)
            # 拼接广告后缀
            final = f"{cleaned}\n\n{config['ad_text']}"
            
            # 使用 parse_mode='md' 确保 @用户名 能够自动识别为蓝色链接
            if event.message.media:
                await client.send_file(config['target_channel'], event.message.media, caption=final, parse_mode='md')
            else:
                await client.send_message(config['target_channel'], final, parse_mode='md')
            logger.info(f"📤 搬运成功: {current_chat} -> {config['target_channel']}")
    except Exception as e:
        logger.error(f"❌ 搬运出错: {e}")

@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    if event.is_private: await send_main_menu(event.chat_id)

async def main():
    Thread(target=run_flask).start()
    await client.start(bot_token=BOT_TOKEN)
    logger.info("✅ 机器人全功能上线 (已支持蓝色链接解析)")
    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
