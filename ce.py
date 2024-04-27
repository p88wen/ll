import requests
import re
import base64
import datetime
from datetime import datetime
from urllib.parse import urlparse
import time
import concurrent.futures
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import os
import threading
from queue import Queue
import eventlet
eventlet.monkey_patch()

#修改需要查询的省份
province_names = ["广东"]
for province in province_names:
    current_time = datetime.now()
    timeout_cnt = 0
    result_urls = set()
    str_channels = ''
    while len(result_urls) == 0 and timeout_cnt <= 5:
        try:
            search_url = 'https://fofa.info/result?qbase64='
            search_txt = f'\"udpxy\" && country=\"CN\" && region=\"{province}\"'
                # 将字符串编码为字节流
            bytes_string = search_txt.encode('utf-8')
                # 使用 base64 进行编码
            search_txt = base64.b64encode(bytes_string).decode('utf-8')
            search_url += search_txt
            print(f"{current_time} province : {province}，search_url : {search_url}")
            # 创建一个Chrome WebDriver实例
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')

            driver = webdriver.Chrome(options=chrome_options)

            # 使用WebDriver访问网页
            driver.get(search_url)  # 将网址替换为你要访问的网页地址
            time.sleep(10)  # 等待页面加载完成，可以根据实际情况调整等待时间

            # 获取网页内容
            page_content = driver.page_source

            # 关闭WebDriver
            driver.quit()
            # 查找所有符合指定格式的网址
            # 设置匹配的格式，如http://8.8.8.8:8888
            pattern = r"http://\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d+"
            urls_all = re.findall(pattern, page_content)
                # 去重得到唯一的URL列表
            result_urls = set(urls_all)
            print(f"{current_time} result_urls:{result_urls}")
        except (requests.Timeout, requests.RequestException) as e:
            timeout_cnt += 1
            print(f"{current_time} [{province}]搜索请求发生超时，异常次数：{timeout_cnt}")
            if timeout_cnt <= 5:
                    # 继续下一次循环迭代
                continue
            else:
                print(f"{current_time} 搜索IPTV频道源[]，超时次数过多：{timeout_cnt} 次，停止处理")
            
#对应省份的组播地址:重庆联通cctv1：225.0.4.74:7980，重庆电信cctv1:235.254.199.51:7980，广东电信广东卫视239.77.1.19:5146
urls_udp = "/status"

def is_url_accessible(url):
    try:
        response = requests.get(url, timeout=0.5)
        if response.status_code == 200:
            return url
    except requests.exceptions.RequestException:
        pass
    return None

valid_ips = []

# 遍历所有视频链接
for url in result_urls:
    ip_port = url.replace("http://", "")
    video_url = url + urls_udp

    # 检测链接是否有效
    if is_url_accessible(video_url):
        valid_ips.append(ip_port)
    else:
        print(f"{current_time} {video_url} 无效")

# 将有效的结果保存到res.txt文件中
with open("res.txt", "w") as file:
    for ip in valid_ips:
        file.write(ip + "\n")

print(f"可用IP为：{valid_ips},已保存至res.txt")
