import sys, os
from datetime import datetime as dt, date, timedelta, time as _time
from typing import Pattern
from pybeans import AppTool
import json
import time
import random
import subprocess
import socket
from contextlib import closing
from rich.console import Console
console = Console()

import requests
requests.adapters.DEFAULT_RETRIES = 5
session = requests.session()
session.keep_alive = False


from jinja2 import Environment, FileSystemLoader

def my_finalize(thing):
    from numpy import float64
    if thing is None:
        return ''
    elif type(thing) in (float, float64):
        return round(thing, 2)
    else:
        #ut.D(f'##### {type(thing)}')
        return thing

tmp_env = Environment(loader=FileSystemLoader(os.getcwd() + '/templates'), finalize=my_finalize)


class Util(AppTool):
    """
    公用代码
    """
    def __init__(self, name):
        super(Util, self).__init__(name, os.getcwd())
        self._session = None


    def random(self):
        return random.Random().random()
    
    
    def sleep(self, sec=3):
        time.sleep(sec)
        
    
    def env(self, key:str='ENV', default=''):
        env = os.environ.get(key, default=default)
        self.D(f'>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> ENV = {env} <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<')
        return env
    
    
    def convert_date_str(self, date_str:str, from_format:str='%Y/%m/%d', to_format='%Y-%m-%d') -> str:
        a_date = dt.strptime(date_str,from_format).date()
        return dt.strftime(a_date,to_format)
    
        
    def find_free_port(self):
        with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
            s.bind(('', 0))
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            return s.getsockname()[1]
        

    def run(self, cmd, echo_cmd=False):
        try:
            if echo_cmd:
                print(cmd)
            result = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            result = e.output       # Output generated before error
            #code      = e.returncode   # Return code
        return str(result, encoding = "utf-8", errors='ignore')
    
    
    def request(self, url):
        resp = None
        ping = None

        try:
            resp = session.get(url, stream=True, timeout=10)
            fetch_time = int(resp.elapsed.microseconds/1000)

            #ping_time = ping(server_addr, unit='ms')
            if resp.status_code == 200:
                self.D(f'[√] {url}, fetch={fetch_time} ms.')
                ping = fetch_time
                # return (fetch_time + ping_time) / 2
            else:
                self.I(f'[×] {url}, status={resp.status_code}, timeout.')
        except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError) as ex:
            self.E(f'[×] {url}, {ex}')
            # logger.debug(ex)
        
        # sleep 乘以倍速，高倍速的测试次数少些
        sleep = random.random() * 3
        self.D(f'zZZ 睡眠{sleep}秒 ...')
        time.sleep(sleep)
        return ping

ut = Util('proxy-mon')


if __name__ == '__main__':
    from pybeans import utils as pu
    print(pu.timestamp())