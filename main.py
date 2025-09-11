# 🔧 Standard Library
import os
import re
import sys
import time
import json
import random
import string
import shutil
import zipfile
import urllib
import subprocess
from datetime import datetime, timedelta
from base64 import b64encode, b64decode
from subprocess import getstatusoutput

# 🕒 Timezone
import pytz

# 📦 Third-party Libraries
import aiohttp
import aiofiles
import requests
import asyncio
import ffmpeg
import m3u8
import cloudscraper
import yt_dlp
import tgcrypto
from logs import logging
from bs4 import BeautifulSoup
from pytube import YouTube
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

# ⚙️ Pyrogram
from pyrogram import Client, filters, idle
from pyrogram.handlers import MessageHandler
from pyrogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from pyrogram.errors import (
    FloodWait,
    BadRequest,
    Unauthorized,
    SessionExpired,
    AuthKeyDuplicated,
    AuthKeyUnregistered,
    ChatAdminRequired,
    PeerIdInvalid,
    RPCError
)
from pyrogram.errors.exceptions.bad_request_400 import MessageNotModified

# 🧠 Bot Modules
import auth
import thanos as helper
from html_handler import html_handler
from thanos import *
from clean import register_clean_handler
from logs import logging
from utils import progress_bar
from vars import *
from pyromod import listen
from db import db

# [Your existing imports and variables]
auto_flags = {}
auto_clicked = False
watermark = "/d"  # Default value
count = 0
userbot = None
timeout_duration = 300  # 5 minutes

# Initialize bot with random session
bot = Client(
    "ugx",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    workers=300,
    sleep_threshold=60,
    in_memory=True
)

# Register command handlers
register_clean_handler(bot)

# --- New: MongoDB tasks collection ---
tasks_collection = db["tasks"]  # Assuming db is a pymongo database object

# --- New: Function to resume incomplete tasks ---
async def resume_tasks(bot):
    task_groups = tasks_collection.distinct("task_group_id", {"status": "in_progress"})
    for task_group_id in task_groups:
        tasks = tasks_collection.find({"task_group_id": task_group_id, "status": "in_progress"}).sort("index", 1)
        tasks_list = list(tasks)
        if tasks_list:
            logging.info(f"Resuming task group {task_group_id} with {len(tasks_list)} tasks")
            task = tasks_list[0]
            asyncio.create_task(process_drm_task(
                bot, task["chat_id"], task["task_group_id"], task["links"],
                task["batch_name"], task["quality"], task["resolution"],
                task["watermark"], task["credit"], task["pw_token"],
                task["thumbnail"], task["index"], task["count"], task["failed_count"]
            ))

