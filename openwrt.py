import enum
from utils import ut
import re

REG_SSR_SERVER = re.compile(r'\[\d+\] shadowsocksr\.(\w+)\.alias=\'(.+)\'')
REG_SSR_CURRENT = re.compile(r'shadowsocksr\.\w+\.global_server=\'(.+)\'')
REG_SSR_LIST = re.compile(r'\[\d+\] shadowsocksr\.(\w+)\.alias=\'(.+)\'')

class ShadowSocksR(object):
    def __init__(self, gateway:str) -> None:
        super().__init__()
        self.gateway = gateway
        self.servers = []
        
    
    def get_servers(self):
        if not self.servers:
            ut.I('Copying shadowsocksr.sh to openwrt ...')
            result = ut.run(f'scp ./bin/shadowsocksr.sh root@{self.gateway}:/tmp/shadowsocksr.sh')
            if 'Connection timed out' in result:
                #raise RuntimeError(f'Failed to copy shadowsocksr.sh. Message: {result}')
                return []
            ut.I('Output: ', result)
            ut.I('Running shadowsocksr.sh ...')
            result = ut.run(f'ssh root@{self.gateway} "chmod +x /tmp/shadowsocksr.sh && /tmp/shadowsocksr.sh"')
            if 'Connection timed out' in result:
                #raise RuntimeError(f'Failed to run shadowsocksr.sh. Message: {result}')
                return []
            ut.I('Output: ', result)
            self.servers = REG_SSR_SERVER.findall(result)
            ut.I('Got servers', self.servers)
            
    
    def get_current_server(self):
        self.get_servers()
        if len(self.servers) == 0:
            ut.error('Cannot get servers from openwrt.')
        result = ut.run(f'ssh root@{self.gateway} "uci show shadowsocksr.@global[0].global_server"')
        if 'Connection timed out' in result:
            #raise RuntimeError(f'Failed to get current server. Message: {result}')
            return None

        ss_current = REG_SSR_CURRENT.findall(result)[0]
        for server in self.servers:
            id, alias = server
            if id == ss_current:
                self.id = id
                self.alias = alias
                return server
    
    
    def run(self):
        self.get_servers()
        if len(self.servers) == 0:
            ut.error('Cannot get servers from openwrt.')
        for i, server in enumerate(self.servers):
            id, alias = server
            ut.I(f'Switching to [{i+1}] {alias} ...')
            result = self.set_server(id, alias)
            print(result)
            print(f'Sleeping 3 seconds ...')
            ut.sleep(3)
            yield (id, alias)
            
    
    def set_server(self, id:str, alias:str=None):
        result = ut.run(f'ssh root@{self.gateway} "uci set shadowsocksr.@global[0].global_server=\'{id}\' && uci commit shadowsocksr && /etc/init.d/shadowsocksr restart"')
        if 'Connection timed out' in result:
            raise RuntimeError(f'Failed to set current server. Message: {result}')
        return result


if __name__ == '__main__':
    ssr = ShadowSocksR(ut['gateway'])
    ssr.get_servers()
    print(ssr.servers)