import os, asyncio, logging, sys
from threading import Thread
from flask import Flask
from telethon import TelegramClient, events, Button
from telethon.tl.functions.channels import JoinChannelRequest

# --- 1. 暴力初始化配置 ---
API_ID = 37132348
API_HASH = 'abeefb9d7f75cff36be8052f9519cb5b'
BOT_TOKEN = '7968296089:AAGknOWEh9q_3JO5DBGrWNPH-C9TlrWHnIA'
ADMIN_ID = 8119149388  # ✅ 严格锁定你的 ID

config = {
    "source_channels": ["@dashijian09", "@xoxokrk"], 
    "target_channel": "@SoutheastAsianrevelations", 
    "ad_text": "🎀欢迎订阅频道： 投稿/商务@BBGS1688",
    "is_running": True, "waiting_action": None 
}

# --- 2. 核心保活：必须最先启动 ---
app = Flask(__name__)
@app.route('/')
def health(): return "STABLE", 200

def run_web():
    port = int(os.environ.get("PORT", 10000))
    # 使用极简模式启动，确保不阻塞
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

# 立即启动 Web 服务，不让 Render 等
Thread(target=run_web, daemon=True).start()

# --- 3. 机器人逻辑 ---
client = TelegramClient('ace_final_v12', API_ID, API_HASH)
album_cache = {}

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
    except Exception: pass

# --- 4. 管理面板 (权限逻辑重构) ---
async def send_panel(chat_id):
    btns = [[Button.inline("➕ 添加源", b"add_src"), Button.inline("➖ 删除源", b"del_src")],
            [Button.inline("🎯 修改目标", b"edit_target"), Button.inline("📢 广告语", b"edit_ad")],
            [Button.inline("⏯️ 启动/停止", b"toggle")]]
    await client.send_message(chat_id, f"🤖 **ACE 控制台**\n管理员已锁定: `{ADMIN_ID}`", buttons=btns)

@client.on(events.CallbackQuery())
async def cb_handler(event):
    # 如果点按钮的人 ID 不对，直接弹窗警告
    if event.sender_id != ADMIN_ID:
        return await event.answer(f"❌ 警告：你不是主人！(你的ID:{event.sender_id})", alert=True)
    
    await event.answer()
    data = event.data.decode()
    if data == "toggle": 
        config['is_running'] = not config['is_running']
        await send_panel(event.chat_id)
    else: 
        config['waiting_action'] = data
        await event.respond("✍️ 请输入新内容：")

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
        except: await event.respond("⚠️ 加入失败")
    elif act == "edit_ad": config['ad_text'] = event.text
    elif act == "edit_target": config['target_channel'] = event.text
    
    config['waiting_action'] = None
    await send_panel(event.chat_id)

@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    if event.sender_id == ADMIN_ID: await send_panel(event.chat_id)

# --- 5. 启动 ---
async def main():
    print("🚀 正在连接 Telegram...")
    await client.start(bot_token=BOT_TOKEN)
    print("✅ 机器人已完全就绪")
    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
