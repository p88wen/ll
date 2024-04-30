import requests
import base64
import re
import os
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

def is_url_accessible(url):
    try:
        response = requests.get(url, timeout=0.5)
        if response.status_code == 200:
            return True
    except requests.exceptions.RequestException:
        pass
    return False

def search_and_get_results(province, org):
    current_time = datetime.now()
    timeout_cnt = 0
    result_urls = set()

    while len(result_urls) == 0 and timeout_cnt <= 5:
        try:
            search_url = f"https://fofa.info/result?qbase64={base64.b64encode(f'\"udpxy\" && country=\"CN\" && region=\"{province}\" && org=\"{org}\"'.encode('utf-8')).decode('utf-8')}"
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
            results = [url + "/status" for url in result_urls if is_url_accessible(url + "/status")]
            print(f"{current_time} 有效result: {results}")
            return results
        except Exception as e:
            timeout_cnt += 1
            print(f"{current_time} [{province}]搜索请求发生异常：{e}")
    
    print(f"{current_time} 搜索IPTV频道源[{province}]，超时次数过多：{timeout_cnt}次，停止处理")
    return []

# 获取rtp目录下的文件名
files = os.listdir('rtp')

# 去除后缀名并保存至provinces_isps
provinces_isps = [os.path.splitext(file)[0] for file in files if os.path.splitext(file)[0].count('_') == 1]

# 测试搜索函数
valid_ips = []

# 检查原res.txt中的链接有效性并加入valid_ips
with open("res.txt", "r") as file:
    for line in file:
        parts = line.strip().split(',')
        url = parts[0]
        isp = parts[1]
        province = parts[2]
        if is_url_accessible(url):
            valid_ips.append((url, isp, province))

for province in provinces_isps:
    province, isp = province.split('_')
    org_map = {
        "电信": "Chinanet",
        "联通": "China Unicom IP network China169 Guangdong province",
        "移动": "China Mobile communications corporation",
        "珠江": "China Unicom Guangzhou network"
    }
    org = org_map.get(isp, "")
    result = search_and_get_results(province, org)
    valid_ips.extend([(url, isp, province) for url in result])

# 按isp排序
valid_ips.sort(key=lambda x: x[1])

# 将有效的IP地址写入res.txt文件
with open("res.txt", "a") as file:
    for ip_info in valid_ips:
        ip_txt = f"{ip_info[0]},{ip_info[1]},{ip_info[2]}\n"
        file.write(ip_txt)

print(f"可用IP为：{valid_ips}，已保存至res.txt")
