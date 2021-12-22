from openwrt import ShadowSocksR
from rich.table import Table
from rich.console import Console
console = Console()

SS_GATEWAY = '10.8.9.1'
SSR = ShadowSocksR(SS_GATEWAY)
SSR.get_servers()

def show_servers():
    current_server = SSR.get_current_server()
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("No", style='bold underline yellow')
    table.add_column("Act")
    table.add_column("Name")
    table.add_column("ID")
    for index, server in enumerate(SSR.servers):
        id, alias = server
        table.add_row(f'{index+1}', '*' if id == current_server[0] else '', alias, id)
    console.print(table)


def input_param():    
    tips = '# Input NO (q: quit): '
    return input(tips)
        

def start():
    show_servers()
    while True:
        param = input_param()
        if param == 'q':
            break
        elif len(param) <= 2 and param.isdigit() and 1 <= int(param) <= len(SSR.servers):
            id, alias = SSR.servers[int(param)-1]
            console.print(f'[cyan]Switching to {alias}[/cyan]')
            SSR.set_server(id, alias)
            show_servers()
        

if __name__ == '__main__':
    start()