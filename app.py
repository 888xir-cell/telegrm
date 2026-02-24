import os
import json
import logging
import asyncio
from datetime import datetime
from threading import Thread
from flask import Flask
from telethon import TelegramClient, events
from telethon.tl.functions.channels import JoinChannelRequest

# ================= 配置区（已根据截图为你填好） =================
API_ID = 37132488          # 已填入
API_HASH = 'abeefb9d7f75cff36be8052f9519cb5b' # 已填入
BOT_TOKEN = '7968296089:AAGknOWEh9q_3JO5DBGrWNPH-C9TlrWHnIA' # 已填入
ADMIN_ID = 7443831844      # 请确保这是你的正确数字ID
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
            await asyncio.sleep(2) 
            msgs = album_cache[g_id]['messages']
            caption = (msgs[0].text or "") + config['ad_text']
            await client.send_file(config['target_channel'], msgs, caption=caption, parse_mode='md')
            logger.info("🚢 媒体组(Album)合并搬运成功")
            del album_cache[g_id]
            
        album_cache[gid]['timer'] = asyncio.create_task(send_album(gid))
    else:
        new_text = (event.text or "") + config['ad_text']
        await client.send_message(config['target_channel'], new_text, file=event.media, parse_mode='md')
        logger.info("📝 单条消息搬运成功")

# 管理菜单
@client.on(events.NewMessage(pattern='/start', from_users=ADMIN_ID))
async def start_cmd(event):
    await event.reply("欢迎使用搬运助手！\n\n当前源频道：" + str(config['source_channels']) + 
                     "\n目标频道：" + str(config['target_channel']) + 
                     "\n\n使用 /add_source 添加搬运来源")

@client.on(events.NewMessage(pattern='/add_source', from_users=ADMIN_ID))
async def add_source(event):
    async with client.conversation(event.chat_id) as conv:
        await conv.send_message("请输入要搬运的源频道用户名（带@）：")
        res = await conv.get_response()
        name = res.text.strip()
        
        success, msg = await auto_join(name)
        await conv.send_message(msg)
        
        if name not in config['source_channels']:
            config['source_channels'].append(name)
            save_config()

async def main():
    Thread(target=run_flask).start()
    await client.start(bot_token=BOT_TOKEN)
    logger.info("✅ v10 增强版上线，心跳保活已就绪")
    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
