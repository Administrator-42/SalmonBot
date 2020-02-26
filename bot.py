# -*-coding: utf-8-*-

import discord
from discord.ext import tasks, commands
import asyncio
import json
import time
import platform
import datetime
import pymysql
import logging
import logging.handlers
import paramiko
import re
import os
import urllib.request

# =============== Local Data Load ===============
with open('./data/config.json', encoding='utf-8') as config_file:
    config = json.load(config_file)
with open('./data/version.json', encoding='utf-8') as version_file:
    version = json.load(version_file)

# IMPORTant data
if platform.system() == 'Windows':
    with open('C:/salmonbot/' + config['tokenFileName'], encoding='utf-8') as token_file:
        token = token_file.readline()
    with open('C:/salmonbot/' + config['dbacName'], encoding='utf-8') as dbac_file:
        dbac = json.load(dbac_file)
    with open('C:/salmonbot/' + config['sshFileName'], encoding='utf-8') as ssh_file:
        ssh = json.load(ssh_file)
    with open('C:/salmonbot/' + config['openapiFileName'], encoding='utf-8') as openapi_file:
        openapi = json.load(openapi_file)
elif platform.system() == 'Linux':
    with open('/.salmonbot/' + config['tokenFileName'], encoding='utf-8') as token_file:
        token = token_file.readline()
    with open('/.salmonbot/' + config['dbacName'], encoding='utf-8') as dbac_file:
        dbac = json.load(dbac_file)
    with open('/.salmonbot/' + config['sshFileName'], encoding='utf-8') as ssh_file:
        ssh = json.load(ssh_file)
    with open('/.salmonbot/' + config['openapiFileName'], encoding='utf-8') as openapi_file:
        openapi = json.load(openapi_file)

botname = config['botName']
prefix = config['prefix']
activity = config['activity']
status = config['status']
boticon = config['botIconUrl']
thumbnail = config['thumbnailUrl']
color = config['color']
for i in color.keys(): # convert HEX to DEC
    color[i] = int(color[i], 16)

versionNum = version['versionNum']
versionPrefix = version['versionPrefix']

seclist =[]
black = []

# =============== SSH connect ===============
sshclient = paramiko.SSHClient()
sshclient.set_missing_host_key_policy(paramiko.AutoAddPolicy)
sshclient.connect(ssh['host'], username=ssh['user'], password=ssh['password'], port=ssh['port'])

def sshcmd(cmd):
    stdin, stdout, stderr = sshclient.exec_command(cmd)
    lines = stdout.readlines()
    return ''.join(lines)

# =============== Database server connect ===============
db = pymysql.connect(
    host=dbac['host'],
    user=dbac['dbUser'],
    password=dbac['dbPassword'],
    db=dbac['dbName'],
    charset='utf8'
)
cur = db.cursor(pymysql.cursors.DictCursor)

# =============== NAVER Open API ===============
naverapi_id = openapi['naver']['clientID']
naverapi_secret = openapi['naver']['clientSec']

def naverSearch_blog(text):
    encText = urllib.parse.quote(text)
    url = "https://openapi.naver.com/v1/search/blog?query=" + encText + '&display=100'
    request = urllib.request.Request(url)
    request.add_header("X-Naver-Client-Id", naverapi_id)
    request.add_header("X-Naver-Client-Secret", naverapi_secret)
    response = urllib.request.urlopen(request)
    rescode = response.getcode()
    if rescode == 200:
        results = json.load(response)
        return results
    else:
        return rescode

# =============== Logging ===============
logger = logging.getLogger('salmonbot')
logger.setLevel(logging.DEBUG)
log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
log_streamh = logging.StreamHandler()
log_streamh.setFormatter(log_formatter)
logger.addHandler(log_streamh)
log_fileh = logging.handlers.RotatingFileHandler('./logs/general/salmon.log', maxBytes=config['maxlogbytes'], backupCount=10)
log_fileh.setFormatter(log_formatter)
logger.addHandler(log_fileh)
pinglogger = logging.getLogger('ping')
pinglogger.setLevel(logging.INFO)
ping_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
ping_fileh = logging.handlers.RotatingFileHandler('./logs/ping/ping.log', maxBytes=config['maxlogbytes'], backupCount=10)
ping_fileh.setFormatter(ping_formatter)
pinglogger.addHandler(ping_fileh)