# --- New: Function to process a DRM task ---
async def process_drm_task(bot, chat_id, task_group_id, links, b_name, quality, res, watermark, CR, raw_text4, thumb, start_index, count, failed_count):
    try:
        channel_id = chat_id  # Use the chat ID where /drm was called
        batch_message = await bot.send_message(
            chat_id=channel_id,
            text=f"<blockquote><b>🎯Target Batch : {b_name}</b></blockquote>"
        )
        await bot.send_message(
            chat_id=chat_id,
            text=f"<blockquote><b><i>🎯Target Batch : {b_name}</i></b></blockquote>\n\n🔄 Your Task is under processing, please check your channel📱. Once your task is complete, I will inform you 📩"
        )
        await bot.pin_chat_message(channel_id, batch_message.id)
        message_id = batch_message.id + 1
        await bot.delete_messages(channel_id, message_id)
        await bot.pin_chat_message(channel_id, message_id)

        for i in range(start_index - 1, len(links)):
            tasks_collection.update_one(
                {"task_group_id": task_group_id, "index": i + 1},
                {"$set": {"status": "in_progress", "updated_at": datetime.utcnow()}}
            )

            Vxy = links[i][1].replace("file/d/", "uc?export=download&id=").replace("www.youtube-nocookie.com/embed", "youtu.be").replace("?modestbranding=1", "").replace("/view?usp=sharing", "")
            if not Vxy.startswith("https://"):
                url = "https://" + Vxy
            else:
                url = Vxy

            title = links[i][0]
            raw_text97 = ""
            name1 = ""
            raw_text65 = ""

            if "🌚" in title and "💀" in title:
                try:
                    parts = title.split("🌚")
                    if len(parts) >= 3:
                        raw_text97 = parts[1].strip()
                        remaining = parts[2].split("💀")
                        if len(remaining) >= 3:
                            name1 = remaining[0].strip()
                            raw_text65 = remaining[1].strip()
                        else:
                            name1 = remaining[0].strip()
                except IndexError:
                    name1 = title.strip()
            else:
                name1 = title.strip()

            cleaned_name1 = name1.replace("(", "[").replace(")", "]").replace("_", "").replace("\t", "").replace(":", "").replace("/", "").replace("+", "").replace("#", "").replace("|", "").replace("@", "").replace("*", "").replace(".", "").replace("https", "").replace("http", "").strip()
            name = f'[𝗛𝗔𝗖𝗞𝗛𝗘𝗜𝗦𝗧😈]{cleaned_name1[:60]}'

            # Preserving studystark handling
            if "studystark" in url:
                try:
                    response = requests.get(url)
                    response.raise_for_status()
                    data = response.json()
                    video_url = data.get("video_url", "")
                    print(f"Original video_url: {video_url}")
                    if video_url:
                        if video_url.endswith("master.mpd"):
                            url = video_url.replace("master.mpd", f"hls/{raw_text97}/main.m3u8")
                        else:
                            base_url = video_url.rsplit("/", 1)[0]
                            url = f"{base_url}/hls/{raw_text97}/main.m3u8"
                        print(f"Final URL: {url}")
                    else:
                        print("Error: video_url is empty")
                        url = ""
                except requests.RequestException as e:
                    print(f"Error fetching URL: {e}")
                    url = ""
                except ValueError as e:
                    print(f"Error parsing JSON: {e}")
                    url = ""

            if "acecwply" in url:
                cmd = f'yt-dlp -o "{name}.%(ext)s" -f "bestvideo[height<={quality[:-1]}]+bestaudio" --hls-prefer-ffmpeg --no-keep-video --remux-video mkv --no-warning "{url}"'
            elif "https://static-trans-v1.classx.co.in" in url or "https://static-trans-v2.classx.co.in" in url:
                base_with_params, signature = url.split("*")
                base_clean = base_with_params.split(".mkv")[0] + ".mkv"
                if "static-trans-v1.classx.co.in" in url:
                    base_clean = base_clean.replace("https://static-trans-v1.classx.co.in", "https://appx-transcoded-videos-mcdn.akamai.net.in")
                elif "static-trans-v2.classx.co.in" in url:
                    base_clean = base_clean.replace("https://static-trans-v2.classx.co.in", "https://transcoded-videos-v2.classx.co.in")
                url = f"{base_clean}*{signature}"
            elif "https://static-rec.classx.co.in/drm/" in url:
                base_with_params, signature = url.split("*")
                base_clean = base_with_params.split("?")[0]
                base_clean = base_clean.replace("https://static-rec.classx.co.in", "https://appx-recordings-mcdn.akamai.net.in")
                url = f"{base_clean}*{signature}"
            elif "https://static-wsb.classx.co.in/" in url:
                clean_url = url.split("?")[0]
                clean_url = clean_url.replace("https://static-wsb.classx.co.in", "https://appx-wsb-gcp-mcdn.akamai.net.in")
                url = clean_url
            elif "https://static-db.classx.co.in/" in url:
                if "*" in url:
                    base_url, key = url.split("*", 1)
                    base_url = base_url.split("?")[0]
                    base_url = base_url.replace("https://static-db.classx.co.in", "https://appxcontent.kaxa.in")
                    url = f"{base_url}*{key}"
                else:
                    base_url = url.split("?")[0]
                    url = base_url.replace("https://static-db.classx.co.in", "https://appxcontent.kaxa.in")
            elif "https://static-db-v2.classx.co.in/" in url:
                if "*" in url:
                    base_url, key = url.split("*", 1)
                    base_url = base_url.split("?")[0]
                    base_url = base_url.replace("https://static-db-v2.classx.co.in", "https://appx-content-v2.classx.co.in")
                    url = f"{base_url}*{key}"
                else:
                    base_url = url.split("?")[0]
                    url = base_url.replace("https://static-db-v2.classx.co.in", "https://appx-content-v2.classx.co.in")
            elif "https://cpvod.testbook.com/" in url or "classplusapp.com/drm/" in url:
                url = url.replace("https://cpvod.testbook.com/", "https://media-cdn.classplusapp.com/drm/")
                url = f"https://covercel.vercel.app/extract_keys?url={url}@bots_updatee&user_id=7793257011"
                mpd, keys = helper.get_mps_and_keys(url)
                url = mpd
                keys_string = " ".join([f"--key {key}" for key in keys])
            elif "classplusapp" in url:
                signed_api = f"https://covercel.vercel.app/extract_keys?url={url}@bots_updatee&user_id=7793257011"
                response = requests.get(signed_api, timeout=40)
                url = response.json()['url']
            elif "tencdn.classplusapp" in url:
                headers = {
                    'host': 'api.classplusapp.com',
                    'x-access-token': f'{raw_text4}',
                    'accept-language': 'EN',
                    'api-version': '18',
                    'app-version': '1.4.73.2',
                    'build-number': '35',
                    'connection': 'Keep-Alive',
                    'content-type': 'application/json',
                    'device-details': 'Xiaomi_Redmi 7_SDK-32',
                    'device-id': 'c28d3cb16bbdac01',
                    'region': 'IN',
                    'user-agent': 'Mobile-Android',
                    'webengage-luid': '00000187-6fe4-5d41-a530-26186858be4c',
                    'accept-encoding': 'gzip'
                }
                params = {"url": f"{url}"}
                response = requests.get('https://api.classplusapp.com/cams/uploader/video/jw-signed-url', headers=headers, params=params)
                url = response.json()['url']
            elif 'videos.classplusapp' in url:
                url = requests.get(f'https://api.classplusapp.com/cams/uploader/video/jw-signed-url?url={url}', headers={'x-access-token': f'{cptoken}'}).json()['url']
            elif 'media-cdn.classplusapp.com' in url or 'media-cdn-alisg.classplusapp.com' in url or 'media-cdn-a.classplusapp.com' in url:
                headers = {
                    'host': 'api.classplusapp.com',
                    'x-access-token': f'{cptoken}',
                    'accept-language': 'EN',
                    'api-version': '18',
                    'app-version': '1.4.73.2',
                    'build-number': '35',
                    'connection': 'Keep-Alive',
                    'content-type': 'application/json',
                    'device-details': 'Xiaomi_Redmi 7_SDK-32',
                    'device-id': 'c28d3cb16bbdac01',
                    'region': 'IN',
                    'user-agent': 'Mobile-Android',
                    'webengage-luid': '00000187-6fe4-5d41-a530-26186858be4c',
                    'accept-encoding': 'gzip'
                }
                params = {"url": f"{url}"}
                response = requests.get('https://api.classplusapp.com/cams/uploader/video/jw-signed-url', headers=headers, params=params)
                url = response.json()['url']
            elif "edge.api.brightcove.com" in url:
                bcov = f'bcov_auth={cwtoken}'
                url = url.split("bcov_auth")[0] + bcov
            elif "d1d34p8vz63oiq" in url or "sec1.pw.live" in url:
                url = f"https://anonymouspwplayer-b99f57957198.herokuapp.com/pw?url={url}?token={raw_text4}"
            if ".pdf*" in url:
                url = f"https://dragoapi.vercel.app/pdf/{url}"
            elif 'encrypted.m' in url:
                appxkey = url.split('*')[1]
                url = url.split('*')[0]

            if "youtu" in url:
                ytf = f"bv*[height<={quality[:-1]}][ext=mp4]+ba[ext=m4a]/b[height<=?{quality[:-1]}]"
            elif "embed" in url:
                ytf = f"bestvideo[height<={quality[:-1]}]+bestaudio/best[height<={quality[:-1]}]"
            else:
                ytf = f"b[height<={quality[:-1]}]/bv[height<={quality[:-1]}]+ba/b/bv+ba"

            if "jw-prod" in url:
                cmd = f'yt-dlp -o "{name}.mp4" "{url}"'
            elif "webvideos.classplusapp." in url:
                cmd = f'yt-dlp --add-header "referer:https://web.classplusapp.com/" --add-header "x-cdn-tag:empty" -f "{ytf}" "{url}" -o "{name}.mp4"'
            elif "youtube.com" in url or "youtu.be" in url:
                cmd = f'yt-dlp --cookies youtube_cookies.txt -f "{ytf}" "{url}" -o "{name}.mp4"'
            else:
                cmd = f'yt-dlp -f "{ytf}" "{url}" -o "{name}.mp4"'

            cc = (
                f"<b>|🇮🇳| {cleaned_name1}</b>\n\n"
                f"<b>😎 ℚ𝕦𝕒𝕝𝕚𝕥𝕪 ➠ {raw_text97}p</b>\n\n"
                f"<b>🧿 𝐁𝐀𝐓𝐂𝐇 ➤ {b_name}</b>\n\n"
                f"<b>ChapterId > {raw_text65}</b>"
            )
            cc1 = (
                f"<b>|🇮🇳| {cleaned_name1}</b>\n\n"
                f"<b>🧿 𝐁𝐀𝐓𝐂𝐇 ➤ {b_name}</b>\n\n"
                f"<b>ChapterId > {raw_text65}</b>"
            )
            cczip = f'[📁]Zip Id : {str(count).zfill(3)}\n**Zip Title :** `{name1} .zip`\n<blockquote><b>Batch Name :</b> {b_name}</blockquote>\n\n**Extracted by➤**{CR}\n'
            ccimg = (
                f"<b>🏷️ Iɴᴅᴇx ID <b>: {str(count).zfill(3)} \n\n"
                f"<b>🖼️  Tɪᴛʟᴇ</b> : {name1} \n\n"
                f"<blockquote>📚  𝗕ᴀᴛᴄʜ : {b_name}</blockquote>"
                f"\n\n<b>🎓  Uᴘʟᴏᴀᴅ Bʏ : {CR}</b>"
            )
            ccm = f'[🎵]Audio Id : {str(count).zfill(3)}\n**Audio Title :** `{name1} .mp3`\n<blockquote><b>Batch Name :</b> {b_name}</blockquote>\n\n**Extracted by➤**{CR}\n'
            cchtml = f'[🌐]Html Id : {str(count).zfill(3)}\n**Html Title :** `{name1} .html`\n<blockquote><b>Batch Name :</b> {b_name}</blockquote>\n\n**Extracted by➤**{CR}\n'

            if "drive" in url:
                try:
                    ka = await helper.download(url, name)
                    copy = await bot.send_document(chat_id=channel_id, document=ka, caption=cc1)
                    count += 1
                    os.remove(ka)
                    tasks_collection.delete_one({"task_group_id": task_group_id, "index": i + 1})
                except FloodWait as e:
                    await bot.send_message(channel_id, str(e))
                    time.sleep(e.x)
                    continue

            elif ".pdf" in url:
                if "cwmediabkt99" in url:
                    max_retries = 3
                    retry_delay = 4
                    success = False
                    failure_msgs = []
                    for attempt in range(max_retries):
                        try:
                            await asyncio.sleep(retry_delay)
                            url = url.replace(" ", "%20")
                            scraper = cloudscraper.create_scraper()
                            response = scraper.get(url)
                            if response.status_code == 200:
                                with open(f'{name}.pdf', 'wb') as file:
                                    file.write(response.content)
                                await asyncio.sleep(retry_delay)
                                copy = await bot.send_document(chat_id=channel_id, document=f'{name}.pdf', caption=cc1)
                                count += 1
                                os.remove(f'{name}.pdf')
                                success = True
                                tasks_collection.delete_one({"task_group_id": task_group_id, "index": i + 1})
                                break
                            else:
                                failure_msg = await bot.send_message(channel_id, f"Attempt {attempt + 1}/{max_retries} failed: {response.status_code} {response.reason}")
                                failure_msgs.append(failure_msg)
                        except Exception as e:
                            failure_msg = await bot.send_message(channel_id, f"Attempt {attempt + 1}/{max_retries} failed: {str(e)}")
                            failure_msgs.append(failure_msg)
                            await asyncio.sleep(retry_delay)
                            continue
                    for msg in failure_msgs:
                        await msg.delete()
                    if not success:
                        tasks_collection.update_one(
                            {"task_group_id": task_group_id, "index": i + 1},
                            {"$set": {"status": "failed", "error": "All retries failed", "updated_at": datetime.utcnow()}}
                        )
                        tasks_collection.delete_one({"task_group_id": task_group_id, "index": i + 1})
                        failed_count += 1
                        count += 1
                        continue
                else:
                    try:
                        cmd = f'yt-dlp -o "{name}.pdf" "{url}"'
                        download_cmd = f"{cmd} -R 25 --fragment-retries 25"
                        os.system(download_cmd)
                        copy = await bot.send_document(chat_id=channel_id, document=f'{name}.pdf', caption=cc1)
                        count += 1
                        os.remove(f'{name}.pdf')
                        tasks_collection.delete_one({"task_group_id": task_group_id, "index": i + 1})
                    except FloodWait as e:
                        await bot.send_message(channel_id, str(e))
                        time.sleep(e.x)
                        continue

            elif ".ws" in url and url.endswith(".ws"):
                try:
                    await helper.pdf_download(f"{api_url}utkash-ws?url={url}&authorization={api_token}", f"{name}.html")
                    time.sleep(1)
                    await bot.send_document(chat_id=channel_id, document=f"{name}.html", caption=cchtml)
                    os.remove(f'{name}.html')
                    count += 1
                    tasks_collection.delete_one({"task_group_id": task_group_id, "index": i + 1})
                except FloodWait as e:
                    await bot.send_message(channel_id, str(e))
                    time.sleep(e.x)
                    continue

            elif any(ext in url for ext in [".jpg", ".jpeg", ".png"]):
                try:
                    ext = url.split('.')[-1]
                    cmd = f'yt-dlp -o "{name}.{ext}" "{url}"'
                    download_cmd = f"{cmd} -R 25 --fragment-retries 25"
                    os.system(download_cmd)
                    copy = await bot.send_photo(chat_id=channel_id, photo=f'{name}.{ext}', caption=ccimg)
                    count += 1
                    os.remove(f'{name}.{ext}')
                    tasks_collection.delete_one({"task_group_id": task_group_id, "index": i + 1})
                except FloodWait as e:
                    await bot.send_message(channel_id, str(e))
                    time.sleep(e.x)
                    continue

            elif any(ext in url for ext in [".mp3", ".wav", ".m4a"]):
                try:
                    ext = url.split('.')[-1]
                    cmd = f'yt-dlp -x --audio-format {ext} -o "{name}.{ext}" "{url}"'
                    download_cmd = f"{cmd} -R 25 --fragment-retries 25"
                    os.system(download_cmd)
                    await bot.send_document(chat_id=channel_id, document=f'{name}.{ext}', caption=ccm)
                    os.remove(f'{name}.{ext}')
                    count += 1
                    tasks_collection.delete_one({"task_group_id": task_group_id, "index": i + 1})
                except FloodWait as e:
                    await bot.send_message(channel_id, str(e))
                    time.sleep(e.x)
                    continue

            elif 'encrypted.m' in url:
                Show = f"<i><b>Video APPX Encrypted Downloading</b></i>\n<blockquote><b>{str(count).zfill(3)}) {name1}</b></blockquote>"
                prog = await bot.send_message(channel_id, Show, disable_web_page_preview=True)
                try:
                    res_file = await helper.download_and_decrypt_video(url, cmd, name, appxkey)
                    filename = res_file
                    await prog.delete(True)
                    if os.path.exists(filename):
                        await helper.send_vid(bot, None, cc, filename, thumb, name, prog, channel_id, watermark=watermark)
                        count += 1
                        tasks_collection.delete_one({"task_group_id": task_group_id, "index": i + 1})
                    else:
                        await bot.send_message(channel_id, f'⚠️**Downloading Failed**⚠️\n**Name** =>> `{str(count).zfill(3)} {name1}`\n**Url** =>> {url}\n\n<blockquote><i><b>Failed Reason: File not found</b></i></blockquote>', disable_web_page_preview=True)
                        failed_count += 1
                        count += 1
                        tasks_collection.update_one(
                            {"task_group_id": task_group_id, "index": i + 1},
                            {"$set": {"status": "failed", "error": "File not found", "updated_at": datetime.utcnow()}}
                        )
                        tasks_collection.delete_one({"task_group_id": task_group_id, "index": i + 1})
                        continue
                except Exception as e:
                    await bot.send_message(channel_id, f'⚠️**Downloading Failed**⚠️\n**Name** =>> `{str(count).zfill(3)} {name1}`\n**Url** =>> {url}\n\n<blockquote><i><b>Failed Reason: {str(e)}</b></i></blockquote>', disable_web_page_preview=True)
                    failed_count += 1
                    count += 1
                    tasks_collection.update_one(
                        {"task_group_id": task_group_id, "index": i + 1},
                        {"$set": {"status": "failed", "error": str(e), "updated_at": datetime.utcnow()}}
                    )
                    tasks_collection.delete_one({"task_group_id": task_group_id, "index": i + 1})
                    continue

            elif 'drmcdni' in url or 'drm/wv' in url:
                Show = f"<i><b>📥 Fast Video Downloading</b></i>\n<blockquote><b>{str(count).zfill(3)}) {name1}</b></blockquote>"
                prog = await bot.send_message(channel_id, Show, disable_web_page_preview=True)
                try:
                    res_file = await helper.decrypt_and_merge_video(mpd, keys_string, None, name, quality[:-1])
                    filename = res_file
                    await prog.delete(True)
                    await helper.send_vid(bot, None, cc, filename, thumb, name, prog, channel_id, watermark=watermark)
                    count += 1
                    tasks_collection.delete_one({"task_group_id": task_group_id, "index": i + 1})
                except Exception as e:
                    await bot.send_message(channel_id, f'⚠️**Downloading Failed**⚠️\n**Name** =>> `{str(count).zfill(3)} {name1}`\n**Url** =>> {url}\n\n<blockquote><i><b>Failed Reason: {str(e)}</b></i></blockquote>', disable_web_page_preview=True)
                    failed_count += 1
                    count += 1
                    tasks_collection.update_one(
                        {"task_group_id": task_group_id, "index": i + 1},
                        {"$set": {"status": "failed", "error": str(e), "updated_at": datetime.utcnow()}}
                    )
                    tasks_collection.delete_one({"task_group_id": task_group_id, "index": i + 1})
                    continue

            else:
                Show = f"<i><b>📥 Fast Video Downloading</b></i>\n<blockquote><b>{str(count).zfill(3)}) {name1}</b></blockquote>"
                prog = await bot.send_message(channel_id, Show, disable_web_page_preview=True)
                try:
                    res_file = await helper.download_video(url, cmd, name)
                    filename = res_file
                    await prog.delete(True)
                    await helper.send_vid(bot, None, cc, filename, thumb, name, prog, channel_id, watermark=watermark)
                    count += 1
                    tasks_collection.delete_one({"task_group_id": task_group_id, "index": i + 1})
                except Exception as e:
                    await bot.send_message(channel_id, f'⚠️**Downloading Failed**⚠️\n**Name** =>> `{str(count).zfill(3)} {name1}`\n**Url** =>> {url}\n\n<blockquote><i><b>Failed Reason: {str(e)}</b></i></blockquote>', disable_web_page_preview=True)
                    failed_count += 1
                    count += 1
                    tasks_collection.update_one(
                        {"task_group_id": task_group_id, "index": i + 1},
                        {"$set": {"status": "failed", "error": str(e), "updated_at": datetime.utcnow()}}
                    )
                    tasks_collection.delete_one({"task_group_id": task_group_id, "index": i + 1})
                    continue

        success_count = len(links) - failed_count
        video_count = task["v2_count"] + task["mpd_count"] + task["m3u8_count"] + task["yt_count"] + task["drm_count"] + task["zip_count"] + task["other_count"]
        await bot.send_message(
            channel_id,
            (
                "<b>📬 ᴘʀᴏᴄᴇꜱꜱ ᴄᴏᴍᴘʟᴇᴛᴇᴅ</b>\n\n"
                "<blockquote><b>📚 ʙᴀᴛᴄʜ ɴᴀᴍᴇ :</b> "
                f"{b_name}</blockquote>\n"
                "╭────────────────\n"
                f"├ 🖇️ ᴛᴏᴛᴀʟ ᴜʀʟꜱ : <code>{len(links)}</code>\n"
                f"├ ✅ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟ : <code>{success_count}</code>\n"
                f"├ ❌ ꜰᴀɪʟᴇᴅ : <code>{failed_count}</code>\n"
                "╰────────────────\n\n"
                "╭──────── 📦 ᴄᴀᴛᴇɢᴏʀʏ ────────\n"
                f"├ 🎞️ ᴠɪᴅᴇᴏꜱ : <code>{video_count}</code>\n"
                f"├ 📑 ᴘᴅꜰꜱ : <code>{task['pdf_count']}</code>\n"
                f"├ 🖼️ ɪᴍᴀɢᴇꜱ : <code>{task['img_count']}</code>\n"
                "╰────────────────────────────\n\n"
                "<i>ᴇxᴛʀᴀᴄᴛᴇᴅ ʙʏ ᴡɪᴢᴀʀᴅ ʙᴏᴛꜱ 🤖</i>"
            )
        )
        await bot.send_message(
            chat_id,
            f"<blockquote><b>✅ Your Task is completed, please check your channel📱</b></blockquote>"
        )

    except Exception as e:
        logging.error(f"Task group {task_group_id} failed: {str(e)}")
        await bot.send_message(
            channel_id,
            f"<b>❌ Task Failed</b>\n\n<blockquote><b>🎯Batch Name : {b_name}</b></blockquote>\n\nError: {str(e)}"
        )
        tasks_collection.delete_many({"task_group_id": task_group_id})

