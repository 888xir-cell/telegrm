import os, asyncio, logging, re
from threading import Thread
from flask import Flask
from telethon import TelegramClient, events, Button
from telethon.tl.functions.channels import JoinChannelRequest

# --- 1. 基础配置（已填入你的真实参数） ---
API_ID = 37132348
API_HASH = 'abeefb9d7f75cff36be8052f9519cb5b'
BOT_TOKEN = '7968296089:AAGknOWEh9q_3JO5DBGrWNPH-C9TlrWHnIA'
ADMIN_ID = 8119149388  # ✅ 你的真实 ID，再也不会报错“不是管理员”了

config = {
    "source_channels": ["@dashijian09", "@xoxokrk"], 
    "target_channel": "@SoutheastAsianrevelations", 
    "ad_text": "🎀欢迎订阅频道： 投稿/商务@BBGS1688",
    "is_running": True, 
    "waiting_action": None 
}

# --- 2. 保活服务器（解决 Render 端口扫描问题） ---
app = Flask('')
@app.route('/')
def home(): return "OK"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- 3. 核心功能逻辑 ---
client = TelegramClient('ace_final_v11', API_ID, API_HASH)
album_cache = {}

async def handle_album(gid):
    await asyncio.sleep(2)
    msgs = album_cache.pop(gid, [])
    if not msgs: return
    cap = (next((m.message for m in msgs if m.message), "")) + "\n\n" + config['ad_text']
    await client.send_file(config['target_channel'], msgs, caption=cap)
    logging.info("📤 媒体组搬运成功")

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
            logging.info(f"📤 单条搬运成功: {curr}")
    except Exception as e: logging.error(f"搬运异常: {e}")

# --- 4. 管理面板交互（修复按钮转圈和权限问题） ---
async def show_menu(chat_id):
    btns = [[Button.inline("➕ 添加源", b"add_src"), Button.inline("➖ 删除源", b"del_src")],
            [Button.inline("🎯 修改目标", b"edit_target"), Button.inline("📢 广告语", b"edit_ad")],
            [Button.inline("⏯️ 启动/停止", b"toggle")]]
    await client.send_message(chat_id, f"🤖 **ACE 搬运助手**\n\n当前状态: {'✅ 运行中' if config['is_running'] else '🛑 已停止'}\n当前 ID: `{ADMIN_ID}` (已授权)", buttons=btns)

@client.on(events.CallbackQuery())
async def cb_handler(event):
    if event.sender_id != ADMIN_ID: 
        return await event.answer("⚠️ 权限拒绝：您不是管理员", alert=True)
    
    await event.answer() # 消除按钮转圈
    data = event.data.decode()
    if data == "toggle": 
        config['is_running'] = not config['is_running']
        await show_menu(event.chat_id)
    else: 
        config['waiting_action'] = data
        await event.respond("✍️ 请直接发送内容给我：")

@client.on(events.NewMessage(incoming=True, func=lambda e: e.is_private))
async def input_handler(event):
    if event.sender_id != ADMIN_ID or event.text.startswith('/'): return
    act = config.get('waiting_action')
    if not act: return
    
    if act == "add_src":
        src = event.text.strip()
        try:
            await client(JoinChannelRequest(src)) # 自动尝试加入
            if src not in config['source_channels']: config['source_channels'].append(src)
            await event.respond(f"✅ 已成功监听: {src}")
        except: await event.respond(f"⚠️ 无法自动加入 {src}，请确保频道公开或手动拉机器人入群")
    elif act == "edit_ad": config['ad_text'] = event.text
    elif act == "edit_target": config['target_channel'] = event.text
    
    config['waiting_action'] = None
    await show_menu(event.chat_id)

@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    if event.sender_id == ADMIN_ID: await show_menu(event.chat_id)

# --- 5. 启动入口 ---
async def main():
    Thread(target=run_flask).start()
    await client.start(bot_token=BOT_TOKEN)
    logging.info("🚀 终极解锁版已上线，管理员 ID: 8119149388")
    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
