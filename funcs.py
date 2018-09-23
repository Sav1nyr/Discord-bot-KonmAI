import discord
from discord.ext import commands
from discord.ext.commands import Bot
from lxml import html
import asyncio
import datetime
import json
import os
import requests
import random
import re
import time

TOKEN = os.environ['TOKEN']

BOTNAME = 'KonmAI v0.9'
PREFIX = '`'
DESCRIPTION = ''
GAME = '도움말은 `도움'
THEME_COLOR = 0x00a0ee
URL = 'https://discord.gg/E6eXnpJ'
ICON_URL = 'https://ko.gravatar.com/userimage/54425936/ab5195334dd95d4171ac9ddab1521a5b.jpeg'

GF_TIME_FILE = 'gf_time.json'

CUSTOM_CHO_QUIZ_FILE = 'json/custom_cho_quiz.json'
GAMER_FILE = 'json/gamer.json'
MEMORY_FILE = 'json/memory.json'

ENTER_KEYWORD_MESSAGE = '검색할 키워드를 입력해 주세요'

bot = Bot(description=DESCRIPTION, command_prefix=PREFIX)

bj_games = {}  # 블랙잭
bj_msgs = {}  # 블랙잭 메시지
cho_quizs = {}  # 초성퀴즈
lots_games = {}  # 제비뽑기


# Commonly used


def to_url(keyword):
    return re.sub(' ', '%20', keyword)


def read_json(address):
    try:
        with open(address, 'r') as f:
            ret = json.loads(f.read())
            f.close()
    except IOError:  # 파일이나 파일 내용이 없는 경우
        ret = {}

    return ret


def write_json(address, dic):
    with open(address, 'w') as f:
        f.write(json.dumps(dic))
        f.close()


def make_embed(title=None, desc=None, by_me=False, footer=None, img=None):
    ret = discord.Embed(title=title,
                        description=desc, color=THEME_COLOR)
    if by_me:
        ret.set_author(name=BOTNAME,
                       url=URL, icon_url=ICON_URL)
    if footer is not None:
        ret.set_footer(text=footer)
    if img is not None:
        ret.set_image(url=img)

    return ret


async def delete_message(msg):
    if msg is not None:
        try:
            await bot.delete_message(msg)
        except discord.Forbidden:
            pass


def find_id_by_name(name):
    members = list(bot.get_all_members())
    member_names = list(map(lambda x: x.name, members))
    if name in member_names:
        i = member_names.index(name)
        return members[i].id
    else:
        return None


def find_name_by_id(id):
    member = [s.get_member(id) for s in bot.servers][0]
    if member is not None:
        return member.name
    else:
        return None


# for Commands


def bignumrize(numstr):
    """Discord 이모지로 숫자 강조. Credit for Discord bot Ayana."""
    NUM_EMOJIS = [':zero:', ':one:', ':two:', ':three:', ':four:',
                  ':five:', ':six:', ':seven:', ':eight:', ':nine:']
    ret = ''
    for c in numstr:
        ret += NUM_EMOJIS[int(c)] if c.isdigit() else c

    return ret


HAN_BASE, CHO, JUNG = 44032, 588, 28
CHO_LIST = ['ㄱ', 'ㄲ', 'ㄴ', 'ㄷ', 'ㄸ', 'ㄹ', 'ㅁ', 'ㅂ', 'ㅃ',
            'ㅅ', 'ㅆ', 'ㅇ', 'ㅈ', 'ㅉ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ']
CHO_LITE_LIST = ['ㄱ', 'ㄴ', 'ㄷ', 'ㄹ', 'ㅁ', 'ㅂ', 'ㅅ',
                 'ㅇ', 'ㅈ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ']
PARSED_CHO_LIST = ['%A1', '%A2', '%A4', '%A7', '%A8', '%A9',
                   '%B1', '%B2', '%B3', '%B5', '%B6', '%B7', '%B8', '%B9',
                   '%BA', '%BB', '%BC', '%BD', '%BE']


def cho(keyword):
    """단어를 초성으로"""
    split_keyword_list = list(keyword)
    result = []
    for letter in split_keyword_list:
        if re.match('.*[가-힣]+.*', letter) is not None:
            char_code = ord(letter) - HAN_BASE
            cho_code = int(char_code / CHO)
            result.append(CHO_LIST[cho_code])
        else:
            result.append(letter)

    return ''.join(result)