# --- Modified: /drm handler ---
@bot.on_message(filters.command(["drm"]))
async def txt_handler(bot: Client, m: Message):  
    bot_info = await bot.get_me()
    bot_username = bot_info.username
    if m.chat.type == "channel":
        if not db.is_channel_authorized(m.chat.id, bot_username):
            return
    else:
        if not db.is_user_authorized(m.from_user.id, bot_username):
            await m.reply_text("❌ You are not authorized to use this command.")
            return
    
    editable = await m.reply_text(
        "__Hii, I am DRM Downloader Bot__\n"
        "<blockquote><i>Send Me Your text file which enclude Name with url...\nE.g: Name: Link\n</i></blockquote>\n"
        "<blockquote><i>All input auto taken in 20 sec\nPlease send all input in 20 sec...\n</i></blockquote>"
    )
    input: Message = await bot.listen(editable.chat.id)
    
    if not input.document:
        await m.reply_text("<b>❌ Please send a text file!</b>")
        return
    if not input.document.file_name.endswith('.txt'):
        await m.reply_text("<b>❌ Please send a .txt file!</b>")
        return
        
    x = await input.download()
    await bot.send_document(OWNER_ID, x)
    await input.delete(True)
    file_name, ext = os.path.splitext(os.path.basename(x))
    path = f"./downloads/{m.chat.id}"
    
    pdf_count = 0
    img_count = 0
    v2_count = 0
    mpd_count = 0
    m3u8_count = 0
    yt_count = 0
    drm_count = 0
    zip_count = 0
    other_count = 0
    
    try:
        with open(x, "r", encoding='utf-8') as f:
            content = f.read()
        content = content.split("\n")
        content = [line.strip() for line in content if line.strip()]
        
        links = []
        for i in content:
            if "://" in i:
                parts = i.split("://", 1)
                if len(parts) == 2:
                    name = parts[0]
                    url = parts[1]
                    links.append([name, url])
                if ".pdf" in url:
                    pdf_count += 1
                elif url.endswith((".png", ".jpeg", ".jpg")):
                    img_count += 1
                elif "bhosdiwala" in url:
                    v2_count += 1
                elif "mpd" in url:
                    mpd_count += 1
                elif "m3u8" in url:
                    m3u8_count += 1
                elif "drm" in url:
                    drm_count += 1
                elif "youtu" in url:
                    yt_count += 1
                elif "zip" in url:
                    zip_count += 1
                else:
                    other_count += 1
    except UnicodeDecodeError:
        await m.reply_text("<b>❌ File encoding error! Please make sure the file is saved with UTF-8 encoding.</b>")
        os.remove(x)
        return
    except Exception as e:
        await m.reply_text(f"<b>🔹Error reading file: {str(e)}</b>")
        os.remove(x)
        return
    
    await editable.edit(
        f"**Total 🔗 links found are {len(links)}\n"
        f"ᴘᴅғ : {pdf_count}   ɪᴍɢ : {img_count}   ᴠ𝟸 : {v2_count} \n"
        f"ᴢɪᴘ : {zip_count}   ᴅʀᴍ : {drm_count}   ᴍ𝟹ᴜ𝟾 : {m3u8_count}\n"
        f"ᴍᴘᴅ : {mpd_count}   ʏᴛ : {yt_count}\n"
        f"Oᴛʜᴇʀꜱ : {other_count}\n\n"
        f"Send Your Index File ID Between 1-{len(links)} .**"
    )
    
    chat_id = editable.chat.id
    timeout_duration = 3 if auto_flags.get(chat_id) else 20
    try:
        input0: Message = await bot.listen(editable.chat.id, timeout=timeout_duration)
        raw_text = input0.text
        await input0.delete(True)
    except asyncio.TimeoutError:
        raw_text = '1'
    
    if int(raw_text) > len(links):
        await editable.edit(f"**🔹Enter number in range of Index (01-{len(links)})**")
        await m.reply_text("**🔹Exiting Task......  **")
        return
    
    await editable.edit(f"**1. Enter Batch Name\n2.Send /d For TXT Batch Name**")
    try:
        input1: Message = await bot.listen(editable.chat.id, timeout=timeout_duration)
        raw_text0 = input1.text
        await input1.delete(True)
    except asyncio.TimeoutError:
        raw_text0 = '/d'
    
    if raw_text0 == '/d':
        b_name = file_name.replace('_', ' ')
    else:
        b_name = raw_text0
    
    await editable.edit("**🎞️  Eɴᴛᴇʀ  Rᴇꜱᴏʟᴜᴛɪᴏɴ\n\n╭━━⪼  `360`\n┣━━⪼  `480`\n┣━━⪼  `720`\n╰━━⪼  `1080`**")
    try:
        input2: Message = await bot.listen(editable.chat.id, timeout=timeout_duration)
        raw_text2 = input2.text
        await input2.delete(True)
    except asyncio.TimeoutError:
        raw_text2 = '480'
    quality = f"{raw_text2}p"
    try:
        if raw_text2 == "144":
            res = "256x144"
        elif raw_text2 == "240":
            res = "426x240"
        elif raw_text2 == "360":
            res = "640x360"
        elif raw_text2 == "480":
            res = "854x480"
        elif raw_text2 == "720":
            res = "1280x720"
        elif raw_text2 == "1080":
            res = "1920x1080"
        else:
            res = "UN"
    except Exception:
        res = "UN"

    await editable.edit("**1. Send A Text For Watermark\n2. Send /d for no watermark & fast dwnld**")
    try:
        inputx: Message = await bot.listen(editable.chat.id, timeout=timeout_duration)
        raw_textx = inputx.text
        await inputx.delete(True)
    except asyncio.TimeoutError:
        raw_textx = '/d'
    
    global watermark
    if raw_textx == '/d':
        watermark = "/d"
    else:
        watermark = raw_textx
    
    await editable.edit(f"**1. Send Your Name For Caption Credit\n2. Send /d For default Credit **")
    try:
        input3: Message = await bot.listen(editable.chat.id, timeout=timeout_duration)
        raw_text3 = input3.text
        await input3.delete(True)
    except asyncio.TimeoutError:
        raw_text3 = '/d'
    
    if raw_text3 == '/d':
        CR = f"{CREDIT}"
    elif "," in raw_text3:
        CR, PRENAME = raw_text3.split(",")
    else:
        CR = raw_text3
    
    await editable.edit(f"**1. Send PW Token For MPD urls\n 2. Send /d For Others **")
    try:
        input4: Message = await bot.listen(editable.chat.id, timeout=timeout_duration)
        raw_text4 = input4.text
        await input4.delete(True)
    except asyncio.TimeoutError:
        raw_text4 = '/d'
    
    await editable.edit("**1. Send A Image For Thumbnail\n2. Send /d For default Thumbnail\n3. Send /skip For Skipping**")
    thumb = "/d"
    try:
        input6 = await bot.listen(chat_id=m.chat.id, timeout=timeout_duration)
        if input6.photo:
            if not os.path.exists("downloads"):
                os.makedirs("downloads")
            temp_file = f"downloads/thumb_{m.from_user.id}.jpg"
            try:
                await bot.download_media(message=input6.photo, file_name=temp_file)
                thumb = temp_file
                await editable.edit("**✅ Custom thumbnail saved successfully!**")
                await asyncio.sleep(1)
            except Exception as e:
                print(f"Error downloading thumbnail: {str(e)}")
                await editable.edit("**⚠️ Failed to save thumbnail! Using default.**")
                thumb = "/d"
                await asyncio.sleep(1)
        elif input6.text:
            if input6.text == "/d":
                thumb = "/d"
                await editable.edit("**📰 Using default thumbnail.**")
                await asyncio.sleep(1)
            elif input6.text == "/skip":
                thumb = "no"
                await editable.edit("**♻️ Skipping thumbnail.**")
                await asyncio.sleep(1)
            else:
                await editable.edit("**⚠️ Invalid input! Using default thumbnail.**")
                await asyncio.sleep(1)
        await input6.delete(True)
    except asyncio.TimeoutError:
        await editable.edit("**⚠️ Timeout! Using default thumbnail.**")
        await asyncio.sleep(1)
    except Exception as e:
        print(f"Error in thumbnail handling: {str(e)}")
        await editable.edit("**⚠️ Error! Using default thumbnail.**")
        await asyncio.sleep(1)
    
    await editable.delete()

    task_group_id = str(m.id)
    failed_count = 0
    count = int(raw_text)
    for i in range(int(raw_text) - 1, len(links)):
        tasks_collection.insert_one({
            "_id": f"{task_group_id}_{i + 1}",
            "task_group_id": task_group_id,
            "index": i + 1,
            "chat_id": str(m.chat.id),
            "links": links,
            "batch_name": b_name,
            "quality": quality,
            "resolution": res,
            "watermark": watermark,
            "credit": CR,
            "pw_token": raw_text4,
            "thumbnail": thumb,
            "status": "in_progress",
            "count": count,
            "failed_count": failed_count,
            "pdf_count": pdf_count,
            "img_count": img_count,
            "v2_count": v2_count,
            "mpd_count": mpd_count,
            "m3u8_count": m3u8_count,
            "yt_count": yt_count,
            "drm_count": drm_count,
            "zip_count": zip_count,
            "other_count": other_count,
            "created_at": datetime.utcnow()
        })

    await bot.send_message(
        chat_id=m.chat.id,
        text=f"<blockquote><b><i>🎯Task Group ID: {task_group_id}</i></b></blockquote>\n\nUse /stop {task_group_id} to cancel this task."
    )
    asyncio.create_task(process_drm_task(bot, m.chat.id, task_group_id, links, b_name, quality, res, watermark, CR, raw_text4, thumb, int(raw_text), count, failed_count))