logger.info('========== START ==========')
logger.info('Data Load Complete.')

# ================ Bot Command ===============
client = discord.Client()

@client.event
async def on_ready():
    logger.info(f'Logged in as {client.user}')
    tensecloop.start()
    await client.change_presence(status=eval(f'discord.Status.{status}'), activity=discord.Game(activity)) # presence 를 설정 데이터 첫째로 적용합니다.

@tasks.loop(seconds=5)
async def tensecloop():
    global ping, pinglevel, seclist, dbping
    try:
        ping = round(1000 * client.latency)
        if ping <= 100: pinglevel = '🔵 매우좋음'
        elif ping > 100 and ping <= 250: pinglevel = '🟢 양호함'
        elif ping > 250 and ping <= 400: pinglevel = '🟡 보통'
        elif ping > 400 and ping <= 550: pinglevel = '🔴 나쁨'
        elif ping > 550: pinglevel = '⚫ 매우나쁨'
        pinglogger.info(f'{ping}ms')
        pinglogger.info(f'{db.open}')
        dbip = config['dbIP']
        pingcmd = os.popen(f'ping -n 1 {dbip}').readlines()[-1]
        dbping = re.findall('\d+', pingcmd)[1]
        if not str(globalmsg.author.id) in black:
            if seclist.count(spamuser) >= 8:
                black.append(spamuser)
                await globalmsg.channel.send(f'🤬 <@{spamuser}> 너님은 차단되었고 영원히 명령어를 쓸 수 없습니다. 사유: 명령어 도배')
                msglog(message.author.id, message.channel.id, message.content, '[차단됨. 사유: 명령어 도배]', fwhere_server=serverid_or_type)
            seclist = []
    except: pass

