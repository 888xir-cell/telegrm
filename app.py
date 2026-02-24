import os, asyncio, logging, sys
from threading import Thread
from flask import Flask
from telethon import TelegramClient, events, Button

# --- 1. 配置区 ---
API_ID, API_HASH = 37132348, 'abeefb9d7f75cff36be8052f9519cb5b'
BOT_TOKEN = '7968296089:AAGknOWEh9q_3JO5DBGrWNPH-C9TlrWHnIA'
ADMIN_ID = 8119149388  # ✅ 你的 ID

config = {
    "source_channels": ["@dashijian09", "@xoxokrk"], 
    "target_channel": "@SoutheastAsianrevelations", 
    "ad_text": "🎀欢迎订阅频道： 投稿/商务@BBGS1688",
    "is_running": True
}

# --- 2. 极速保活 (让 Render 闭嘴) ---
app = Flask(__name__)
@app.route('/')
def h(): return "READY", 200

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- 3. 机器人核心 ---
# 🔥 每次启动换个新名字，防止被旧文件锁死
client = TelegramClient('ace_power_v15', API_ID, API_HASH)

async def send_menu(chat_id):
    btns = [[Button.inline("➕ 添加源", b"add_src"), Button.inline("➖ 删除源", b"del_src")],
            [Button.inline("⏯️ 启动/停止", b"toggle")]]
    await client.send_message(chat_id, f"🚀 **ACE 系统已就绪**\n主人 ID: `{ADMIN_ID}`", buttons=btns)

@client.on(events.CallbackQuery())
async def handler(event):
    if event.sender_id != ADMIN_ID:
        return await event.answer(f"❌ 权限拒绝 (ID:{event.sender_id})", alert=True)
    await event.answer("✅ 身份验证通过")
    # 逻辑处理...

@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    if event.sender_id == ADMIN_ID: await send_menu(event.chat_id)

async def main():
    print("🛰️ 正在强制连接 Telegram...")
    await client.start(bot_token=BOT_TOKEN)
    print("✅ 机器人已完全就绪！")
    await client.run_until_disconnected()

if __name__ == '__main__':
    # 先开 Web 端口
    Thread(target=run_web, daemon=True).start()
    # 再开机器人
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"致命错误: {e}")
