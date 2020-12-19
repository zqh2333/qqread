#!/usr/bin/env python3
# _*_ coding:utf-8 _*_

# @Time    : 2020/12/3 1:28
# @Author  : TNanko
# @Site    : https://tnanko.github.io
# @File    : qq_read.py
# @Software: PyCharm
"""
此脚本使用 Python 语言根据 https://raw.githubusercontent.com/ziye12/JavaScript/master/Task/qqreads.js 改写
使用教程 https://github.com/TNanko/Scripts/blob/master/docs/qq_read.md
"""

import sys
import os

cur_path = os.path.abspath(os.path.dirname(__file__))
root_path = os.path.split(cur_path)[0]
sys.path.append(root_path)
import json
import re
import time
import requests
import traceback
from setup import get_standard_time
from utils import notify
from utils.configuration import read


def pretty_dict(dict):
    """
    格式化输出 json 或者 dict 格式的变量
    :param dict:
    :return:
    """
    return print(json.dumps(dict, indent=4, ensure_ascii=False))


def get_user_info(headers):
    """
    获取任务信息
    :param headers:
    :return:
    """
    url = 'https://mqqapi.reader.qq.com/mqq/user/init'
    try:
        response = requests.get(url=url, headers=headers, timeout=(5, 10)).json()
        if response['code'] == 0:
            return response['data']
        else:
            return
    except:
        print(traceback.format_exc())
        return


def open_treasure_box(headers):
    """
    每20分钟开一次宝箱
    :param headers:
    :return:
    """
    url = 'https://mqqapi.reader.qq.com/mqq/red_packet/user/treasure_box'
    try:
        response = requests.get(url=url, headers=headers, timeout=(5, 10)).json()
        time.sleep(15)
        if response['code'] == 0:
            return response['data']
        else:
            return
    except:
        print(traceback.format_exc())
        return


def watch_treasure_box_ads(headers):
    """
    看广告，宝箱奖励翻倍
    :param headers:
    :return:
    """
    url = 'https://mqqapi.reader.qq.com/mqq/red_packet/user/treasure_box_video'
    try:
        response = requests.get(url=url, headers=headers, timeout=(5, 10)).json()
        time.sleep(15)
        if response['code'] == 0:
            return response['data']
        else:
            return
    except:
        print(traceback.format_exc())
        return


def track(headers, body):
    """
    数据追踪，解决1金币问题
    :param headers:
    :param body:
    :return:
    """
    try:
        url = 'https://mqqapi.reader.qq.com/log/v4/mqq/track'
        timestamp = re.compile(r'"dis": (.*?),')
        body = json.dumps(body)
        body = re.sub(timestamp.findall(body)[0], str(int(time.time() * 1000)), str(body))
        response = requests.post(url=url, headers=headers, data=body, timeout=(5, 10)).json()
        if response['code'] == 0:
            return True
        else:
            return
    except:
        print(traceback.format_exc())
        return


def get_red_packets(headers, pn):
    """
    今日金币统计
    :param headers:
    :param pn: 金币列表序号
    :return:
    """
    try:
        url = f'https://mqqapi.reader.qq.com/mqq/red_packet/user/trans/list?pn={pn}'
        response = requests.get(url=url, headers=headers, timeout=(5, 10)).json()
        if response['code'] == 0:
            return response['data']
        else:
            return
    except:
        print(traceback.format_exc())
        return


def get_withdraw_info(headers):
    try:
        url = 'https://mqqapi.reader.qq.com/mqq/red_packet/user/withdraw/page'
        response = requests.get(url=url, headers=headers, timeout=(5, 10)).json()
        if response['code'] == 0:
            return response['data']['configList']
        else:
            return
    except:
        print(traceback.format_exc())
        return


def withdraw_to_wallet(headers, amount):
    try:
        url = f"https://mqqapi.reader.qq.com/mqq/red_packet/user/withdraw?amount={amount}"
        response = requests.post(url=url, headers=headers, timeout=(5, 10)).json()
        if response['data']['code'] == 0:
            return True
        else:
            return response['data']['msg']
    except:
        print(traceback.format_exc())
        return '访问提现接口错误！'


