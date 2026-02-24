import os, asyncio, logging, re, sys
from threading import Thread
from flask import Flask
from telethon import TelegramClient, events, Button
from telethon.tl.functions.channels import JoinChannelRequest

# --- 1. 基础配置 (已严格锁定你的 ID: 8119149388) ---
API_ID = 37132348
API_HASH = 'abeefb9d7f75cff36be8052f9519cb5b'
BOT_TOKEN = '7968296089:AAGknOWEh9q_3JO5DBGrWNPH-C9TlrWHnIA'
ADMIN_ID = 8119149388  # ✅ 确认为你的真实 ID

config = {
    "source_channels": ["@dashijian09", "@xoxokrk"], 
    "target_channel": "@SoutheastAsianrevelations", 
    "ad_text": "🎀欢迎订阅频道： 投稿/商务@BBGS1688",
    "is_running": True, "waiting_action": None 
}

# --- 2. 强力保活：解决 Render 的红字 Port scan timeout ---
app = Flask(__name__)
@app.route('/')
def home(): return "Bot is running perfectly!"

def start_flask():
    # 强制监听 Render 指定的 PORT
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- 3. 核心客户端 (针对 DC 迁移优化) ---
client = TelegramClient('ace_stable_session', API_ID, API_HASH)
album_cache = {}

# 媒体组处理
async def handle_album(gid):
    await asyncio.sleep(2)
    msgs = album_cache.pop(gid, [])
    if not msgs: return
    cap = (next((m.message for m in msgs if m.message), "")) + "\n\n" + config['ad_text']
    await client.send_file(config['target_channel'], msgs, caption=cap)

@client.on(events.NewMessage())
async def forwarder(event):
    if not config['is_running'] or event.is_private: return
    try:
        chat = await event.get_chat()
        curr = f"@{chat.username}" if hasattr(chat, 'username') and chat.username else str(event.chat_id)
        if curr in config['source_channels']:
            if event.message.grouped_id:
                gid = event.message.grouped_id
                if gid not in album_cache:
                    album_cache[gid] = []
                    asyncio.create_task(handle_album(gid))
                album_cache[gid].append(event.message)
                return 
            txt = (event.message.message or "") + "\n\n" + config['ad_text']
            await client.send_message(config['target_channel'], txt, file=event.message.media)
    except Exception as e: logging.error(f"搬运异常: {e}")

# --- 4. 管理面板 (带 ID 自检功能) ---
async def show_menu(chat_id):
    btns = [[Button.inline("➕ 添加源", b"add_src"), Button.inline("➖ 删除源", b"del_src")],
            [Button.inline("🎯 修改目标", b"edit_target"), Button.inline("📢 广告语", b"edit_ad")],
            [Button.inline("⏯️ 启动/停止", b"toggle")]]
    await client.send_message(chat_id, f"🤖 **ACE 搬运助手**\n已识别管理员: `{ADMIN_ID}`\n如点击没反应，请先发 /start", buttons=btns)

@client.on(events.CallbackQuery())
async def cb_handler(event):
    # 这里的判断会直接在弹窗里告诉你谁在点
    if event.sender_id != ADMIN_ID:
        return await event.answer(f"❌ 拒绝! 你的ID是: {event.sender_id}", alert=True)
    
    await event.answer()
    data = event.data.decode()
    if data == "toggle": 
        config['is_running'] = not config['is_running']
        await show_menu(event.chat_id)
    else: 
        config['waiting_action'] = data
        await event.respond("✍️ 身份已确认，请输入内容：")

@client.on(events.NewMessage(incoming=True, func=lambda e: e.is_private))
async def input_handler(event):
    if event.sender_id != ADMIN_ID or event.text.startswith('/'): return
    act = config.get('waiting_action')
    if not act: return
    
    if act == "add_src":
        try:
            await client(JoinChannelRequest(event.text.strip()))
            config['source_channels'].append(event.text.strip())
            await event.respond(f"✅ 已添加源: {event.text.strip()}")
        except: await event.respond("⚠️ 加入失败，请检查频道名")
    elif act == "edit_ad": config['ad_text'] = event.text
    elif act == "edit_target": config['target_channel'] = event.text
    
    config['waiting_action'] = None
    await show_menu(event.chat_id)

@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    if event.sender_id == ADMIN_ID: await show_menu(event.chat_id)

# --- 5. 启动入口 ---
async def main():
    # 1. 立即启动 Flask，抢在 Render 扫描前占领端口
    flask_thread = Thread(target=start_flask, daemon=True)
    flask_thread.start()
    
    # 2. 启动 Telegram 客户端
    try:
        await client.start(bot_token=BOT_TOKEN)
        logging.info("🚀 终极解锁版已上线，管理员: 8119149388")
        await client.run_until_disconnected()
    except Exception as e:
        logging.error(f"启动失败: {e}")

if __name__ == '__main__':
    asyncio.run(main())
