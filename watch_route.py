import subprocess
import re, os
import time, random
import requests
from colorama import Fore, Back, init, Style
# conda install pywin32
#from win10toast import ToastNotifier
#Toast Notifier 在WIN10下经常不工作
#toaster = ToastNotifier()
from rich.console import Console
console = Console()

from pybeans import utils as ut

TITLE = 'CHANGE ROUTE'
os.system(f'title {TITLE}')
init()

###################################### Interface Definition ######################################
REAL_IP = '10.20.193.67'
REAL_GW = '10.20.0.254'
REAL_IF = 'Realtek USB GbE Family Controller #3'
REAL_IF_NUM = 0
REAL_IF_ALIAS = '物理网关'

#PROXY_IP = '192.168.33.18'
#PROXY_GW = '192.168.33.254'
#PROXY_IF = 'VirtualBox Host-Only Ethernet Adapter #8'
#PROXY_IF_NUM = 0
#PROXY_IF_ALIAS = '代理网关'

PROXY_IP = '192.168.10.18'
PROXY_GW = '192.168.10.1'
PROXY_IF = 'ASIX AX88179 USB 3.0 to Gigabit Ethernet Adapter'
PROXY_IF_NUM = 0
PROXY_IF_ALIAS = '代理网关'

REG_IF = re.compile(r'\s*(\d+)\.+(?:\w\w\s){6}\.+(.+)')
REG_SNF = re.compile(rf'0.0.0.0\s+0.0.0.0\s+{REAL_GW}\s+{REAL_IP}\s+(\d+)')
REG_OWR = re.compile(rf'0.0.0.0\s+0.0.0.0\s+{PROXY_GW}\s+{PROXY_IP}\s+(\d+)')
REG_OWR_NO_IP = re.compile(rf'0.0.0.0\s+0.0.0.0\s+{PROXY_GW}\s+169\.254\.\d{1,3}\.\d{1,3}\s+(\d+)')

ROUTE_BAT_FILE = r'c:\temp\change_route.bat'
###################################### Interface Definition ######################################

MAX_CURL_TIME = 0
MIN_CURL_TIME = 9999999

BAIDU_TIMEOUT_CNT = 0
GOOGLE_TIMEOUT_CNT = 0

VBOX_PATH = r'C:\Program Files\Oracle\VirtualBox\VBoxManage.exe'
ROUTER_VM_NAME = 'router'

REG_SSR_LIST = re.compile(r'\[\d+\] shadowsocksr\.(\w+)\.alias=\'(.+)\'')
REG_SSR_CURRENT = re.compile(r'shadowsocksr\.\w+\.global_server=\'(.+)\'')
SS_GATEWAY = '10.8.9.1'
SS_SERVERS = []


def run(cmd, echo_cmd=False):
    try:
        if echo_cmd:
            print(cmd)
        result = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        result = e.output       # Output generated before error
        #code      = e.returncode   # Return code
    return str(result, encoding = "utf-8", errors='ignore')


def get_metrics(route_table: str, gw: str, ip: str):
    reg_metric = re.compile(r'0.0.0.0\s+0.0.0.0\s+{}\s+{}\s+(\d+)'.format(gw, ip))
    results = reg_metric.findall(route_table)
    if not results:
        return -1
    return int(results[0])


def get_if_map(route_table: str):
    results = REG_IF.findall(route_table)
    return { n[-1].rstrip('\r'):n[0] for n in results}


def _request_page(website):
    resp = None

    try:
        resp = requests.get(website, stream=True, timeout=10)
        fetch_time = int(resp.elapsed.microseconds/1000)

        #ping_time = ping(server_addr, unit='ms')
        if resp.status_code in (200, 403):
            #print(f'{website}, status={resp.status_code}, fetch={fetch_time} ms.')
            return fetch_time
            # return (fetch_time + ping_time) / 2
        else:
            #print(f'{website}, status={resp.status_code}, timeout.')
            return None
    except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError) as ex:
        #print(f'Failed to access {website}')
        # logger.debug(ex)
        return None


