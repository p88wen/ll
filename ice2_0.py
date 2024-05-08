import time
import concurrent.futures
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from datetime import datetime
import requests
import re
import os
import threading
from queue import Queue
import eventlet
eventlet.monkey_patch()
current_time = datetime.now()

def search_and_get_results(province, org):
    #current_time = datetime.now()
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
            return result_urls
        except Exception as e:
            timeout_cnt += 1
            print(f"{current_time} [{province}]搜索请求发生异常：{e}")
    
    print(f"{current_time} 搜索IPTV源[{province}]，超时次数过多：{timeout_cnt}次，停止处理")
    return []

# 获取rtp目录下的文件名
files = os.listdir('rtp')

# 去除后缀名并保存至provinces_isps
provinces_isps = [os.path.splitext(file)[0] for file in files if os.path.splitext(file)[0].count('_') == 1]

# 测试搜索函数
valid_ips = []

# 检查原res.txt中的链接有效性并加入valid_ips
with open("res2.txt", "r") as file:
    for line in file:
        parts = line.strip().split(',')
        url = parts[0]
        isp = parts[1]
        province = parts[2]
        with open("res2_bak.txt", "a") as file:
            file.write(line)
        valid_ips.append((url, isp, province))

channels = []

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
    channels.extend([(url, isp, province) for url in result])


# 定义后缀字典
suffix_dict = {
    "广东": {
        "电信": "/udp/102.3.1.25",
        "移动": "/udp/101.3.1.25",
        "联通": "/udp/100.3.1.25",
        "珠江": "/udp/103.3.1.25"
    }
}

# 线程安全的队列，用于存储下载任务
task_queue = Queue()

# 线程安全的列表，用于存储结果
results = []

error_channels = []

# 定义工作线程函数
def worker():
    while True:
        # 从队列中获取一个任务
        url, isp, province = task_queue.get()		
        try:
            channel_url = url+suffix_dict[province][isp]
            ts_lists_0 = 'temp.txt'

            # 多获取的视频数据进行5秒钟限制
            with eventlet.Timeout(5, False):
                start_time = time.time()
                content = requests.get(channel_url, timeout = 1).content
                end_time = time.time()
                response_time = (end_time - start_time) * 1

            if content:
                with open(ts_lists_0, 'ab') as f:
                    f.write(content)  # 写入文件
                file_size = len(content)
                # print(f"文件大小：{file_size} 字节")
                download_speed = file_size / response_time / 1024
                # print(f"下载速度：{download_speed:.3f} kB/s")
                normalized_speed = min(max(download_speed / 1024, 0.001), 100)  # 将速率从kB/s转换为MB/s并限制在1~100之间
                #print(f"标准化后的速率：{normalized_speed:.3f} MB/s")

                # 删除下载的文件
                os.remove(ts_lists_0)
                result = url, isp, f"{normalized_speed:.3f} MB/s", province
                results.append(result)
                numberx = (len(results) + len(error_channels)) / len(channels) * 100
                print(f"可用：{len(results)} 个 , 不可用：{len(error_channels)} 个 , 总：{len(channels)} 个 ,总进度：{numberx:.2f} %。")
        except:
            error_channel = url, isp
            error_channels.append(error_channel)
            numberx = (len(results) + len(error_channels)) / len(channels) * 100
            print(f"可用：{len(results)} 个 , 不可用：{len(error_channels)} 个 , 总：{len(channels)} 个 ,总进度：{numberx:.2f} %。")

        # 标记任务完成
        task_queue.task_done()

# 创建多个工作线程
num_threads = 10
for _ in range(num_threads):
    t = threading.Thread(target=worker, daemon=True)  # 将工作线程设置为守护线程
    t.start()

# 添加下载任务到队列
for channel in channels:
    task_queue.put(channel)

# 等待所有任务完成
task_queue.join()

# 对进行排序
results.sort(key=lambda x: (x[0], -float(x[2].split()[0])))

# 将有效的IP地址写入res.txt文件
with open("res2.txt", "w") as file:
    for ip_info in results:
        ip_txt = f"{ip_info[0]},{ip_info[1]},{ip_info[3]}\n"
        file.write(ip_txt)

print(f"可用IP为：{results}，已保存至res.txt")
