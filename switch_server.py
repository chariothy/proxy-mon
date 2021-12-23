from openwrt import ShadowSocksR
from rich.table import Table
from rich.console import Console
console = Console()
from utils import ut

gateways = ut['gateways']
SSR = None
ADMIN = 'admin'
GW_USING = {}

for gw in gateways:
    ip = gateways[gw]
    console.print(f'Finding servers in gateway: {gw}', end=',\t ')
    ssr = ShadowSocksR(ip)
    if gw == ADMIN: SSR = ssr
    svr_id, svr_alias = ssr.get_current_server()
    if svr_alias not in GW_USING:
        GW_USING[svr_alias] = []
    GW_USING[svr_alias].append(gw)
    console.print(f'Found server: {svr_alias}')    


def show_servers(first_time=False):
    global GW_USING
    if first_time:
        cur_svr_id = SSR.id
    else:
        cur_svr_id, cur_svr_alias = SSR.get_current_server()
        for svr_alias in GW_USING:
            gws = GW_USING[svr_alias]
            if ADMIN in gws:
                gws.remove(ADMIN)
        GW_USING[cur_svr_alias].append(ADMIN)
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("")
    table.add_column("No", style='bold underline yellow')
    table.add_column("Name")
    table.add_column("Used At")
    for index, server in enumerate(SSR.servers):
        id, alias = server
        table.add_row('*' if id == cur_svr_id else ''
                      , f'{index+1}'
                      , alias
                      , ', '.join(GW_USING.get(alias, [])))
    console.print(table)


def input_param():    
    tips = '# Input No of server (q: quit): '
    return input(tips)
        

def start():
    show_servers(True)
    while True:
        param = input_param()
        if param == 'q':
            break
        elif len(param) <= 2 and param.isdigit() and 1 <= int(param) <= len(SSR.servers):
            # TODO: 与当前不同时才切换
            id, alias = SSR.servers[int(param)-1]
            console.print(f'[cyan]Switching to {alias}[/cyan]')
            SSR.set_server(id, alias)
            show_servers()
        

if __name__ == '__main__':
    start()