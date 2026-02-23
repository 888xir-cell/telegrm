import os
import asyncio
import logging
import re
from threading import Thread
from flask import Flask
from telethon import TelegramClient, events, Button

# --- 1. 解决 Render 假死与端口报错 ---
server = Flask('')

@server.route('/')
def home():
    return "Bot is running!"

def run_flask():
    # 绑定 10000 端口，解决 Render 健康检查失败问题
    server.run(host='0.0.0.0', port=10000)

# --- 2. 基础日志与环境变量配置 ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

API_ID = int(os.getenv('TG_API_ID', '37132348'))
API_HASH = os.getenv('TG_API_HASH', 'abeefb9d7f75cff36be8052f9519cb5b')
BOT_TOKEN = os.getenv('TG_BOT_TOKEN', '7968296089:AAGknOWEh9q_3JO5DBGrWNPH-C9TlrWHnIA')

# 动态配置缓存
config = {
    "source_channels": ["@dashijian09"], 
    "target_channel": "@SoutheastAsianrevelations", 
    "ad_text": "✨ 关注我的频道获取更多资讯！",
    "block_words": [], 
    "is_running": True,
    "waiting_for_ad": None  # 用于防止 TimeoutError 的状态追踪
}

client = TelegramClient('ace_pro_cleaner', API_ID, API_HASH)

# --- 3. 消息清洗逻辑 (去广告/去@/去链接) ---
def clean_message_content(text):
    if not text:
        return ""
    
    # 剔除包含特定引流词的行 (如：关注吃瓜频道、投稿等)
    lines = text.split('\n')
    filtered_lines = [line for line in lines if not any(word in line for word in ["关注", "频道", "投稿", ">>"])]
    text = '\n'.join(filtered_lines)

    # 剔除所有 @用户名 和 链接
    text = re.sub(r'@\w+', '', text)
    text = re.sub(r'https?://\S+|t\.me/\S+', '', text)
    
    # 压缩多余换行
    text = re.sub(r'\n\s*\n', '\n\n', text)
    return text.strip()

# --- 4. 菜单界面 ---
async def send_main_menu(chat_id):
    status = "✅ 运行中" if config['is_running'] else "🛑 已暂停"
    text = (f"🤖 **ACE 搬运机器人后台**\n\n"
            f"📈 状态: {status}\n"
            f"📡 监听: `{', '.join(config['source_channels'])}`\n"
            f"🎯 目标: `{config['target_channel']}`\n\n"
            f"📝 当前广告后缀:\n`{config['ad_text']}`")
    
    buttons = [
        [Button.inline("➕ 添加源频道", b"add_src"), Button.inline("⏯️ 启动/停止", b"toggle")],
        [Button.inline("📢 修改广告语", b"edit_ad"), Button.inline("🚫 设置屏蔽词", b"edit_block")]
    ]
    await client.send_message(chat_id, text, buttons=buttons)

# --- 5. 核心事件处理器 ---

# A. 处理自动搬运
@client.on(events.NewMessage())
async def forward_handler(event):
    # 忽略私聊指令和停止状态
    if not config['is_running'] or event.is_private:
        return
    
    chat = await event.get_chat()
    chat_username = f"@{chat.username}" if hasattr(chat, 'username') and chat.username else str(event.chat_id)
    
    if chat_username in config['source_channels']:
        raw_text = event.message.text or event.message.caption or ""
        cleaned_text = clean_message_content(raw_text) # 执行清洗
        final_text = f"{cleaned_text}\n\n{config['ad_text']}"
        
        try:
            if event.message.media:
                await client.send_file(config['target_channel'], event.message.media, caption=final_text)
            else:
                await client.send_message(config['target_channel'], final_text)
            logger.info("📤 搬运并自动去重成功")
        except Exception as e:
            logger.error(f"❌ 搬运失败: {e}")

# B. 处理后台输入 (解决 TimeoutError)
@client.on(events.NewMessage())
async def input_listener(event):
    if not event.is_private or event.text.startswith('/'):
        return
        
    # 如果用户点击了修改广告语按钮
    if config.get('waiting_for_ad') == event.chat_id:
        config['ad_text'] = event.text
        config['waiting_for_ad'] = None 
        await event.respond(f"✅ 修改成功！新的广告后缀已生效。")
        await send_main_menu(event.chat_id)

# --- 6. 交互按钮回调 ---
@client.on(events.CallbackQuery())
async def callback_handler(event):
    if event.data == b"toggle":
        config['is_running'] = not config['is_running']
        await send_main_menu(event.chat_id)
    
    elif event.data == b"edit_ad":
        # 激活等待输入状态，不使用 conv 模式防止超时
        config['waiting_for_ad'] = event.chat_id
        await event.respond("✍️ 请直接发送你想要设置的**自定义广告后缀**（支持文字、链接和表情）：")

# --- 7. 启动指令 ---
@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    if event.is_private:
        await send_main_menu(event.chat_id)

async def main():
    Thread(target=run_flask).start() # 启动健康检查窗口
    await client.start(bot_token=BOT_TOKEN)
    logger.info("✅ 机器人已上线，对话超时修复已生效")
    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