@client.event
async def on_message(message):
    global spamuser, globalmsg
    if message.author == client.user:
        return
    if message.author.bot:
        return
    if message.author.id in black:
        return
    if message.content == prefix:
        return
    # 서버인지 아닌지 확인
    if message.channel.type == discord.ChannelType.group or message.channel.type == discord.ChannelType.private: serverid_or_type = message.channel.type
    else: serverid_or_type = message.guild.id
    
    # 일반 사용자 커맨드.
    if message.content.startswith(prefix):
        globalmsg = message
        spamuser = str(message.author.id)
        seclist.append(spamuser)
        def checkmsg(m):
            return m.channel == message.channel and m.author == message.author
        userexist = cur.execute('select * from userdata where id=%s', message.author.id) # 유저 등록 여부
        # 등록 확인
        if userexist == 0:
            if message.content == prefix + '등록':
                await message.channel.send(f'<@{message.author.id}>')
                embed = discord.Embed(title=f'{botname} 등록', description='**연어봇을 이용하기 위한 이용약관 및 개인정보 취급방침입니다. 동의하시면 20초 안에 `동의`를 입력해주세요.**', color=color['ask'], timestamp=datetime.datetime.utcnow())
                embed.add_field(name='ㅤ', value='[이용약관](https://www.infiniteteam.me/tos)\n', inline=True)
                embed.add_field(name='ㅤ', value='[개인정보 취급방침](https://www.infiniteteam.me/privacy)\n', inline=True)
                await message.channel.send(embed=embed)
                msglog(message.author.id, message.channel.id, message.content, '[등록: 이용약관 및 개인정보 취급방침의 동의]', fwhere_server=serverid_or_type) 
                try:
                    msg = await client.wait_for('message', timeout=20.0, check=checkmsg)
                except asyncio.TimeoutError:
                    await message.channel.send('시간이 초과되었습니다.')
                    msglog(message.author.id, message.channel.id, message.content, '[등록: 시간 초과]', fwhere_server=serverid_or_type)
                else:
                    if msg.content == '동의':
                        if cur.execute('select * from userdata where id=%s', (msg.author.id)) == 0:
                            now = datetime.datetime.now()
                            if cur.execute('insert into userdata values (%s, %s, %s, %s)', (msg.author.id, 1, 'User', datetime.date(now.year, now.month, now.day))) == 1:
                                db.commit()
                                await message.channel.send(f'등록되었습니다. `{prefix}도움` 명령으로 전체 명령을 볼 수 있습니다.')
                                msglog(message.author.id, message.channel.id, message.content, '[등록: 등록 완료]', fwhere_server=serverid_or_type)
                        else:
                            await message.channel.send('이미 등록된 사용자입니다.')
                            msglog(message.author.id, message.channel.id, message.content, '[등록: 이미 등록됨]', fwhere_server=serverid_or_type)
                    else:
                        await message.channel.send('취소되었습니다.')
                        msglog(message.author.id, message.channel.id, message.content, '[등록: 취소됨]', fwhere_server=serverid_or_type)
            else:
                embed=discord.Embed(title='❔ 미등록 사용자', description=f'**등록되어 있지 않은 사용자입니다!**\n`{prefix}등록`명령을 입력해서, 약관에 동의해주세요.', color=color['error'], timestamp=datetime.datetime.utcnow())
                embed.set_author(name=botname, icon_url=boticon)
                embed.set_footer(text=message.author, icon_url=message.author.avatar_url)
                await message.channel.send(embed=embed)
                msglog(message.author.id, message.channel.id, message.content, '[미등록 사용자]', fwhere_server=serverid_or_type)

        elif userexist == 1: # 일반 사용자 명령어
            if message.content == prefix + '등록':
                await message.channel.send('이미 등록된 사용자입니다!')
            elif message.content == prefix + '블랙':
                await message.channel.send(str(black))
            elif message.content == prefix + '샌즈':
                await message.channel.send('와!')
                msglog(message.author.id, message.channel.id, message.content, '[와 샌즈]', fwhere_server=serverid_or_type)

            elif message.content == prefix + '정보':
                embed=discord.Embed(title='봇 정보', description=f'봇 이름: {botname}\n봇 버전: {versionPrefix}{versionNum}', color=color['info'], timestamp=datetime.datetime.utcnow())
                embed.set_thumbnail(url=thumbnail)
                embed.set_author(name=botname, icon_url=boticon)
                embed.set_footer(text=message.author, icon_url=message.author.avatar_url)
                await message.channel.send(embed=embed)
                msglog(message.author.id, message.channel.id, message.content, '[정보]', fwhere_server=serverid_or_type)

            elif message.content == prefix + '핑':
                embed=discord.Embed(title='🏓 퐁!', description=f'**디스코드 지연시간: **{ping}ms - {pinglevel}\n**데이터서버 지연시간: **{dbping}ms\n\n디스코드 지연시간은 디스코드 웹소켓 프로토콜의 지연 시간(latency)을 뜻합니다.', color=color['error'], timestamp=datetime.datetime.utcnow())
                embed.set_author(name=botname, icon_url=boticon)
                embed.set_footer(text=message.author, icon_url=message.author.avatar_url)
                await message.channel.send(embed=embed)
                msglog(message.author.id, message.channel.id, message.content, '[핑]', fwhere_server=serverid_or_type)

            elif message.content == prefix + '서버상태 데이터서버':
                dbalive = None
                try: db.ping(reconnect=False)
                except: dbalive = 'Closed'
                else: dbalive = 'Alive'

                temp = sshcmd('vcgencmd measure_temp') # CPU 온도 불러옴 (RPi 전용)
                temp = temp[5:]
                cpus = sshcmd("mpstat -P ALL | tail -5 | awk '{print 100-$NF}'") # CPU별 사용량 불러옴
                cpulist = cpus.split('\n')[:-1]

                mem = sshcmd('free -m')
                memlist = re.findall('\d+', mem)
                memtotal, memused, memfree, membc, swaptotal, swapused, swapfree = memlist[0], memlist[1], memlist[2], memlist[4], memlist[6], memlist[7], memlist[8]
                memrealfree = str(int(memfree) + int(membc))
                membarusedpx = round((int(memused) / int(memtotal)) * 10)
                memusedpct = round((int(memused) / int(memtotal)) * 100)
                membar = '|' + '▩' * membarusedpx + 'ㅤ' * (10 - membarusedpx) + '|'
                swapbarusedpx = round((int(swapused) / int(swaptotal)) * 10)
                swapusedpct = round((int(swapused) / int(swaptotal)) * 100)
                swapbar = '|' + '▩' * swapbarusedpx + 'ㅤ' * (10 - swapbarusedpx) + '|'

                embed=discord.Embed(title='🖥 데이터서버 상태', description=f'데이터베이스 연결 열림: **{db.open}**\n데이터베이스 서버 상태: **{dbalive}**', color=color['info'], timestamp=datetime.datetime.utcnow())
                embed.add_field(name='CPU사용량', value=f'```  ALL: {cpulist[0]}%\nCPU 0: {cpulist[1]}%\nCPU 1: {cpulist[2]}%\nCPU 2: {cpulist[3]}%\nCPU 3: {cpulist[4]}%\nCPU 온도: {temp}```', inline=True)
                embed.add_field(name='메모리 사용량', value=f'메모리\n```{membar}\n {memused}M/{memtotal}M ({memusedpct}%)```스왑 메모리\n```{swapbar}\n {swapused}M/{swaptotal}M ({swapusedpct}%)```', inline=True)
                embed.set_author(name=botname, icon_url=boticon)
                embed.set_footer(text=message.author, icon_url=message.author.avatar_url)
                await message.channel.send(embed=embed)
                msglog(message.author.id, message.channel.id, message.content, '[서버상태 데이터서버]', fwhere_server=serverid_or_type)

            elif message.content.startswith(prefix + '네이버검색'):
                if message.content.startswith(prefix + '네이버검색 블로그'):
                    cmdlen = 9
                    if len(prefix + message.content) >= len(prefix)+1+cmdlen and message.content[1+cmdlen] == ' ':
                        page = 0
                        word = message.content[len(prefix)+1+cmdlen:]
                        blogsc = naverSearch_blog(word)
                        if blogsc == 429:
                            await message.channel.send('봇이 하루 사용 가능한 네이버 검색 횟수가 초과되었습니다! 내일 다시 시도해주세요.')
                            msglog(message.author.id, message.channel.id, message.content, '[네이버검색: 횟수초과]', fwhere_server=serverid_or_type)
                        elif type(blogsc) == int:
                            await message.channel.send(f'오류! 코드: {blogsc}\n검색 결과를 불러올 수 없습니다. 네이버 API의 일시적인 문제로 예상되며, 나중에 다시 시도해주세요.')
                            msglog(message.author.id, message.channel.id, message.content, '[네이버검색: 오류]', fwhere_server=serverid_or_type)
                        else:
                            print(len(blogsc['items']))
                            for linenum in range(len(blogsc['items'])):
                                blogsc['items'][linenum]['title'] = blogsc['items'][linenum]['title'].replace('<b>', '`')
                                blogsc['items'][linenum]['title'] = blogsc['items'][linenum]['title'].replace('</b>', '`')
                                blogsc['items'][linenum]['description'] = blogsc['items'][linenum]['description'].replace('<b>', '`')
                                blogsc['items'][linenum]['description'] = blogsc['items'][linenum]['description'].replace('</b>', '`')
                            def naverblogembed(pg, one):
                                embed=discord.Embed(title=f'🔍 네이버 블로그 검색 결과 - `{word}`', color=color['websearch'], timestamp=datetime.datetime.utcnow())
                                for af in range(one):
                                    print(page*one+af)
                                    title = blogsc['items'][page*one+af]['title']
                                    link = blogsc['items'][page*one+af]['link']
                                    description = blogsc['items'][page*one+af]['description']
                                    bloggername = blogsc['items'][page*one+af]['bloggername']
                                    bloggerlink = blogsc['items'][page*one+af]['bloggerlink']
                                    postdate_year = int(blogsc['items'][page*one+af]['postdate'][0:4])
                                    postdate_month = int(blogsc['items'][page*one+af]['postdate'][4:6])
                                    postdate_day = int(blogsc['items'][page*one+af]['postdate'][6:8])
                                    postdate = f'{postdate_year}년 {postdate_month}월 {postdate_day}일'
                                    embed.add_field(name="ㅤ", value=f"**[{title}]({link})**\n{description}\n- [*{bloggername}*]({bloggerlink}) / **{postdate}**", inline=False)
                                embed.add_field(name="ㅤ", value=f"```{page+1}/{round(100/one)} 페이지, 총 {blogsc['total']}건 중 100건, 정확도순```", inline=False)
                                embed.set_author(name=botname, icon_url=boticon)
                                embed.set_footer(text=message.author, icon_url=message.author.avatar_url)
                                return embed
                            blogresult = await message.channel.send(embed=naverblogembed(page, 4))
                            for emoji in ['⏪', '◀', '⏹', '▶', '⏩']:
                                await blogresult.add_reaction(emoji)
                            msglog(message.author.id, message.channel.id, message.content, '[네이버검색: 블로그검색]', fwhere_server=serverid_or_type)
                            def naverblogcheck(reaction, user):
                                return user == message.author and str(reaction.emoji) in ['⏪', '◀', '⏹', '▶', '⏩']
                            while True:
                                print('loop')
                                try:
                                    reaction, user = await client.wait_for('reaction_add', timeout=300.0, check=naverblogcheck)
                                except asyncio.TimeoutError:
                                    await blogresult.clear_reactions()
                                    break
                                else:
                                    if reaction.emoji == '⏹':
                                        print('s')
                                        await blogresult.clear_reactions()
                                        break
                                    if reaction.emoji == '▶':
                                        await blogresult.remove_reaction('▶', user)
                                        if page < 25-1:
                                            page += 1
                                        else:
                                            return
                                    if reaction.emoji == '◀':
                                        await blogresult.remove_reaction('◀', user)
                                        if page > 1-1: 
                                            page -= 1
                                        else:
                                            return
                                    if reaction.emoji == '⏩':
                                        await blogresult.remove_reaction('⏩', user)
                                        if page < 25-5:
                                            page += 4
                                        else:
                                            page = 24
                                    if reaction.emoji == '⏪':
                                        await blogresult.remove_reaction('⏪', user)
                                        if page > 25-5:
                                            page -= 4
                                        else:
                                            page = 0
                                    await blogresult.edit(embed=naverblogembed(page, 4))
                                        
                            msglog(message.author.id, message.channel.id, message.content, '[네이버검색: 블로그검색 정지]', fwhere_server=serverid_or_type)

            else:
                embed=discord.Embed(title='**❌ 존재하지 않는 명령입니다!**', description=f'`{prefix}도움`을 입력해서 전체 명령어를 볼 수 있어요.', color=color['error'], timestamp=datetime.datetime.utcnow())
                embed.set_author(name=botname, icon_url=boticon)
                embed.set_footer(text=message.author, icon_url=message.author.avatar_url)
                await message.channel.send(embed=embed)
                msglog(message.author.id, message.channel.id, message.content, '[존재하지 않는 명령어]', fwhere_server=serverid_or_type)
        
        else:
            errormsg('DB.FOUND_DUPLICATE_USER', serverid_or_type)
            await globalmsg.channel.send(embed=embed)
            