def cho_gen_lite(length):
    result = ''
    for _ in range(length):
        result += CHO_LITE_LIST[random.randint(0, 13)]

    return result


def jaum_search(genre=None, chos=cho_gen_lite(random.randint(2, 3))):
    """genre : movie, music, animal, dic, game, people, book"""
    query = ''
    for i in range(len(chos)):
        query += '%A4' + PARSED_CHO_LIST[CHO_LIST.index(chos[i])]
    if genre is None:
            page = requests.get('http://www.jaum.kr/index.php?w='+query)
    else:
        page = requests.get('http://www.jaum.kr/index.php?w='+query+'&k='+genre)
    tree = html.fromstring(page.content)

    result = tree.xpath('//*[@id="container"]/div/table/tbody/tr[1]/td[1]//text()')

    return result


def jaum_quiz(genre=None):
    if genre == '영화':
        genre = 'movie'
    elif genre == '음악':
        genre = 'music'
    elif genre == '동식물':
        genre = 'animal'
    elif genre == '사전':
        genre = 'dic'
    elif genre == '게임':
        genre = 'game'
    elif genre == '인물':
        genre = 'people'
    elif genre == '책':
        genre = 'book'
    else:
        return None

    answers = []
    while len(answers) == 0:
        answers = jaum_search(genre, cho_gen_lite(random.randint(2, 3)))
    answer = random.choice(answers)
    answer = re.sub(r'\s+$', '',
                    re.sub(r'^\s+', '',
                           re.sub(r'(?i)[A-Z().]', '', answer)))

    print('정답 : '+answer)  # DEBUG
    return answer


def josa(word, j):
    last_char = word[-1]
    has_jong = True if (ord(last_char) - HAN_BASE) % 28 > 0 else False
    if j in ['은', '는']:
        return '은' if has_jong else '는'
    elif j in ['이', '가']:
        return '이' if has_jong else '가'
    elif j in ['을', '를']:
        return '을' if has_jong else '를'
    elif j in ['으로', '로']:
        return '으로' if has_jong else '로'
    elif j in ['과', '와']:
        return '과' if has_jong else '와'
    else:
        raise Exception('josa 함수에 잘못된 인수 전달.')


class ChoQuiz:
    def __init__(self):
        self.genre = None
        self.count = None
        self.answer = None
        self.score = None

    @staticmethod
    def find(channel):
        global cho_quizs

        return cho_quizs[channel] if channel in cho_quizs else None

    @staticmethod
    def start(channel, genre, count, answer):
        global cho_quizs

        cho_quizs[channel] = ChoQuiz()
        cho_quizs[channel].genre = genre
        cho_quizs[channel].count = count
        cho_quizs[channel].answer = answer

        return cho_quizs[channel]

    @staticmethod
    def end(channel):
        global cho_quizs

        if channel in cho_quizs:
            del cho_quizs[channel]
            ret = '초성퀴즈를 종료했어요.'
        else:
            ret = '진행중인 초성퀴즈가 없어요.'

        return ret

    @staticmethod
    def add_custom(author, args):
        """args: ['정답', '설', '명', ...], quizs: {'정답': ['id', 'name', '설명']}"""
        print(author)
        print(args)
        if len(args) > 1:
            quizs = read_json(CUSTOM_CHO_QUIZ_FILE)

            if args[0] in quizs:  # 이미 등록된 정답
                mem = quizs[args[0]]
                if author.id == mem[0]:  # 수정
                    quizs[args[0]][2] = ' '.join(args[1:])
                    ret = '설명을 수정했어요.'
                else:
                    return '다른 유저님이 이미 등록한 정답이에요. :confused:'
            else:
                quizs[args[0]] = [author.id, author.name, ' '.join(args[1:])]
                ret = '새로운 초성퀴즈를 등록했어요.'

            write_json(CUSTOM_CHO_QUIZ_FILE, quizs)
            return ret
        else:
            return '` `초성 등록 정답 설명 `처럼 입력해 주세요.'

    def correct(self, channel):
        self.count -= 1
        if self.count > 0:
            self.answer = jaum_quiz(self.genre)
            return cho(self.answer)
        else:
            return ChoQuiz.end(channel)


