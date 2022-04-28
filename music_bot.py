import discord
import logging
import os
import time
import asyncio
import youtube_dl
from my_data import data
from googleapiclient.discovery import build

logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

TOKEN = data["BOT_TOKEN"]
developer_key = data['developer']
client = discord.Client()

youtube = build('youtube', 'v3', developerKey=developer_key)  # pomenyat apikey
search = youtube.search()

prefix = 'https://youtube.com/watch?v='

voice_clients = {}

song_queue = []

_loop = False

yt_dl_options = {'format': 'bestaudio/best'}
ytdl = youtube_dl.YoutubeDL(yt_dl_options)

ffmpeg_options = {'options': '-vn'}


@client.event
async def on_ready():
    print(f'Bot logged in as {client.user}')


async def playQueue(voice):
    if song_queue and not voice.is_playing():
        await play(song_queue.pop(0)[1], voice)
        print('queue: ' + str(song_queue))


# async def after(voice, loop):
#     cor = await playQueue(voice)
#     asyncio.run_coroutine_threadsafe(cor, loop).result()


async def play(song, voice):  # функция по проигрыванию музыки
    loop = asyncio.get_event_loop()
    _data = await loop.run_in_executor(None, lambda: ytdl.extract_info(song, download=False))
    song = _data['url']
    x = await playQueue(voice)
    voice.play(discord.FFmpegPCMAudio(song, **ffmpeg_options, executable='ffmpeg\\ffmpeg.exe'),
               after=lambda e: x)


@client.event
async def on_message(message):
    if message.content.startswith(";;play"):  # Запрос и поиск музыки, запуск функции по проигрыванию музыки
        voice_client = message.author.guild.voice_client
        if not voice_client:
            voice_client = await message.author.voice.channel.connect()
        voice_clients[voice_client.guild.id] = voice_client

        query = ' '.join(message.content.split()[1:])
        request = search.list(part='snippet', type='video', maxResults=5, q=query)
        response = request.execute()
        video_id = response['items'][0]['id']['videoId']
        url = prefix + video_id
        title = response['items'][0]['snippet']['title']
        if not voice_client.is_playing():
            await play(url, voice_client)
            print(f'Song({title}) now played.')
            await message.channel.send(f'Song({title}) now played.')
        else:
            song_queue.append((title, url))
            print(f'Song({title}) added to queue.')
            await message.channel.send(f'Song({title}) added to queue.')

    if message.content.startswith(";;pause"):  # Пауза
        try:
            voice_clients[message.guild.id].pause()

        except Exception as error:
            print(error)

    if message.content.startswith(";;resume"):  # Воспроизведение
        try:
            return voice_clients[message.guild.id].resume()

        except Exception as error:
            print(error)

    # if message.content.startswith(";;loop"):  # looping / unlooping
    #     try:
    #         voice_clients[message.guild.id].pause()
    #         _loop = True
    #
    #     except Exception as error:
    #         print(error)

    if message.content.startswith(";;stop"):  # Остановка бота и выход из голосового канала
        try:
            voice_clients[message.guild.id].stop()
            await voice_clients[message.guild.id].disconnect()
            del voice_clients[message.guild.id]
        except Exception as error:
            print(error)


client.run(TOKEN)