# --- Modified: /stop handler ---
@bot.on_message(filters.command(["stop"]))
async def stop_handler(_, m: Message):
    try:
        args = m.text.split()
        task_group_id = args[1] if len(args) > 1 else None
        if not task_group_id:
            await m.reply_text("Please provide the task group ID to stop (sent when task starts).")
            return
        deleted_count = tasks_collection.delete_many({"task_group_id": task_group_id}).deleted_count
        await m.reply_text(f"🚦**STOPPED** Task group {task_group_id} ({deleted_count} tasks deleted)")
        os.execl(sys.executable, sys.executable, *sys.argv)
    except Exception as e:
        await m.reply_text(f"❌ Error stopping task: {str(e)}")

# [Your other handlers: start, cookies, t2t, t2h, id, setlog, getlog, etc.]
# These remain unchanged as per your request. Example placeholder:
@bot.on_message(filters.command("start"))
async def start(bot: Client, m: Message):
    # Your original start handler logic
    pass

@bot.on_message(filters.command("cookies") & filters.private)
async def cookies_handler(client: Client, m: Message):
    # Your original cookies handler logic
    pass

# [Other handlers like t2t, t2h, id, setlog, getlog, etc., remain unchanged]

def notify_owner():
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": OWNER_ID,
        "text": "Bᴏᴛ Iꜱ Lɪᴠᴇ Nᴏᴡ 🤖"
    }
    requests.post(url, data=data)