def change_route():
    del_real_route_cmd = f'route delete 0.0.0.0 IF {REAL_IF_NUM}'
    del_proxy_route_cmd = f'route delete 0.0.0.0 IF {PROXY_IF_NUM}'
    dc1_route_cmd = f'route add 10.0.0.0 MASK 255.255.0.0 {REAL_GW} METRIC 1 IF {REAL_IF_NUM}'  # 服务器
    dc2_route_cmd = f'route add 10.21.0.0 MASK 255.255.0.0 {REAL_GW} METRIC 1 IF {REAL_IF_NUM}' # 如东
    real_route_cmd = f'route add 0.0.0.0 MASK 0.0.0.0 {REAL_GW} METRIC 9999 IF {REAL_IF_NUM}'
    proxy_route_cmd = f'route add 0.0.0.0 MASK 0.0.0.0 {PROXY_GW} METRIC 1000 IF {PROXY_IF_NUM}'
    print(Fore.GREEN, '=================网口信息===================', Style.RESET_ALL)
    print(f'物理网口序号：{REAL_IF_NUM}，IP：{REAL_IP:14}，网关：{REAL_GW:14}，名称：{REAL_IF}')
    print(f'代理网口序号：{PROXY_IF_NUM}，IP：{PROXY_IP:14}，网关：{PROXY_GW:14}，名称：{PROXY_IF}')
    print(Fore.YELLOW, '=================路由命令===================', Style.RESET_ALL)
    #run(del_real_route_cmd, True)
    #run(del_proxy_route_cmd, True)
    #run(dc1_route_cmd, True)
    #run(dc2_route_cmd, True)
    #run(real_route_cmd, True)
    #run(proxy_route_cmd, True)
    
    print(f'将路由命令写入 {ROUTE_BAT_FILE}')
    with open(ROUTE_BAT_FILE, 'w') as fp:
        fp.write(f'{del_real_route_cmd} \n{del_proxy_route_cmd} \n{dc1_route_cmd} \n{dc2_route_cmd} \n{real_route_cmd} \n{proxy_route_cmd}')
    print(f'执行 {ROUTE_BAT_FILE} 中的路由命令')
    os.system(f'PowerShell -Command "Start-Process cmd.exe -ArgumentList \'/s,/c, {ROUTE_BAT_FILE}\' -Verb RunAs"')
    time.sleep(3)
    #os.system(f'runas /savecred /user:henrytian@snfchina "{del_real_route_cmd}"')
    #os.system(f'runas /savecred /user:henrytian@snfchina "{del_proxy_route_cmd}"')
    #os.system(f'runas /savecred /user:henrytian@snfchina "{dc1_route_cmd}"')
    #os.system(f'runas /savecred /user:henrytian@snfchina "{dc2_route_cmd}"')
    #os.system(f'runas /savecred /user:henrytian@snfchina "{real_route_cmd}"')
    #os.system(f'runas /savecred /user:henrytian@snfchina "{proxy_route_cmd}"')
    

def is_router_running():
    runningVMs = run([VBOX_PATH, 'list', 'runningvms'])
    print(runningVMs)
    if f'"{ROUTER_VM_NAME}"' in runningVMs:
        return True
    return False


def wait_for_router_down():
    running = is_router_running()
    while running:
        print(f'"{ROUTER_VM_NAME}" is running, sleep 3 seconds ...')
        time.sleep(3)
        running = is_router_running()
        
        
def wait_for_router_up():
    running = is_router_running()
    while not running:
        print(f'"{ROUTER_VM_NAME}" is down, sleep 3 seconds ...')
        time.sleep(3)
        running = is_router_running()
    

def start_router(close_router_first:bool=False):
    if close_router_first:
      print(f'ACPI power off "{ROUTER_VM_NAME}" ...')
      run([VBOX_PATH, 'controlvm', ROUTER_VM_NAME, 'acpipowerbutton'])
    wait_for_router_down()
    seconds = 15
    print(f'Power on "{ROUTER_VM_NAME}", please wait for {seconds} seconds ...')
    run([VBOX_PATH, 'startvm', ROUTER_VM_NAME])
    wait_for_router_up()
    time.sleep(seconds)
    
    curl_gw_time = _request_page(f'http://{PROXY_GW}')
    while curl_gw_time is None:
        print('No responding from router webpage.')
        time.sleep(3)
        curl_gw_time = _request_page(f'http://{PROXY_GW}')
    

def toast(title, msg, duration):
    #Toast Notifier 在WIN10下经常不工作
    return
    try:
      toaster.show_toast(
        title, 
        msg, 
        icon_path=None, # 'icon_path' 
        duration=duration, # for how many seconds toast should be visible; None = leave notification in Notification Center
        threaded=True # True = run other code in parallel; False = code execution will wait till notification disappears 
      )
    except Exception as ex:
      print(f'无法弹出气泡通知：{ex}')
      pass


def get_servers():
    global SS_SERVERS
    ut.run(f'scp C:/projects/python/proxy-mon/bin/shadowsocksr.sh root@{SS_GATEWAY}:/tmp/shadowsocksr.sh')
    result = ut.run(f'ssh root@{SS_GATEWAY} "chmod +x /tmp/shadowsocksr.sh && /tmp/shadowsocksr.sh"')
    SS_SERVERS = REG_SSR_LIST.findall(result)
    console.print(SS_SERVERS)


def get_current_server():
    result = ut.run(f'ssh root@{SS_GATEWAY} "uci show shadowsocksr.@global[0].global_server"')
    ss_current = REG_SSR_CURRENT.findall(result)[0]
    for server in SS_SERVERS:
        id, alias = server
        if id == ss_current:
            return alias


