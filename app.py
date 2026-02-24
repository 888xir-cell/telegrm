import os
import asyncio
import logging
import re
from threading import Thread
from flask import Flask
from telethon import TelegramClient, events, Button
from telethon.tl.functions.channels import JoinChannelRequest

# --- 1. 基础配置 ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 已根据你的截图严格校对
API_ID = 37132348
API_HASH = 'abeefb9d7f75cff36be8052f9519cb5b'
BOT_TOKEN = '7968296089:AAGknOWEh9q_3JO5DBGrWNPH-C9TlrWHnIA'
ADMIN_ID = 8119149388  # ✅ 已修正为你的真实 ID

# 默认配置
config = {
    "source_channels": ["@dashijian09", "@xoxokrk"], 
    "target_channel": "@SoutheastAsianrevelations", 
    "ad_text": "🎀欢迎订阅频道： 投稿/商务@BBGS1688",
    "is_running": True,
    "waiting_action": None 
}

client = TelegramClient('ace_pro_final_v2', API_ID, API_HASH)

# --- 2. 菜单界面 ---
async def send_main_menu(chat_id):
    status = "✅ 运行中" if config['is_running'] else "🛑 已暂停"
    text = (f"🤖 **ACE 搬运机器人 (管理员已解锁)**\n\n"
            f"📈 状态: {status}\n"
            f"📡 监听: `{', '.join(config['source_channels'])}`\n"
            f"🎯 目标: `{config['target_channel']}`\n\n"
            f"📝 广告: \n{config['ad_text']}")
    buttons = [[Button.inline("➕ 添加源", b"add_src"), Button.inline("➖ 删除源", b"del_src")],
               [Button.inline("🎯 修改目标", b"edit_target"), Button.inline("📢 广告语", b"edit_ad")],
               [Button.inline("⏯️ 启动/停止", b"toggle")]]
    await client.send_message(chat_id, text, buttons=buttons)

# --- 3. 核心交互逻辑 ---
@client.on(events.CallbackQuery())
async def callback_handler(event):
    if event.sender_id != ADMIN_ID: 
        return await event.answer("⚠️ 您不是管理员", alert=True)
    
    await event.answer() # 消除按钮转圈
    data = event.data.decode()

    if data == "toggle":
        config['is_running'] = not config['is_running']
        await send_main_menu(event.chat_id)
    else:
        config['waiting_action'] = data
        await event.respond(f"✍️ ID已识别！请输入内容：")

@client.on(events.NewMessage(incoming=True, func=lambda e: e.is_private))
async def manager_input(event):
    if event.sender_id != ADMIN_ID or event.text.startswith('/'): return
    
    action = config.get('waiting_action')
    if not action: return 

    if action == "add_src":
        name = event.text.strip()
        if name not in config['source_channels']:
            config['source_channels'].append(name)
            await event.respond(f"✅ 已成功添加源: {name}")
    elif action == "edit_ad":
        config['ad_text'] = event.text
        await event.respond("✅ 广告语已更新")
    elif action == "edit_target":
        config['target_channel'] = event.text
        await event.respond(f"✅ 目标频道已修改")
    
    config['waiting_action'] = None 
    await send_main_menu(event.chat_id)

@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    if event.sender_id == ADMIN_ID:
        await send_main_menu(event.chat_id)

# (保活接口省略，保持不变)
async def main():
    await client.start(bot_token=BOT_TOKEN)
    logger.info("✅ 管理员 ID 修正版上线")
    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
