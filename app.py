import os
import asyncio
import logging
import re
from telethon import TelegramClient, events, Button

# --- 基础配置 ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 从环境变量获取凭证
API_ID = int(os.getenv('TG_API_ID', '37132348'))
API_HASH = os.getenv('TG_API_HASH', 'abeefb9d7f75cff36be8052f9519cb5b')
BOT_TOKEN = os.getenv('TG_BOT_TOKEN', '7968296089:AAGknOWEh9q_3JO5DBGrWNPH-C9TlrWHnIA')

# 机器人运行配置
config = {
    "source_channels": ["@dashijian09"], # 监听的频道
    "target_channel": "@SoutheastAsianrevelations", # 目标频道
    "ad_text": "欢迎关注 @SoutheastAsianrevelations 获取更多精彩内容！",
    "block_words": [], # 初始设为空，防止误杀导致无法搬运
    "is_running": True
}

client = TelegramClient('ace_transfer_session', API_ID, API_HASH)

# --- 菜单界面模块 ---
async def send_main_menu(chat_id):
    status = "✅ 运行中" if config['is_running'] else "🛑 已暂停"
    text = (f"🤖 **ACE 搬运机器人管理后台**\n\n"
            f"📈 **当前状态**: {status}\n"
            f"📢 **监听频道**: `{', '.join(config['source_channels'])}`\n"
            f"🎯 **目标频道**: `{config['target_channel']}`\n"
            f"🚫 **过滤规则**: {len(config['block_words'])} 个关键词")
    
    buttons = [
        [Button.inline("➕ 增加源频道", b"add_src"), Button.inline("➖ 删除源频道", b"del_src")],
        [Button.inline("📢 修改广告语", b"edit_ad"), Button.inline("🚫 设置屏蔽词", b"edit_block")],
        [Button.inline("⏯️ 启动/停止机器人", b"toggle")]
    ]
    await client.send_message(chat_id, text, buttons=buttons)

# --- 核心搬运逻辑 ---
@client.on(events.NewMessage())
async def handler(event):
    # 逻辑开关：暂停中或私聊消息不搬运
    if not config['is_running'] or event.is_private:
        return
    
    # 获取发送者信息
    chat = await event.get_chat()
    chat_username = f"@{chat.username}" if hasattr(chat, 'username') and chat.username else str(event.chat_id)
    
    # 匹配源频道
    if chat_username in config['source_channels']:
        logger.info(f"📩 收到源频道 {chat_username} 的新消息")
        
        text = event.message.text or event.message.caption or ""
        
        # 1. 关键词过滤逻辑
        if config['block_words'] and any(word in text.lower() for word in config['block_words']):
            logger.info("🚫 命中关键词屏蔽，跳过转发")
            return
            
        # 2. 拼接广告后缀
        full_text = f"{text}\n\n{config['ad_text']}"
        
        try:
            # 3. 执行转发
            if event.message.media:
                await client.send_file(config['target_channel'], event.message.media, caption=full_text)
            else:
                await client.send_message(config['target_channel'], full_text)
            logger.info(f"📤 成功搬运至 {config['target_channel']}")
        except Exception as e:
            logger.error(f"❌ 搬运失败，请检查机器人是否为目标频道管理员。错误: {e}")

# --- 按钮与指令交互 ---
@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    if event.is_private:
        await send_main_menu(event.chat_id)

@client.on(events.CallbackQuery())
async def callback_query_handler(event):
    if event.data == b"toggle":
        config['is_running'] = not config['is_running']
        await event.answer(f"状态已切换")
        await send_main_menu(event.chat_id)
    elif event.data == b"add_src":
        await event.respond("请直接发送要绑定的频道用户名（如 @chan123）")

async def main():
    await client.start(bot_token=BOT_TOKEN)
    logger.info("✅ 机器人已上线并处于监听状态")
    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