def start():
    global BAIDU_TIMEOUT_CNT, GOOGLE_TIMEOUT_CNT, REAL_IF_NUM, PROXY_IF_NUM, MAX_CURL_TIME, MIN_CURL_TIME
    if not is_router_running():
      print('VM router is not running')
      #start_router()
    else:
      print('VM router is running')
    ipconfig = run('ipconfig')
    real_ip_pos = ipconfig.find(REAL_IP)
    real_gw_pos = ipconfig.find(REAL_GW)

    sleep_sec = 5
    print(f'当前节点：{get_current_server()}')
    while real_ip_pos >= 0 and real_gw_pos >= 0:
        route_table = run('route print')
        if_map = get_if_map(route_table)
        REAL_IF_NUM = if_map[REAL_IF]
        PROXY_IF_NUM = if_map[PROXY_IF]
        
        metric_snf = get_metrics(route_table, REAL_GW, REAL_IP)
        metric_pxy = get_metrics(route_table, PROXY_GW, PROXY_IP)
            
        if metric_pxy < 0:
            metric_pxy = get_metrics(route_table, PROXY_GW, r'169\.254\.\d{2,3}\.\d{2,3}')
            if metric_pxy > 0:
                msg = f'{PROXY_IF}未能正确获取IP，需要重启网卡'
                print(Fore.RED, f'\n>>> {msg} <<<', Style.RESET_ALL, flush=True)
                run(f'netsh interface set interface name="{PROXY_IF}" admin=DISABLED', True)
                run(f'netsh interface set interface name="{PROXY_IF}" admin=ENABLED', True)
            else:
                msg = f'[{PROXY_IF_ALIAS}] 已下线！'
                print(Fore.RED, f'\n>>> {msg} <<<', Style.RESET_ALL, flush=True)
                change_route()
                toast('Route', msg, duration=15)
        elif metric_snf > 0 and metric_pxy >= metric_snf:
            print(f'\n>>> [{PROXY_IF_ALIAS}] metric={metric_pxy}，[{REAL_IF_ALIAS}] metric={metric_snf}', flush=True)
            msg = f'[{PROXY_IF_ALIAS}] 的优先级低于 [{REAL_IF_ALIAS}]，需要调整'
            print(Fore.YELLOW, f'\n>>> {msg}', Style.RESET_ALL, flush=True)
            change_route()
            toast('Route', msg, duration=5)
        else:
            curl_google_time = _request_page('https://www.google.com')
            if curl_google_time is None:
                GOOGLE_TIMEOUT_CNT += 1
                print(Fore.YELLOW, f'【谷歌】超时 {GOOGLE_TIMEOUT_CNT} 次', Style.RESET_ALL, flush=True)
                toast('Route', f'!!! 【谷歌】超时{GOOGLE_TIMEOUT_CNT}次', duration=5)
                sleep_sec = 5
                if GOOGLE_TIMEOUT_CNT >= 8:
                  print(f'【谷歌】超时已达{GOOGLE_TIMEOUT_CNT}次，开始测试【百度】......')                  
                  curl_baidu_time = _request_page('http://www.baidu.com')
                  if curl_baidu_time is None:
                      BAIDU_TIMEOUT_CNT += 1
                      print(Fore.RED, f'【百度】超时 {BAIDU_TIMEOUT_CNT} 次', Style.RESET_ALL, flush=True)
                      toast('Route', f'!!! 【百度】超时{BAIDU_TIMEOUT_CNT}次', duration=5)
                      if BAIDU_TIMEOUT_CNT >= 8:
                        print(f'【百度】超时已达{BAIDU_TIMEOUT_CNT}次，开始重启【openwrt】......')
                        #start_router(True)
                        BAIDU_TIMEOUT_CNT = 0
                  else:
                      print(Fore.RED, f'【百度】可连接，延迟{curl_baidu_time}', Style.RESET_ALL, flush=True)
                      BAIDU_TIMEOUT_CNT = 0
                print(f'当前节点：{get_current_server()}')
            else:
                GOOGLE_TIMEOUT_CNT = 0
                BAIDU_TIMEOUT_CNT = 0
                times = '-' * round(curl_google_time/10) + str(curl_google_time)
                if curl_google_time > MAX_CURL_TIME:
                    print(f'{Fore.YELLOW}{times}', Style.RESET_ALL, flush=True)
                    toast('Route', f'+++ MAX：{curl_google_time}', duration=3)
                    MAX_CURL_TIME = curl_google_time
                elif curl_google_time < MIN_CURL_TIME:
                    print(f'{Fore.GREEN}{times}', Style.RESET_ALL, flush=True)
                    toast('Route', f'--- MIN：{curl_google_time}', duration=3)
                    MIN_CURL_TIME = curl_google_time
                else:
                    print(times, flush=True)
                sleep_sec = 10

        time.sleep(sleep_sec)
    

if __name__ == '__main__':
    #start_router()
    get_servers()
    try:
      start()
    except Exception as ex:
      bar = '*' * 60
      print(f'!!! Fatal error: {ex}.\n{bar}')
      console.print_exception()
      print(f'{bar}\nPress any key to exit...')
      run('pause')