#!/usr/bin/env python
# -*- coding: utf-8 -*-
import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
"""
V2EX Hot Topics Scraper
抓取 V2EX 热议主题列表数据

Usage:
    python v2ex_hot_scraper.py
"""

import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import urllib3
import re

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def parse_topic_id_from_url(url):
    """从URL中提取主题ID"""
    match = re.search(r'/t/(\d+)', url)
    if match:
        return int(match.group(1))
    return None


def scrape_v2ex_hot():
    """抓取 V2EX 热议主题列表"""

    url = "https://www.v2ex.com/?tab=hot"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }

    try:
        print(f"正在抓取 {url}")
        response = requests.get(url, headers=headers, timeout=30, verify=False)
        response.raise_for_status()
        response.encoding = 'utf-8'

        soup = BeautifulSoup(response.text, 'html.parser')
        print(f"获取到HTML长度: {len(response.text)}")

        topics = []

        # 查找所有主题项
        topic_items = soup.find_all('div', class_='cell item')

        for item in topic_items:
            topic = {}

            # 标题和链接
            title_elem = item.find('a', class_='topic-link')
            if title_elem:
                topic['title'] = title_elem.text.strip()
                topic_url = title_elem.get('href', '')
                topic_id = parse_topic_id_from_url(topic_url)
                if topic_id:
                    topic['id'] = topic_id

            # 节点信息
            node_elem = item.find('a', class_='node')
            if node_elem:
                topic['nodeTitle'] = node_elem.text.strip()
                node_url = node_elem.get('href', '')
                if node_url:
                    # 提取节点URL路径
                    topic['nodeUrl'] = node_url.replace('/go/', '')

            # 用户头像和用户名
            avatar_elem = item.find('img', class_='avatar')
            if avatar_elem:
                avatar_url = avatar_elem.get('src', '')
                # 处理头像URL，确保是完整URL
                if avatar_url.startswith('//'):
                    avatar_url = 'https:' + avatar_url
                elif not avatar_url.startswith('http'):
                    avatar_url = 'https://www.v2ex.com' + avatar_url
                topic['avatar'] = avatar_url

            # 作者用户名
            author_elem = item.find('strong')
            if author_elem and author_elem.find('a'):
                topic['username'] = author_elem.find('a').text.strip()

            # 回复数
            reply_elem = item.find('a', class_='count_livid')
            if reply_elem:
                topic['replyCount'] = int(reply_elem.text.strip())
            else:
                topic['replyCount'] = 0

            # 最后回复信息
            topic_info = item.find('span', class_='topic_info')
            if topic_info:
                info_text = topic_info.text.strip()

                # 提取最后回复时间（如"4 分钟前"）
                time_match = re.search(r'(\d+\s*[分秒小时天周月年]+前)', info_text)
                if time_match:
                    topic['lastReplyDateAgo'] = time_match.group(1)

                # 提取最后回复用户名
                last_reply_links = topic_info.find_all('a')
                if len(last_reply_links) > 1:
                    # 通常第二个链接是最后回复的用户
                    topic['lastReplyUsername'] = last_reply_links[-1].text.strip()

            # 设置默认值
            topic['isTop'] = False

            # 尝试计算具体时间（这里只是示例，实际时间需要根据"几分钟前"等计算）
            now = datetime.now()
            if 'lastReplyDateAgo' in topic:
                topic['lastReplyDate'] = now.strftime('%Y-%m-%d %H:%M:%S')

            if topic.get('title') and topic.get('id'):
                topics.append(topic)

        return topics

    except requests.RequestException as e:
        print(f"请求失败: {e}")
        return []
    except Exception as e:
        print(f"解析失败: {e}")
        return []


def save_to_json(data, filename=None):
    """保存数据到 JSON 文件"""
    if filename is None:
        # 创建 hot 目录（如果不存在）
        import os
        os.makedirs('hot', exist_ok=True)
        
        # 使用 YYYY-M-D 格式（Windows兼容格式）
        now = datetime.now()
        timestamp = f"{now.year}-{now.month}-{now.day}"
        filename = f'hot/{timestamp}.json'

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    print(f"数据已保存到 {filename}")
    return filename


def main():
    """主函数"""
    print("=" * 80)
    print("V2EX 热议主题抓取工具")
    print("=" * 80)

    # 抓取数据
    topics = scrape_v2ex_hot()

    if topics:

        # 保存到文件
        filename = save_to_json(topics)

    else:
        print("未能抓取到数据，请检查网络连接或稍后重试")


if __name__ == "__main__":
    main()
