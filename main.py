from importlib import import_module
import subprocess
import requests
import time, random
from queue import Queue
from multiprocessing import Pool as ProcessPool
from multiprocessing.dummy import Pool as ThreadPool

from utils import ut
from model import Delay
from proxy import q, subscribe, create_config
import proxy_filter


def get_proxy(local_port):
    return {
        'https': f'socks5h://127.0.0.1:{local_port}', # 使用socks5h而不是socks5，可在proxy端dns解析
        'http': f'socks5h://127.0.0.1:{local_port}'
    }
    
    
def start_ss(server):
    args = ['ss-local', '-s', server['addr'], '-p', str(server['port']), '-k', server['pwd'], \
        '-m', server['method'], '-l', str(server['local_port'])]
    # logger.info(' '.join(args))
    proc = subprocess.Popen(args)
    ut.D(f'启动ss [{server["local_port"]}]：{server["remark"]}')
    return proc


def start_v2ray(server):
    args = ['v2ray', '-c', server['path']]
    # logger.info(' '.join(args))
    proc = subprocess.Popen(args)
    ut.D(f'启动v2ray [{server["local_port"]}]：{server["remark"]}')
    return proc


def _request_page(server, local_port):
    resp = None
    ping = None
    website = ut['website']

    proxy = get_proxy(local_port)
    try:
        resp = requests.get(website, stream=True, proxies=proxy, timeout=10)
        fetch_time = int(resp.elapsed.microseconds/1000)

        #ping_time = ping(server_addr, unit='ms')
        if resp.status_code == 200:
            ut.D(f'[√] {server["type"]} {local_port} {server["remark"]} => {website}, fetch={fetch_time} ms.')
            ping = fetch_time
            # return (fetch_time + ping_time) / 2
        else:
            ut.D(f'[×] {server["type"]} {local_port} {server["remark"]} ≠> {website}, status={resp.status_code}, timeout.')
    except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError) as ex:
        ut.D(f'[×] {server["type"]} {local_port} {server["remark"]} ≠> {website}, {ex}')
        # logger.debug(ex)
    
    q = server['q']
    q.put((server['proxy_id'], ping))
    
    # sleep 乘以倍速，高倍速的测试次数少些
    sleep = (300 + random.random()*10) * server['multi']
    ut.D(f'zZZ 睡眠{sleep}秒 ...')
    time.sleep(sleep)
    return ping
    
    
def start_client(server):
    #ut.D(server['type'])
    if server['type'] == 'ss':
        proc = start_ss(server)
    elif server['type'] == 'vmess':
        proc = start_v2ray(server)
    time.sleep(1)   # 避免来不及切换proxy而无法请求
    return proc
    
    
def _test_and_kill(server):
    proc = start_client(server)
    try:
        delay = _request_page(server, server['local_port'])
        return delay
    finally:
        proc.kill()
        
        
def _test_forever(server):
    start_client(server)
    while True:
        _request_page(server, server['local_port'])
        
        
def benchmark():
    for proxy_type in ut['proxy']:
        proxy_config = ut['proxy'][proxy_type]
        if 'subscribe' in proxy_config:
            servers = subscribe(proxy_config['subscribe'])
            #ut.D(servers)
            configs = create_config(proxy_config['config_dir'], servers)
            #ut.D(configs)
            filter = getattr(proxy_filter, proxy_config['vendor'])
            ut.D('订阅找到{}个服务节点'.format(len(configs)))
            configs = filter(configs)
            ut.D('过滤后剩下{}个服务节点'.format(len(configs)))
            if ut['max_client'] == 0: #无限客户端，因此无需退出客户端
                pool = ThreadPool(len(configs))
                server_info = pool.map_async(_test_forever, configs.values())
                pool.close()
            else:
                pool = ThreadPool(ut['max_client'])
                server_info = pool.map_async(_test_and_kill, configs.values())
                pool.close()
    
    while True:
        proxy_id, ping = q.get()
        ut.D(f'代理ID={proxy_id}, 延迟={ping}')
        delay = Delay()
        delay.proxy_id = proxy_id
        delay.value = ping
        ut.session.add(delay)
        ut.session.commit()


if __name__ == '__main__':
    benchmark()
