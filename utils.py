import sys, os
from datetime import datetime as dt, date, timedelta, time as _time
from typing import Pattern
from pybeans import AppTool
import json
import time
import random
import io
import socket
from contextlib import closing

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from colorama import Fore, Back, init, Style


class Util(AppTool):
    """
    公用代码
    """
    def __init__(self):
        super(Util, self).__init__('proxy_mon', os.getcwd())
        self._session = None

    
    @property
    def conn(self):
        return 'mysql+mysqlconnector://{c[user]}:{c[pwd]}@{c[host]}:{c[port]}/{c[db]}?ssl_disabled=True' \
            .format(c=self['mysql'])
        
        
    @property
    def session(self):
        """
        Lazy loading
        """
        if self._session:
            return self._session
        
        assert(self['mysql'] is not None)
        engine = create_engine(
            self.conn, 
            pool_size=20, 
            max_overflow=0, 
            echo=self['log.sql'] == 1
        )
        from model import Base, Proxy, Delay
        Base.metadata.create_all(engine, checkfirst=True)
        self._session = sessionmaker(bind=engine)()
        return self._session
    
    
    def D(self, *args):
        self.print('DEBUG', *args)


    def I(self, *args):
        self.print('INFO', *args)


    def print(self, level, *args):
        local_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        if level == 'DEBUG':
            color = Fore.YELLOW
        elif level == 'INFO':
            color = Fore.GREEN
        elif level == 'ERROR':
            color = Fore.RED
        else:
            color = Fore.BLUE
        print(color, '{} [{}] - {} - '.format(local_time, self.name, level), *args)
        print(Style.RESET_ALL, flush=True)


    def random(self):
        return random.Random().random()
    
    
    def sleep(self, sec=3):
        time.sleep(sec)
        
    
    def timestamp(self):
        return time.time_ns()
    
    
    def env(self, key:str='ENV', default=''):
        env = os.environ.get(key, default=default)
        self.D(f'>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> ENV = {env} <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<')
        return env
    
    
    def convert_date_str(self, date_str:str, from_format:str='%Y/%m/%d', to_format='%Y-%m-%d') -> str:
        a_date = dt.strptime(date_str,from_format).date()
        return dt.strftime(a_date,to_format)
    
        
    def extract_str(self, reg:Pattern, content:str, default=None):
        """从字符串中提取文本信息

        Args:
            reg (Pattern): 编译后的正则对象
            content (str): 要提取内容的字符串
            default (str|None)
        """
        match = reg.search(content)
        if match:
            groups = match.groups()
            if groups:
                return groups[0].strip()
            else:
                return default
        else:
            return default
    
    
    def find_free_port(self):
        with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
            s.bind(('', 0))
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            return s.getsockname()[1]
        

ut = Util()