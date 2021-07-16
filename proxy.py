from os import path
import requests
import base64
import json
from urllib import parse
from queue import Queue
q = Queue(60)

from utils import ut

from model import Proxy, Delay

headers = {'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:23.0) Gecko/20100101 Firefox/23.0'}

def padding_base64(data):
    missing_padding = len(data) % 4
    if missing_padding != 0:
        data += '='* (4 - missing_padding)
    return data


def parse_ss(url:str):
    """解析ss协议

    Args:
        url (str): ss分享url，不含ss://，#之后为remark
    """
    parts = url.split('#')
    config = base64.urlsafe_b64decode(padding_base64(parts[0]))
    config = config.decode('utf-8')
    method, pwd_ip, port = config.split(':')
    pwd, ip = pwd_ip.split('@')
    return dict(
        type='ss',
        method=method,
        pwd=pwd,
        addr=ip,
        port=port,
        local_port=ut.find_free_port(),
        remark=parse.unquote_plus(parts[1])
    )


def parse_vmess(url:str):
    url= str.encode(url)
    url = base64.urlsafe_b64decode(url)
    config = json.loads(bytes.decode(url))
    config['type'] = 'vmess'
    return config


def subscribe(url):
    req = requests.get(url=url, headers=headers)
    return_content = req.content

    ## 解析订阅地址内容
    result = base64.decodestring(return_content)
    share_links=result.splitlines()
    ## 解析vmess协议
    schemes_allow = ['vmess', 'ss', 'ssr']
    servers = []
    for share_link in share_links:
        share_link = bytes.decode(share_link)
        #ut.D(share_link)
        url = share_link.split("://")
        ## 解析协议
        scheme = url[0]
        #ut.D('协议：',scheme)
        if scheme not in schemes_allow:
            raise ValueError(f'不支持的协议：{scheme}')
        ## 解析内容
        if scheme == 'ss':
            server = parse_ss(url[1])
        elif scheme == 'vmess':
            server = parse_vmess(url[1])
        #ut.D(server)
        servers.append(server)
    #ut.D(configs)
    return servers


def create_config(config_dir:str, servers):
    data = {}
    
    server_data = {}
    for server in servers:
        addr = server['add'] if server['type'] == 'vmess' else server['addr']
        proxy = ut.session.query(Proxy).filter_by(
            type = server['type'],
            addr = addr,
            port = server['port']
        ).one_or_none()
        
        if proxy is None:
            ut.D('数据库中未找到"{}"'.format(server['remark']))
            proxy = Proxy()
            proxy.type = server['type']
            proxy.addr = addr
            proxy.port = server['port']
            proxy.remark = server['remark']
            ut.session.add(proxy)
            ut.session.commit()
        else:
            ut.D('"{}"已经在数据库中,ID={}'.format(server['remark'], proxy.id))
            
        if server['type'] == 'vmess':
            with open(f'{server["type"]}_v{server["v"]}.json', 'r', encoding='utf8') as fp:
                data = json.load(fp)
            if not data:
                continue
            config = data.copy()
            config['inbound']['port'] = ut.find_free_port()
            
            vnext = config['outbound']['settings']['vnext'][0]
            vnext['address'] = server['add']
            vnext['port'] = server['port']
            vnext['users'][0]['id'] = server['id']
            vnext['users'][0]['alterId'] = server['aid']
            
            stream = config['outbound']['streamSettings']
            stream['network'] = server['net']
            stream['wsSettings']['path'] = server['path']
            stream['wsSettings']['security'] = server['tls']
        
            config_path = f"{config_dir}/{server['add']}_{server['port']}.json"
            with open(config_path, 'w', encoding='utf8') as fd:
                json.dump(config, fd, indent=2, ensure_ascii=False)
            server_data[f"{server['add']}:{server['port']}"] = dict(
                type=server['type'],
                path=config_path,
                addr=server['add'],
                port=server['port'],
                local_port=config['inbound']['port'],
                remark=server['remark'],
                proxy_id=proxy.id,
                q=q
            )
        elif server['type'] == 'ss':
            server_data[f"{server['addr']}:{server['port']}"] = {**server, **{'proxy_id': proxy.id, 'q': q}}
    return server_data