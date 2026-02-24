import os
import json
import logging
import asyncio
from datetime import datetime
from threading import Thread
from flask import Flask
from telethon import TelegramClient, events
from telethon.tl.functions.channels import JoinChannelRequest

# ================= 配置区（请务必修改这里） =================
API_ID = 1234567           # 填入你的 API ID (数字)
API_HASH = 'your_hash'     # 填入你的 API HASH (字符串)
BOT_TOKEN = 'your_token'   # 填入你的 Bot Token
ADMIN_ID = 12345678        # 填入你的 Telegram 数字 ID
# =========================================================

# 初始化日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 配置存储
CONFIG_FILE = 'config.json'
def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f: return json.load(f)
    return {'source_channels': [], 'target_channel': '', 'ad_text': '\n\n更多精彩内容关注：@BBGS1688'}

config = load_config()
def save_config():
    with open(CONFIG_FILE, 'w') as f: json.dump(config, f)

# Flask 用于保活 (Keep-alive)
app = Flask('')
@app.route('/')
def home(): return "OK"

def run_flask():
    app.run(host='0.0.0.0', port=10000)

# 初始化机器人客户端
client = TelegramClient('bot_session', API_ID, API_HASH)

# 自动加入频道的函数
async def auto_join(channel_username):
    try:
        clean_name = channel_username.replace('@', '').strip()
        await client(JoinChannelRequest(clean_name))
        return True, f"✅ 已成功自动加入并开始监听: @{clean_name}"
    except Exception as e:
        return False, f"⚠️ 无法自动加入 @{clean_name}: {str(e)}\n(请确保频道公开，或手动拉我入群)"

# 媒体组合并缓存
album_cache = {}

@client.on(events.NewMessage(chats=config.get('source_channels', [])))
async def handler(event):
    if not config['target_channel']: return
    
    # 自动处理媒体组 (Album)
    if event.grouped_id:
        gid = event.grouped_id
        if gid not in album_cache:
            album_cache[gid] = {'messages': [], 'timer': None}
        
        album_cache[gid]['messages'].append(event.message)
        
        if album_cache[gid]['timer']: album_cache[gid]['timer'].cancel()
        
        async def send_album(g_id):
            await asyncio.sleep(2) # 等待2秒确保收集齐所有图片
            msgs = album_cache[g_id]['messages']
            caption = (msgs[0].text or "") + config['ad_text']
            await client.send_file(config['target_channel'], msgs, caption=caption, parse_mode='md')
            logger.info("🚢 媒体组(Album)合并搬运成功")
            del album_cache[g_id]
            
        album_cache[gid]['timer'] = asyncio.create_task(send_album