# 메시지 로그 출력기 - 
# 함수 인자: fwho: 수신자, fwhere_channel: 수신 채널 아이디, freceived: 수신한 메시지 내용, fsent: 발신한 메시지 요약, fetc: 기타 기록, fwhere_server: 수신 서버 아이디
# 출력 형식: [날짜&시간] [ChannelType:] (채널 유형- DM/Group/서버아이디), [Author:] (수신자 아이디), [RCV:] (수신한 메시지 내용), [Sent:] (발신한 메시지 내용), [etc:] (기타 기록)
def msglog(fwho, fwhere_channel, freceived, fsent, fetc=None, fwhere_server=None):
    if fwhere_server == discord.ChannelType.group:
        logline = f'[ChannelType:] Group, [ChannelID:] {fwhere_channel}, [Author:] {fwho}, [RCV]: {freceived}, [Sent]: {fsent}, [etc]: {fetc}'
    elif fwhere_server == discord.ChannelType.private:
        logline = f'[ChannelType:] DM, [ChannelID:] {fwhere_channel}, [Author:] {fwho}, [RCV]: {freceived}, [Sent]: {fsent}, [etc]: {fetc}'
    else:
        logline = f'[ServerID:] {fwhere_server}, [ChannelID:] {fwhere_channel}, [Author:] {fwho}, [RCV:] {freceived}, [Sent:] {fsent}, [etc:] {fetc}'
    logger.info(logline)

def errormsg(error, where='idk'):
    embed=discord.Embed(title='**❌ 무언가 오류가 발생했습니다!**', description='오류가 기록되었습니다. 시간이 되신다면, 오류 정보를 개발자에게 알려주시면 감사하겠습니다.\n오류 코드: ```{error}```', color=color['error'], timestamp=datetime.datetime.utcnow())
    embed.set_author(name=botname, icon_url=boticon)
    embed.set_footer(text=globalmsg.author, icon_url=globalmsg.author.avatar_url)
    msglog(globalmsg.author.id, globalmsg.channel.id, globalmsg.content, '[존재하지 않는 명령어입니다!]', fwhere_server=where)

client.run(token)