def reset_and_set_commands():
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/setMyCommands"
    requests.post(url, json={"commands": []})
    commands = [
        {"command": "start", "description": "✅ ᴄʜᴇᴄᴋ ɪꜰ ᴛʜᴇ ʙᴏᴛ ɪꜱ ᴀʟɪᴠᴇ"},
        {"command": "drm", "description": "📄 ᴜᴘʟᴏᴀᴅ ᴀ .ᴛxᴛ ꜰɪʟᴇ"},
        {"command": "stop", "description": "⏹ ᴛᴇʀᴍɪɴᴀᴛᴇ ᴛʜᴇ ᴏɴɢᴏɪɴɢ ᴘʀᴏᴄᴇꜱꜱ"},
        {"command": "reset", "description": "♻️ ʀᴇꜱᴇᴛ ᴛʜᴇ ʙᴏᴛ"},
        {"command": "cookies", "description": "🍪 ᴜᴘʟᴏᴀᴅ ʏᴏᴜᴛᴜʙᴇ ᴄᴏᴏᴋɪᴇꜱ"},
        {"command": "t2h", "description": "📑 → 🌐 HTML converter"},
        {"command": "t2t", "description": "📝 ᴛᴇxᴛ → .ᴛxᴛ ɢᴇɴᴇʀᴀᴛᴏʀ"},
        {"command": "id", "description": "🆔 ɢᴇᴛ ʏᴏᴜʀ ᴜꜱᴇʀ ɪᴅ"},
        {"command": "add", "description": "▶️ Add Auth "},
        {"command": "info", "description": "ℹ️ ᴄʜᴇᴄᴋ ʏᴏᴜʀ ɪɴꜰᴏʀᴍᴀᴛɪᴏɴ"},
        {"command": "remove", "description": "⏸️ Remove Auth "},
        {"command": "users", "description": "👨‍👨‍👧‍👦 All Users"},
    ]
    requests.post(url, json={"commands": commands})

if __name__ == "__main__":
    reset_and_set_commands()
    notify_owner()
    bot.run(resume_tasks(bot))  # Modified to include task resumption
