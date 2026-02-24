import os
import json
import logging
import asyncio
from datetime import datetime
from threading import Thread
from flask import Flask
from telethon import TelegramClient, events
from telethon.tl.functions.channels import JoinChannelRequest # 核心：自动加入功能

# --- 基础配置 ---
API_ID = '你的API_ID'
API_HASH = '你的API_HASH'
BOT_TOKEN = '你的BOT_TOKEN'
ADMIN_ID = 你的ID
CONFIG_FILE = 'config.json'

# --- 自动加入逻辑补丁 ---
async def try_join_channel(channel_username):
    try:
        # 清除用户名中的 @ 符号
        clean_name = channel_username.replace('@', '').strip()
        await client(JoinChannelRequest(clean_name))
        return True, f"✅ 已成功自动加入并开始监听: @{clean_name}"
    except Exception as e:
        return False, f"⚠️ 无法自动加入 @{clean_name}: {str(e)}\n(请确保频道公开，或手动将机器人拉入该频道)"

# --- 这里的逻辑会在你点击“添加”按钮时触发 ---
@client.on(events.NewMessage(pattern='/add_source'))
async def handle_add_source(event):
    if event.sender_id != ADMIN_ID: return
    async with event.client.conversation(event.chat_id) as conv:
        await conv.send_message("请输入要监听的源频道用户名 (例如: @dashijian09)")
        response = await conv.get_response()
        new_channel = response.text.strip()
        
        # 核心：存入配置前先尝试自动潜伏
        success, msg = await try_join_channel(new_channel)
        await conv.send_message(msg)
        
        if success:
            config['source_channels'].append(new_channel)
            save_config()

# --- 启动函数 ---
async def main():
    Thread(target=lambda: app.run(host='0.0.0.0', port=10000)).start()
    await client.start(bot_token=BOT_TOKEN)
    
    # 启动时，对已有频道也尝试一次自动加入，确保万无一失
    for ch in config.get('source_channels', []):
        await try_join_channel(ch)
        
    print("✅ 机器人全功能上线")
    await client.run_until_disconnected()

# (其余合并搬运逻辑保持 v10 版本不变...)