def qq_read():
    config_latest, config_current = read()
    # 读取企鹅读书配置
    try:
        qq_read_config = config_current['jobs']['qq_read']
    except:
        print('配置文件中没有此任务！请更新您的配置文件')
        return
    # 脚本版本检测
    try:
        if qq_read_config['skip_check_script_version']:
            print('参数 skip_check_script_version = true ，跳过脚本版本检测...')
        elif config_latest:
            if config_latest['jobs']['qq_read']['version'] > qq_read_config['version']:
                print(f"检测到最新的脚本版本号为{config_latest['jobs']['qq_read']['version']}，当前脚本版本号：{qq_read_config['version']}")
            else:
                print('当前脚本为最新版本')
        else:
            print('未获取到最新脚本的版本号')
    except:
        print('程序运行异常，跳过脚本版本检测...')
    # 获取config.yml账号信息
    accounts = qq_read_config['parameters']['ACCOUNTS']
    # 每次上传的时间
    upload_time = qq_read_config['parameters']['UPLOAD_TIME']
    # 每天最大阅读时长
    max_read_time = qq_read_config['parameters']['MAX_READ_TIME']
    # 消息推送方式
    notify_mode = qq_read_config['notify_mode']

    # 确定脚本是否开启执行模式
    if qq_read_config['enable']:
        for account in accounts:
            book_url = account['BOOK_URL']
            headers = account['HEADERS']
            body = account['BODY']
            withdraw = account['WITHDRAW']
            hosting_mode = account['HOSTING_MODE']
            utc_datetime, beijing_datetime = get_standard_time()
            symbol = '=' * 16
            print(
                f'\n{symbol}【企鹅读书】{utc_datetime.strftime("%Y-%m-%d %H:%M:%S")}/{beijing_datetime.strftime("%Y-%m-%d %H:%M:%S")} {symbol}\n')

            start_time = time.time()
            title = f'☆【企鹅读书】{beijing_datetime.strftime("%Y-%m-%d %H:%M:%S")} ☆'
            content = ''

            # 调用 track 接口，为保证输出结果美观，输出信息写在后面
            track_result = track(headers=headers, body=body)
            # 获取用户信息（昵称）
            user_info = get_user_info(headers=headers)
            if user_info:
                content += f'【用户昵称】{user_info["user"]["nickName"]}'
            # 获取任务列表，查询金币余额
            daily_tasks = get_daily_tasks(headers=headers)
            if daily_tasks:
                content += f'\n【金币余额】剩余{daily_tasks["user"]["amount"]}金币，可提现{daily_tasks["user"]["amount"] // 10000}元'
            # 查询今日获得金币数量
            beijing_datetime_0 = beijing_datetime.strftime('%Y-%m-%d') + ' 00:00:00'
            today_coins_total = 0
            is_today_red_packet = True
            for pn in range(1, 15):
                red_packets = get_red_packets(headers=headers, pn=pn)
                if red_packets and is_today_red_packet:
                    for red_packet in red_packets['list']:
                        if red_packet['content'] >= beijing_datetime_0:
                            today_coins_total += red_packet['amount']
                        else:
                            is_today_red_packet = False
                            break
                elif not red_packets:
                    content += f'\n【今日收益】请求接口错误！'
                    break
                else:
                    content += f"\n【今日收益】{today_coins_total}金币，约{'{:4.2f}'.format(today_coins_total / 10000)}元"
                    break

            # 开宝箱领金币
            if daily_tasks['treasureBox']['doneFlag'] == 0:
                treasure_box_reward = open_treasure_box(headers=headers)
                if treasure_box_reward:
                    content += f"\n【开启第{treasure_box_reward['count']}个宝箱】获得{treasure_box_reward['amount']}金币"

            # 宝箱金币奖励翻倍
            daily_tasks = get_daily_tasks(headers=headers)
            if daily_tasks['treasureBox']['videoDoneFlag'] == 0:
                treasure_box_ads_reward = watch_treasure_box_ads(headers=headers)
                if treasure_box_ads_reward:
                    content += f"\n【宝箱奖励翻倍】获得{treasure_box_ads_reward['amount']}金币"


            content += f'\n🕛耗时：%.2f秒' % (time.time() - start_time)
            content += f'\n如果帮助到您可以点下🌟STAR鼓励我一下，谢谢~'
            print(title)
            print(content)
            # 每天 22:00 - 22:10 发送消息推送
            if qq_read_config['notify'] and beijing_datetime.hour == 22 and beijing_datetime.minute <= 10:
                notify.send(title=title, content=content, notify_mode=notify_mode)
            elif not qq_read_config['notify']:
                print('未进行消息推送，原因：未设置消息推送。如需发送消息推送，请确保配置文件的对应的脚本任务中，参数notify的值为true\n')
            elif not beijing_datetime.hour == 22:
                print('未进行消息推送，原因：没到对应的推送时间点\n')
            else:
                print('未在规定的时间范围内\n')
    else:
        print('未执行该任务，如需执行请在配置文件的对应的任务中，将参数enable设置为true\n')

def main():
    qq_read()


if __name__ == '__main__':
 
