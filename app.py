import os, asyncio, logging
from threading import Thread
from flask import Flask
from telethon import TelegramClient, events, Button
from telethon.tl.functions.channels import JoinChannelRequest

# --- 1. 基础配置 (严格锁定你的 ID) ---
API_ID, API_HASH = 37132348, 'abeefb9d7f75cff36be8052f9519cb5b'
BOT_TOKEN = '7968296089:AAGknOWEh9q_3JO5DBGrWNPH-C9TlrWHnIA'
ADMIN_ID = 8119149388  # ✅ 确认为你的 ID

config = {
    "source_channels": ["@dashijian09", "@xoxokrk"], 
    "target_channel": "@SoutheastAsianrevelations", 
    "ad_text": "🎀欢迎订阅频道： 投稿/商务@BBGS1688",
    "is_running": True, "waiting_action": None 
}

# --- 2. 暴力保活 (解决 Render Port scan timeout) ---
app = Flask(__name__)
@app.route('/')
def health(): return "OK", 200

def run_web():
    # 强制立刻启动，不带任何延迟
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

# 🔥 核心改动：在所有逻辑开始前，先启动 Web 服务
web_thread = Thread(target=run_web, daemon=True)
web_thread.start()

# --- 3. 机器人主体 ---
client = TelegramClient('ace_final_v13', API_ID, API_HASH)

@client.on(events.CallbackQuery())
async def cb_handler(event):
    # 增加弹窗自检，如果 ID 不对会直接告诉你
    if event.sender_id != ADMIN_ID:
        return await event.answer(f"❌ 拒绝访问！你的 ID 是: {event.sender_id}", alert=True)
    
    await event.answer()
    data = event.data.decode()
    if data == "toggle":
        config['is_running'] = not config['is_running']
        await send_panel(event.chat_id)
    else:
        config['waiting_action'] = data
        await event.respond("✍️ 身份已确认，请输入内容：")

async def send_panel(chat_id):
    btns = [[Button.inline("➕ 添加源", b"add_src"), Button.inline("➖ 删除源", b"del_src")],
            [Button.inline("🎯 修改目标", b"edit_target"), Button.inline("📢 广告语", b"edit_ad")],
            [Button.inline("⏯️ 启动/停止", b"toggle")]]
    await client.send_message(chat_id, f"🤖 **ACE 控制台**\n管理员: `{ADMIN_ID}`", buttons=btns)

@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    if event.sender_id == ADMIN_ID: await send_panel(event.chat_id)

# (其他搬运逻辑保持不变...)

async def main():
    print("🚀 正在连接 Telegram...")
    await client.start(bot_token=BOT_TOKEN)
    print("✅ 机器人已完全就绪")
    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
