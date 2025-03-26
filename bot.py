import os
import asyncio
import requests
from pyrogram import Client, filters
from pytgcalls import PyTgCalls
from pytgcalls.types import AudioPiped
import yt_dlp

from config import API_ID, API_HASH, BOT_TOKEN, OWNER_ID, YOUTUBE_API_KEY

# Initialize Pyrogram bot client
bot = Client("yt_player_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
pytgcalls = PyTgCalls(bot)

# Function to search YouTube using API Key
def search_youtube(query):
    if not YOUTUBE_API_KEY:
        return None, "❌ YouTube API Key is missing. Please set it in config.py."

    url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&q={query}&key={YOUTUBE_API_KEY}&maxResults=1&type=video"
    response = requests.get(url).json()
    
    if "items" in response and len(response["items"]) > 0:
        video_id = response["items"][0]["id"]["videoId"]
        video_title = response["items"][0]["snippet"]["title"]
        return f"https://www.youtube.com/watch?v={video_id}", video_title
    else:
        return None, "❌ No matching videos found on YouTube."

# Start command
@bot.on_message(filters.command(["start", "help"]))
async def start(_, message):
    await message.reply("🎵 I am a YouTube Music & Video Player Bot.\n\n"
                        "Commands:\n"
                        "/play song_name - Play a song\n"
                        "/stop - Stop the music")

# Play command
@bot.on_message(filters.command("play"))
async def play(_, message):
    if len(message.command) < 2:
        return await message.reply("❌ Provide a song name or YouTube link.")

    query = " ".join(message.command[1:])
    
    # Search YouTube for video link
    url, response_msg = search_youtube(query)
    if not url:
        return await message.reply(response_msg)
    
    # Download YouTube audio
    try:
        ydl_opts = {"format": "bestaudio", "noplaylist": True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            audio_url = info['url']
    except Exception as e:
        return await message.reply(f"❌ Error downloading audio: {str(e)}")

    # Play in voice chat
    chat_id = message.chat.id
    try:
        await pytgcalls.join_group_call(chat_id, AudioPiped(audio_url))
        await message.reply(f"🎶 Now playing: [{info['title']}]({url})", disable_web_page_preview=True)
    except Exception as e:
        return await message.reply(f"❌ Failed to join voice chat: {str(e)}")

# Stop command
@bot.on_message(filters.command("stop"))
async def stop(_, message):
    chat_id = message.chat.id
    try:
        await pytgcalls.leave_group_call(chat_id)
        await message.reply("⏹ Stopped playing.")
    except Exception as e:
        await message.reply(f"❌ Error stopping: {str(e)}")

# Start bot
bot.start()
pytgcalls.start()
print("Bot is running...")
asyncio.get_event_loop().run_forever()