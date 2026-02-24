import os, asyncio, logging
from threading import Thread
from flask import Flask
from telethon import TelegramClient, events, Button

# --- 1. 配置区 (直接在这里填好，重启也不会丢！) ---
API_ID, API_HASH = 37132348, 'abeefb9d7f75cff36be8052f9519cb5b'
BOT_TOKEN = '7968296089:AAGknOWEh9q_3JO5DBGrWNPH-C9TlrWHnIA'
ADMIN_ID = 8119149388  # ✅ 你的主人 ID

# 📝 在这里直接改好你的默认设置
CONFIG = {
    "sources": ["@dashijian09", "@xoxokrk"], 
    "target": "@SoutheastAsianrevelations", 
    "ad": "🎀欢迎订阅频道： 投稿/商务@BBGS1688",
    "active": True
}

# --- 2. 暴力保活 (解决 Render 杀进程问题) ---
app = Flask(__name__)
@app.route('/')
def home(): return "OK", 200

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port, debug=False)

# 启动保活线程
Thread(target=run_flask, daemon=True).start()

# --- 3. 核心机器人逻辑 ---
client = TelegramClient('ace_final_v99', API_ID, API_HASH)

def get_menu_text():
    # 修复“绑定提醒显示”，确保这里直接抓取最新配置
    status = "✅ 运行中" if CONFIG['active'] else "❌ 已停止"
    src_str = ", ".join(CONFIG['sources']) if CONFIG['sources'] else "未设置"
    return (f"🤖 **ACE 搬运控制台 (配置已锁定)**\n\n"
            f"📈 状态: {status}\n"
            f"📡 监听: `{src_str}`\n"
            f"🎯 目标: `{CONFIG['target']}`\n\n"
            f"📝 广告语: \n{CONFIG['ad']}")

async def send_main_menu(chat_id):
    btns = [[Button.inline("➕ 添加源", b"add"), Button.inline("➖ 清空源", b"clear")],
            [Button.inline("🎯 修改目标", b"target"), Button.inline("📢 修改广告", b"ad")],
            [Button.inline("⏯️ 启动/停止", b"toggle")]]
    await client.send_message(chat_id, get_menu_text(), buttons=btns)

@client.on(events.CallbackQuery())
async def cb_handler(event):
    if event.sender_id != ADMIN_ID:
        return await event.answer("❌ 你不是管理员", alert=True)
    
    data = event.data.decode()
    await event.answer()
    
    if data == "toggle":
        CONFIG['active'] = not CONFIG['active']
        await event.edit(get_menu_text(), buttons=event.reply_markup)
    elif data == "clear":
        CONFIG['sources'] = []
        await event.edit(get_menu_text(), buttons=event.reply_markup)
    else:
        # 进入输入模式
        event.sender.waiting_for = data
        await event.respond(f"✍️ 请输入要修改的内容：")

@client.on(events.NewMessage(incoming=True, func=lambda e: e.is_private))
async def input_handler(event):
    if event.sender_id != ADMIN_ID or event.text.startswith('/'): return
    
    mode = getattr(event.sender, 'waiting_for', None)
    if not mode: return
    
    if mode == "add": CONFIG['sources'].append(event.text.strip())
    elif mode == "target": CONFIG['target'] = event.text.strip()
    elif mode == "ad": CONFIG['ad'] = event.text.strip()
    
    event.sender.waiting_for = None
    await event.respond("✅ 设置已同步！")
    await send_main_menu(event.chat_id)

@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    if event.sender_id == ADMIN_ID:
        await send_main_menu(event.chat_id)

# --- 4. 启动 ---
async def main():
    print("🛰️ 正在强制连接 Telegram...")
    await client.start(bot_token=BOT_TOKEN)
    print("✅ 机器人已完全就绪！")
    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
