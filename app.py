#!/usr/bin/env python3
"""
Telegram 频道搬运机器人 - 可配置版本
"""

import os
import asyncio
import logging
import sys
import re
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def load_config():
    """加载配置，支持环境变量和默认值"""
    # Telegram API 配置（从环境变量获取）
    api_id = os.getenv('TG_API_ID', '37132348')
    api_hash = os.getenv('TG_API_HASH', 'abeefb9d7f75cff36be8052f9519cb5b')
    bot_token = os.getenv('TG_BOT_TOKEN', '7968296089:AAGknOWEh9q_3JO5DBGrWNPH-C9TlrWHnIA')
    
    # 频道配置（从环境变量获取，支持多个源频道）
    source_channels_env = os.getenv('SOURCE_CHANNELS', '@dashijian09')
    # 支持多个频道，用逗号分隔
    source_channels = [chan.strip() for chan in source_channels_env.split(',') if chan.strip()]
    
    target_channel = os.getenv('TARGET_CHANNEL', '@SoutheastAsianrevelations')
    ad_text = os.getenv('AD_TEXT', '欢迎关注 @SoutheastAsianrevelations 获取更多精彩内容！')
    
    return {
        'api_id': api_id,
        'api_hash': api_hash,
        'bot_token': bot_token,
        'source_channels': source_channels,
        'target_channel': target_channel,
        'ad_text': ad_text
    }

async def main():
    logger.info("🚀 启动 Telegram 频道搬运机器人")
    
    # 加载配置
    config = load_config()
    
    logger.info(f"📋 当前配置:")
    logger.info(f"   源频道: {config['source_channels']}")
    logger.info(f"   目标频道: {config['target_channel']}")
    logger.info(f"   广告语: {config['ad_text']}")
    
    if not all([config['api_id'], config['api_hash'], config['bot_token']]):
        logger.error("❌ 请设置环境变量: TG_API_ID, TG_API_HASH, TG_BOT_TOKEN")
        logger.info("💡 在 Hugging Face Spaces 的 Settings → Repository secrets 中添加:")
        logger.info("   TG_API_ID: 你的API ID")
        logger.info("   TG_API_HASH: 你的API Hash")
        logger.info("   TG_BOT_TOKEN: 你的Bot Token")
        return
    
    # 检查频道配置
    if not config['source_channels']:
        logger.error("❌ 请设置源频道")
        logger.info("💡 添加环境变量 SOURCE_CHANNELS，例如:")
        logger.info("   SOURCE_CHANNELS: @dashijian09")
        logger.info("   多个频道用逗号分隔: @channel1,@channel2")
        return
    
    if not config['target_channel']:
        logger.error("❌ 请设置目标频道")
        logger.info("💡 添加环境变量 TARGET_CHANNEL，例如:")
        logger.info("   TARGET_CHANNEL: @SoutheastAsianrevelations")
        return
    
    try:
        from telethon import TelegramClient, events
        
        client = TelegramClient('hf_bot', int(config['api_id']), config['api_hash'])
        
        await client.start(bot_token=config['bot_token'])
        logger.info("✅ Telegram 连接成功")
        
        @client.on(events.NewMessage(chats=config['source_channels']))
        async def handler(event):
            try:
                msg = event.message
                text = msg.text or msg.caption or ""
                
                if text:
                    # 移除链接（可选）
                    text = re.sub(r'https?://\S+|www\.\S+', '', text)
                    text = text.strip()
                    
                    if text:
                        # 添加广告
                        full_text = f"{text}\n\n{config['ad_text']}"
                        await client.send_message(config['target_channel'], full_text)
                        logger.info(f"📤 已转发消息到 {config['target_channel']}")
                
                elif msg.media:
                    await client.forward_messages(config['target_channel'], msg)
                    logger.info(f"📤 已转发媒体到 {config['target_channel']}")
                    
            except Exception as e:
                logger.error(f"❌ 转发失败: {e}")
        
        logger.info("=" * 50)
        logger.info("🤖 机器人配置完成")
        logger.info(f"👂 正在监听: {len(config['source_channels'])} 个源频道")
        logger.info(f"🎯 目标频道: {config['target_channel']}")
        logger.info("⏳ 等待新消息...")
        logger.info("=" * 50)
        
        await client.run_until_disconnected()
        
    except Exception as e:
        logger.error(f"❌ 启动失败: {e}")
        logger.error("💡 请检查:")
        logger.error("   1. API凭证是否正确")
        logger.error("   2. Bot Token是否正确")
        logger.error("   3. 网络连接是否正常")

if __name__ == "__main__":
    asyncio.run(main())
