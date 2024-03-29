from datetime import datetime
from utils import ut
from pybeans import utils as pu
from openwrt import ShadowSocksR
from rank import df_from_json, history, report, rank, history

ssr = ShadowSocksR(ut['gateways.guest'])
    
def curl():
    result = []
    url = ut['website']
    filename = f'./data/{pu.timestamp()}.json'
    for id, alias in ssr.run():
        server = dict(
            id = id,
            alias = alias,
        )
        raw_curl = []
        for _ in range(ut['curl_count']):
            curl = ut.request(url)
            raw_curl.append(curl)
        server['raw'] = raw_curl
        result.append(server)
        pu.dump_json(filename, result)
    #ut.run(f'scp {filename} {ut["proxy_service_ssh"]}:/www/proxy-mon/data/')  # 复制到网站服务器
    return filename


def mon():
    try:
        start = datetime.now()
        id, alias = ssr.get_current_server()
        ut.I('Got current server', (id, alias))
        
        filename = curl()
        #filename='./data/20211015_133816.json'
        end = datetime.now()
        elapsed = (end - start).microseconds
        ut.I(f'Elapsed {elapsed / 1000 / 60} minutes during running curl()')
        df = df_from_json(filename)
        df_agg = rank(df)
        ut.D(df_agg)
        history(df_agg)
    
        ssr.set_server(id, alias)
        
        top_n = ut['top_n']
        report(df_agg.head(top_n))
        #ssr.set_server(df_agg.at[0, 'id'], df_agg.at[0, 'alias'])
    except Exception:
        ut.ex('测试代理节点出错')

if __name__ == '__main__':
    mon()