def pubg_profile(name, server='krjp'):
    # server: krjp, jp, as, na, eu, oc, sa, sea, ru
    if server is None:
        response = requests.get('https://dak.gg/profile/'+name)
    else:
        year = str(time.gmtime().tm_year)
        month = str(time.gmtime().tm_mon)
        if len(month) < 2:
            month = '0' + month
        response = requests.get(f'https://dak.gg/profile/{name}/{year}-{month}/{server}')

    tree = html.fromstring(response.content)
    data = tree.xpath('//section[@class="solo modeItem"]//text()')
    data = list(map(lambda x: re.sub('\n', '', re.sub(' ', '', x)), data))
    data = list(filter(lambda x: x != '', data))

    if len(data) >= 44:
        ret = {}
        ret['avatar'] = tree.xpath('//div[@class="userInfo"]/img/@src')[0]
        ret['solo-playtime'] = data[1]
        ret['solo-record'] = data[2]
        ret['solo-grade'] = data[3]
        ret['solo-score'] = data[4]
        ret['solo-rank'] = data[6]
        if len(data) == 45:
            ret['solo-top'] = data[7]
        i = 7 if len(data) == 44 else 8
        ret['solo-win-rating'] = data[i]
        ret['solo-win-top'] = data[i+2]
        ret['solo-kill-rating'] = data[i+3]
        ret['solo-kill-top'] = data[i+5]
        ret['solo-kd'] = data[i+8]
        ret['solo-kd-top'] = data[i+9]
        ret['solo-winratio'] = data[i+11]
        ret['solo-winratio-top'] = data[i+12]
        ret['solo-top10'] = data[i+14]
        ret['solo-top10-top'] = data[i+15]
        ret['solo-avgdmg'] = data[i+17]
        ret['solo-avgdmg-top'] = data[i+18]
        ret['solo-games'] = data[i+20]
        ret['solo-games-top'] = data[i+21]
        ret['solo-mostkills'] = data[i+23]
        ret['solo-mostkills-top'] = data[i+24]
        ret['solo-headshots'] = data[i+26]
        ret['solo-headshots-top'] = data[i+27]
        ret['solo-longest'] = data[i+29]
        ret['solo-longest-top'] = data[i+30]
        ret['solo-survived'] = data[i+32]
        ret['solo-survived-top'] = data[i+33]
    else:
        ret = None

    return ret


def gf_time(pd_time):
    gf_times = read_json(GF_TIME_FILE)

    if len(pd_time) == 3:  # 340
        pd_time = '0' + pd_time[0] + ':' + pd_time[1:3]
    if len(pd_time) == 4:  # 0340
        pd_time = pd_time[0:2] + ':' + pd_time[2:4]
    ret = '제조시간이 **' + pd_time + '**인 전술인형: ' + ', '.join(gf_times[pd_time])

    return ret


def roll_dice(cnt, side, mention=None):  # `주사위
    try:
        dice = []
        for _ in range(cnt):
            dice.append(random.randint(1, side))

        ret = f'{mention}님의 ' if mention is not None else ''
        ret += f'{str(cnt)}d{str(side)} 주사위 결과 : '
        ret += ', '.join([str(x) for x in dice])
        ret += ' (' + str(sum(dice)) + ')'
    except ValueError:
        ret = f'{mention}님, ' if mention is not None else ''
        ret += '` `주사위 2d6 `처럼 입력해 주세요. `2`는 주사위 개수, `6`은 주사위 면수예요.'

    return ret


