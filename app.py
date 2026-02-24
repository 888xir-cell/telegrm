import os, asyncio, logging
from threading import Thread
from flask import Flask
from telethon import TelegramClient, events, Button

# --- 1. 基础配置 ---
API_ID, API_HASH = 37132348, 'abeefb9d7f75cff36be8052f9519cb5b'
BOT_TOKEN = '7968296089:AAGknOWEh9q_3JO5DBGrWNPH-C9TlrWHnIA'
ADMIN_ID = 8119149388 

# 🔥 核心补救：手动把你的配置写死在代码里，这样重启也不会丢了
config = {
    "source_channels": ["@dashijian09", "@xoxokrk"], # 在这里直接改，重启也有效
    "target_channel": "@SoutheastAsianrevelations", 
    "ad_text": "🎀欢迎订阅频道： 投稿/商务@BBGS1688",
    "is_running": True, "waiting_action": None 
}

# --- 2. 强力保活 ---
app = Flask(__name__)
@app.route('/')
def h(): return "LIVE", 200

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

Thread(target=run_web, daemon=True).start()

# --- 3. 机器人逻辑 ---
client = TelegramClient('ace_stable_v20', API_ID, API_HASH)

def get_panel_text():
    # 修复你说的“绑定提醒显示”，确保这里显示的是最新设置
    status = "✅ 运行中" if config['is_running'] else "❌ 已停止"
    sources = ", ".join(config['source_channels'])
    return (f"🤖 **ACE 搬运助手 (已修复版)**\n\n"
            f"📈 状态: {status}\n"
            f"📡 监听: `{sources}`\n"
            f"🎯 目标: `{config['target_channel']}`\n\n"
            f"📝 广告: {config['ad_text']}")

async def show_menu(chat_id):
    btns = [[Button.inline("➕ 添加源", b"add_src"), Button.inline("➖ 清空源", b"clear_src")],
            [Button.inline("🎯 修改目标", b"edit_target"), Button.inline("📢 广告语", b"edit_ad")],
            [Button.inline("⏯️ 启动/停止", b"toggle")]]
    await client.send_message(chat_id, get_panel_text(), buttons=btns)

@client.on(events.CallbackQuery())
async def cb_handler(event):
    if event.sender_id != ADMIN_ID: return
    await event.answer()
    data = event.data.decode()
    
    if data == "toggle":
        config['is_running'] = not config['is_running']
        await event.edit(get_panel_text(), buttons=event.reply_markup)
    elif data == "clear_src":
        config['source_channels'] = []
        await event.edit(get_panel_text(), buttons=event.reply_markup)
    else:
        config['waiting_action'] = data
        await event.respond(f"✍️ 请输入要更新的内容：\n(当前操作: {data})")

@client.on(events.NewMessage(incoming=True, func=lambda e: e.is_private))
async def input_handler(event):
    if event.sender_id != ADMIN_ID or not config['waiting_action']: return
    
    val = event.text.strip()
    if config['waiting_action'] == "add_src":
        config['source_channels'].append(val)
    elif config['waiting_action'] == "edit_target":
        config['target_channel'] = val
    elif config['waiting_action'] == "edit_ad":
        config['ad_text'] = val
        
    config['waiting_action'] = None
    await event.respond("✅ 设置已保存！新配置如下：")
    await show_menu(event.chat_id)

@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    if event.sender_id == ADMIN_ID: await show_menu(event.chat_id)

# --- 启动 ---
async def main():
    await client.start(bot_token=BOT_TOKEN)
    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
