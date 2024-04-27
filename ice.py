import requests
import base64
import re
import os
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# 获取rtp目录下的文件名
files = os.listdir('rtp')

files_name = []

# 去除后缀名并保存至provinces_isps
for file in files:
    name, extension = os.path.splitext(file)
    files_name.append(name)

#忽略不符合要求的文件名
provinces_isps = [name for name in files_name if name.count('_') == 1]

# 打印结果
print(f"本次查询：{provinces_isps}的组播节目") 

urls_udp = "/status"

def is_url_accessible(url):
    try:
        response = requests.get(url, timeout=0.5)
        if response.status_code == 200:
            return url
    except requests.exceptions.RequestException:
        pass
    return None

def search_and_get_results(province, org):
    current_time = datetime.now()
    timeout_cnt = 0
    result_urls = set()
    results = []  # 新增：定义一个空列表用于保存结果
    
    # 最多尝试5次搜索
    while len(result_urls) == 0 and timeout_cnt <= 5:
        try:
            search_url = 'https://fofa.info/result?qbase64='
            search_txt = f'\"udpxy\" && country=\"CN\" && region=\"{province}\" && org=\"{org}\"'  # 修改：修正了字符串拼接错误
            bytes_string = search_txt.encode('utf-8')
            search_txt = base64.b64encode(bytes_string).decode('utf-8')
            search_url += search_txt
            print(f"{current_time} province: {province}, search_url: {search_url}")

            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')

            driver = webdriver.Chrome(options=chrome_options)
            driver.get(search_url)
            time.sleep(10)
            page_content = driver.page_source
            driver.quit()

            pattern = r"http://\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d+"
            urls_all = re.findall(pattern, page_content)
            result_urls = set(urls_all)
            print(f"{current_time} result_urls: {result_urls}")
            if org == "Chinanet":                
                isp = "电信"
            elif org == "China Unicom IP network China169 Guangdong province":                
                isp = "联通"
            elif org == "China Mobile communications corporation":                
                isp = "移动"
            elif org == "China Unicom Guangzhou network":                
                isp = "珠江"
            else:
                isp = ""
            for url in urls_all:
                ip_port = url.replace("http://", "")
                video_url = url + urls_udp
                if is_url_accessible(video_url):
                    result = url, isp, province
                    print(f"{current_time} 有效result: {result}")
                    results.append(result)  # 将结果保存到results列表中
                else:
                    print(f"{current_time} {video_url} 无效")
            return results
        except Exception as e:
            timeout_cnt += 1
            print(f"{current_time} [{province}]搜索请求发生异常：{e}")
    
    print(f"{current_time} 搜索IPTV频道源[{province}]，超时次数过多：{timeout_cnt}次，停止处理")
    return set()

valid_ips = []

# 测试搜索函数
for province in provinces_isps:
    province, isp = province.split('_')
    if isp == "电信":
        org = "Chinanet"
    elif isp == "联通":
        org = "China Unicom IP network China169 Guangdong province"
    elif isp == "移动":
        org = "China Mobile communications corporation"
    elif isp == "珠江":
        org = "China Unicom Guangzhou network"
    else:
        org = ""
    result = search_and_get_results(province, org)
    result = set(result)
    valid_ips.extend(result)  # 将结果添加到valid_ips中
    with open("res.txt", "w") as file:
        for ip in valid_ips:  # 修改：写入结果时应该遍历result而不是valid_ips
            ip_txt = f'{ip}\n'
            file.write(ip_txt)  # 修改：写入的应该是ip元组的第一个元素，即IP地址

print(f"可用IP为：{valid_ips}, 已保存至res.txt")