def memory(author, *args):  # `기억
    """args: ['키워드', '내', '용', ...], memories: {'키워드': ['id', 'name', '내용'] * n}"""
    MEMORIZE_MESSAGE = ['기억해둘게요.', 'DB에 기록했어요.']
    NOT_IN_MEMORY_MESSAGE = ['기억을 찾지 못했어요.', '그런 기억은 없어요.',
                             '기억에 없어요.', 'DB에 없는 기억이에요.']

    memories = read_json(MEMORY_FILE)

    if len(args) > 1:
        if args[0] == '삭제':
            if args[1] in memories:
                mem = memories[args[1]]
                if author.id in mem[::3]:
                    i = mem.index(author.id)
                    for _ in range(3):
                        del memories[args[1]][i]
                else:
                    return '그 키워드에 대한 '+author.name+'님의 기억은 없어요.'
            else:
                return random.choice(NOT_IN_MEMORY_MESSAGE)
        elif args[0] in memories:  # 키워드에 대한 기억 존재
            mem = memories[args[0]]
            if author.id in mem[::3]:  # 같은 유저의 기억 덮어쓰기
                i = mem.index(author.id)
                memories[args[0]][i] = author.id
                memories[args[0]][i+1] = author.name
                memories[args[0]][i+2] = ' '.join(args[1:])
            else:  # 새로운 유저의 기억
                memories[args[0]] += [author.id, author.name, ' '.join(args[1:])]
        else:  # 새로운 키워드
            memories[args[0]] = [author.id, author.name, ' '.join(args[1:])]

        write_json(MEMORY_FILE, memories)
        return random.choice(MEMORIZE_MESSAGE) if args[0] != '삭제' else '기억에서 지웠어요.'
    elif len(args) == 1:
        if args[0] == '삭제':
            return '어떤 키워드에 대한 기억을 삭제할까요? ` `기억 삭제 원주율 `처럼 입력해 주세요.'
        elif args[0] in memories or args[0] == '랜덤':
            if args[0] == '랜덤' and len(memories) > 0:
                key = random.choice(list(memories.keys()))
            elif args[0] in memories:
                key = args[0]
            else:
                return '기억이 하나도 없어요.'

            mem = memories[key]
            contents = []
            for i in range(len(mem)//3):
                contents += [mem[3*i+2]+' _- '+mem[3*i+1]+'_']
            embed = discord.Embed(title=key,
                                  description='\n'.join(contents), color=THEME_COLOR)
            embed.set_author(name=BOTNAME + ' DB', url=URL, icon_url=ICON_URL)
            return embed
        else:
            return random.choice(NOT_IN_MEMORY_MESSAGE)
    else:
        return '기억해둘 내용이나 기억해낼 내용을 입력해 주세요.'


# for GAMER


class Gamer:

    @staticmethod
    def init(id):
        gamers = read_json(GAMER_FILE)

        if id not in gamers:
            gamers[id] = {}
            gamers[id]['coin'] = 100
            write_json(GAMER_FILE, gamers)
            ret = '게이머 등록을 완료했어요.'
        else:
            ret = '이미 등록되어 있어요.'

        return ret

    @staticmethod
    def find(id):
        gamers = read_json(GAMER_FILE)

        return True if id in gamers else False

    @staticmethod
    def info(id):
        gamers = read_json(GAMER_FILE)

        if id in gamers:
            ret = '계좌에 '+str(gamers[id]['coin'])+'코인이 있어요.'
        else:
            ret = '등록되지 않은 게이머예요.'

        return ret

    @staticmethod
    def reset_coin(id):
        gamers = read_json(GAMER_FILE)

        if id in gamers:
            gamers[id]['coin'] = 100
            write_json(GAMER_FILE, gamers)
            ret = '코인을 초기화했어요.'
        else:
            ret = '등록되지 않은 게이머예요.'

        return ret

    @staticmethod
    def check_coin(id, amount):
        gamers = read_json(GAMER_FILE)

        if id in gamers:
            if gamers[id]['coin'] >= amount:
                return True

        return False

    @staticmethod
    def add_coin(id, amount):
        gamers = read_json(GAMER_FILE)

        if id in gamers:
            gamers[id]['coin'] += amount
            write_json(GAMER_FILE, gamers)
            ret = str(amount)+'코인 이체를 완료했어요.'
        else:
            ret = '등록되지 않은 게이머예요.'

        return ret

    @staticmethod
    def remove_coin(id, amount):
        gamers = read_json(GAMER_FILE)

        if id in gamers:
            if gamers[id]['coin'] >= amount:
                gamers[id]['coin'] -= amount
                write_json(GAMER_FILE, gamers)
                ret = str(amount)+'코인 이체를 완료했어요.'
            else:
                raise Exception('[!] 게이머 잔액 부족')
        else:
            raise Exception('[!] 등록되지 않은 게이머')

        return ret

    @staticmethod
    def transfer_coin(from_id, to_id, amount):
        gamers = read_json(GAMER_FILE)

        if from_id in gamers:
            if to_id in gamers:
                if gamers[from_id]['coin'] >= amount+100:
                    gamers[from_id]['coin'] -= amount
                    gamers[to_id]['coin'] += amount
                    write_json(GAMER_FILE, gamers)
                    ret = str(amount)+'코인 이체를 완료했어요.'
                else:
                    ret = '잔액이 부족해요. 잔고가 100코인 이상 남아야 해요.'
            else:
                ret = '받는 게이머를 찾지 못했어요.'
        else:
            ret = '등록되지 않은 게이머예요.'

        return ret


class PlayingCard:
    NUMBERS = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
    SUITS = [':clubs:', ':diamonds:', ':hearts:', ':spades:']

    def __init__(self, number, suit, value, point):
        self.number = number
        self.suit = suit
        self.value = value
        self.point = point

    def __str__(self):
        return self.suit + self.number

    @staticmethod
    def str(cards):
        return [str(card) for card in cards]

    @staticmethod
    def bj_sum(cards):
        ret = sum(card.value for card in cards)
        cnt_a = list(map(lambda x: x.number, cards)).count('A')
        ret += cnt_a * 10
        if ret > 21:
            for _ in range(cnt_a):
                ret -= 10
                if ret <= 21:
                    break

        return ret


class Deck:
    def __init__(self):
        self.cards = []
        point = 1
        for i, number in enumerate(PlayingCard.NUMBERS):
            for suit in PlayingCard.SUITS:
                self.cards.append(PlayingCard(number, suit, min(i + 1, 10), point))
                point += 1

    def shuffle(self):
        random.shuffle(self.cards)

    def size(self):
        return len(self.cards)

    def draw(self):
        return self.cards.pop()

    def top(self):
        return self.cards[-1]  # if len(self.cards) > 0 else None


class Blackjack:
    BLACKJACKED, WIN, DRAW, LOSE = 1, 2, 4, 8
    BLACKJACK_MESSAGES = ['블랙잭!!']
    HIT_MESSAGES = ['히트.', '히트!', '히트다 히트!', '한 장 더 뽑을게요.']
    HIT_MESSAGES_FIRST = ['저는 히트할게요.']
    HIT_MESSAGES_MORE = []
    STAND_MESSAGES = ['스탠드.', '스탠드!']
    STAND_MESSAGES_HIT = ['여기까지 할게요.']
    STAND_MESSAGES_NOHIT = ['저는 바로 스탠드할게요.']
    BUST_MESSAGES_PLAYER = ['버스트!', '버스트! 욕심이었어요.']
    BUST_MESSAGES_DEALER = ['왝.', '아니!', '버스트. 저의 패배예요.']
    WIN_MESSAGES_PLAYER = ['제가 졌어요.', '저의 패배예요.', '졌어요. 제법이시군요.']
    WIN_MESSAGES_DEALER = ['제가 이겼어요!', '저의 승리예요!', '특이점은 온다!']
    DRAW_MESSAGES = ['비겼네요.', '무승부예요.', '무승부! 한 판 더 하실래요?']

    def __init__(self, player, bet=None):
        self.player = player
        self.bet = bet
        self.cnt_dhit = 0
        self.deck = Deck()
        self.deck.shuffle()
        self.pcards = [self.deck.draw(), self.deck.draw()]  # player
        self.dcards = [self.deck.draw(), self.deck.draw()]  # dealer
        self.calc_psum()
        self.calc_dsum()

    def __str__(self):
        return 'KonmAI의 패: {} ({} + ?)\n{}님의 패: {} ({})'.format(
            ', '.join(PlayingCard.str(self.dcards[0:-1])),
            str(PlayingCard.bj_sum(self.dcards[0:-1])), self.player.name, ', '.join(PlayingCard.str(self.pcards)), str(PlayingCard.bj_sum(self.pcards)))

    def result(self):
        return 'KonmAI의 패: {} ({})\n{}님의 패: {} ({})'.format(
            ', '.join(PlayingCard.str(self.dcards)),
            str(PlayingCard.bj_sum(self.dcards)), self.player.name, ', '.join(PlayingCard.str(self.pcards)), str(PlayingCard.bj_sum(self.pcards)))

    @staticmethod
    def sum(cards):
        ret = sum(card.value for card in cards)
        cnt_a = list(map(lambda x: x.number, cards)).count('A')
        ret += cnt_a * 10
        if ret > 21:
            for _ in range(cnt_a):
                ret -= 10
                if ret <= 21:
                    break

        return ret

    @staticmethod
    def end(player, result):
        global bj_games
        global bj_msgs

        if player in bj_games:
            bet = bj_games[player].bet
            if bet is not None:
                if result == BLACKJACKED:
                    Gamer.add_coin(player.id, bet * 3)
                elif result == WIN:
                    Gamer.add_coin(player.id, bet * 2)
                elif result == DRAW:
                    Gamer.add_coin(player.id, bet)
            del bj_games[player]
        if player in bj_msgs:
            del bj_msgs[player]

    def calc_psum(self):
        self.psum = Blackjack.sum(self.pcards)

    def calc_dsum(self):
        self.dsum = Blackjack.sum(self.dcards)

    def p_draw(self):
        self.pcards.append(self.deck.draw())
        self.calc_psum()

    def d_draw(self):
        self.dcards.append(self.deck.draw())
        self.calc_dsum()


async def blackjack_dturn(player, channel):  # Dealer's turn
    d_msg = None
    while True:
        if bj_games[player].dsum < 17:  # 딜러 히트
            await asyncio.sleep(1.0)
            if bj_games[player].cnt_dhit > 0:
                await delete_message(d_msg)
                d_msg = await bot.send_message(channel, random.choice(Blackjack.HIT_MESSAGES + Blackjack.HIT_MESSAGES_MORE))
            else:
                await delete_message(d_msg)
                d_msg = await bot.send_message(channel, random.choice(Blackjack.HIT_MESSAGES + Blackjack.HIT_MESSAGES_FIRST))
            bj_games[player].cnt_dhit += 1
            bj_games[player].d_draw()
            await asyncio.sleep(1.0)
            if bj_games[player].dsum > 21:
                await asyncio.sleep(1.0)
                await bot.edit_message(bj_msgs[player], bj_games[player].result())
                await asyncio.sleep(0.5)
                await delete_message(d_msg)
                await bot.send_message(channel, random.choice(Blackjack.BUST_MESSAGES_DEALER))
                Blackjack.end(player, Blackjack.WIN)
                break
            else:
                await bot.edit_message(bj_msgs[player], bj_games[player])
        else:  # 딜러 스탠드
            await asyncio.sleep(1.0)
            if bj_games[player].cnt_dhit > 0:
                await delete_message(d_msg)
                d_msg = await bot.send_message(channel, random.choice(Blackjack.STAND_MESSAGES + Blackjack.STAND_MESSAGES_HIT))
            else:
                await delete_message(d_msg)
                d_msg = await bot.send_message(channel, random.choice(Blackjack.STAND_MESSAGES + Blackjack.STAND_MESSAGES_NOHIT))
            break

    if player in bj_games:
        await asyncio.sleep(1.0)
        await bot.edit_message(bj_msgs[player], bj_games[player].result())
        await asyncio.sleep(1.0)
        if bj_games[player].psum > bj_games[player].dsum:
            await delete_message(d_msg)
            await bot.send_message(channel, random.choice(Blackjack.WIN_MESSAGES_PLAYER))
            if bj_games[player].psum != 21:
                Blackjack.end(player, Blackjack.WIN)
            else:
                Blackjack.end(player, BLACKJACKED)
        elif bj_games[player].psum < bj_games[player].dsum:
            await delete_message(d_msg)
            await bot.send_message(channel, random.choice(Blackjack.WIN_MESSAGES_DEALER))
            Blackjack.end(player, Blackjack.LOSE)
        else:
            await delete_message(d_msg)
            await bot.send_message(channel, random.choice(Blackjack.DRAW_MESSAGES))
            Blackjack.end(player, Blackjack.DRAW)

    await bot.change_presence(game=discord.Game(name=GAME))
