import enum
from utils import ut
import re

REG_SSR_SERVER = re.compile(r'\[\d+\] shadowsocksr\.(\w+)\.alias=\'(.+)\'')

class ShadowSocksR(object):
    def __init__(self, gateway:str) -> None:
        super().__init__()
        self.gateway = gateway
        self.servers = []
        
    
    def get_servers(self):
        if not self.servers:
            ut.run(f'scp ./bin/shadowsocksr.sh root@{self.gateway}:/tmp/shadowsocksr.sh')
            result = ut.run(f'ssh root@{self.gateway} "chmod +x /tmp/shadowsocksr.sh && /tmp/shadowsocksr.sh"')
            self.servers = REG_SSR_SERVER.findall(result)
            
    
    def run(self):
        self.get_servers()
        for i, server in enumerate(self.servers):
            id, alias = server
            ut.I(f'Switching to [{i+1}] {alias} ...')
            result = ut.run(f'ssh root@{self.gateway} "uci set shadowsocksr.@global[0].global_server=\'{id}\' && uci commit shadowsocksr && /etc/init.d/shadowsocksr restart"')
            print(result)
            print(f'Sleeping 3 seconds ...')
            ut.sleep(3)
            yield (id, alias)
            
    
    def set_server(self, id:str, alias:str=None):
        print(f'Switching to {alias} ...')
        result = ut.run(f'ssh root@{self.gateway} "uci set shadowsocksr.@global[0].global_server=\'{id}\' && uci commit shadowsocksr && /etc/init.d/shadowsocksr restart"')
        print(result)
            


if __name__ == '__main__':
    ssr = ShadowSocksR(ut['gateway'])
    ssr.get_servers()
    print(ssr.servers)