from utils import ut
from model import Proxy, Delay, Rank, query_delay, query_proxy, query_rank
from matplotlib import get_backend
import matplotlib.pyplot as plt
import matplotlib.dates as md
import seaborn as sns
from pybeans import alignment
import pandas as pd


def display():
    id_proxy = {}

    proxies = query_proxy(ut.session).all()

    for i, p in enumerate(proxies):
        id_proxy[p.id] = p
        print(f'ID {p.id}'.ljust(6), f'RK {p.rank}'.ljust(6), '|', alignment(p.remark, 30), '||', end=' ')
        if (i+1) % 5 == 0:
            print()

    print()
    input_correct = False
    while not input_correct:
        proxy_ids = input('>>> 输入要显示的代理id，以逗号分隔：')
        proxy_id_list = proxy_ids.split(',')
        accepted_ids = []
        input_correct = True
        for proxy_id in proxy_id_list:
            if not proxy_id.isdigit():
                print(f'>>> 不能接受{proxy_id}, 只能输入数字')
                input_correct = False
                break
            try:
                proxy_id_int = int(proxy_id)
            except Exception:
                print(f'>>> 不能接受{proxy_id}, 只能输入数字')
                input_correct = False
                break
            if proxy_id_int not in id_proxy:
                print(f'>>> {proxy_id}不是正确的代理ID')
                input_correct = False
                break
            accepted_ids.append(proxy_id_int)
            
    print('>>> 选中代理：', ', '.join([id_proxy[id].remark for id in accepted_ids]))

    for proxy_id in accepted_ids:
        q = query_delay(ut.session, proxy_id)
        df = pd.read_sql(q.statement, q.session.bind, parse_dates=["when"])
        df.describe()
        #print(df)
        #print(df.shape)
        
        p01 = df.value.quantile(0.01)
        p99 = df.value.quantile(0.99)
        vdf = df[(df.value >= p01) & (df.value <= p99)]
        remark = id_proxy[proxy_id].remark

        plt.figure(figsize = (20,10))
        ax1 = plt.subplot2grid(shape=(2,2), loc=(0,0), colspan=2)
        ax1.set_title(remark)
        ax1.set_xlabel('日期时间')
        ax1.set_ylabel('CURL延迟')
        ax1.scatter(vdf.when, vdf.value, alpha=0.5, label=remark)
        plt.grid() 

        ax2 = plt.subplot2grid(shape=(2,2), loc=(1,0))
        plt.grid()      # 添加网格
        ax2.set_title('直方图')
        sns.distplot(vdf.value, bins=30, ax=ax2)

        ax3 = plt.subplot2grid(shape=(2,2), loc=(1,1))
        plt.grid()      # 添加网格
        
        txt = f'''
最小值 = {vdf.value.min()}, 最大值 = {vdf.value.max()}, 平均值 = {round(vdf.value.mean(),2)}, 中位数 = {round(vdf.value.median(),2)} \n
数据量 = {df.value.count()}, 有效数据量 = {vdf.value.count()}, 有效数据占比 = {round(100 * vdf.value.count() / df.value.count(),2)}%\n
超时数据量 = {df[df.value.isnull()].proxy_id.count() }, 超时数据占比 = {round(100 * df[df.value.isnull()].proxy_id.count() / df.count().value,2)}%\n
标准差 = {round(vdf.value.std(),2)}, 平均绝对偏差 = {round(vdf.value.mad(),2)}\n
偏度 = {round(vdf.value.skew(),2)}, 峰度 = {round(vdf.value.kurt(),2)}, 最近排名 = {id_proxy[proxy_id].rank}
'''
        ax2.text(0.01, 0.95, txt, 
                 transform=ax2.transAxes, 
                 verticalalignment='top', 
                 bbox=dict(facecolor='wheat', edgecolor='blue', pad=3.0, alpha=0.5)
                 )
        
        q = query_rank(ut.session, proxy_id)
        rank_df = pd.read_sql(q.statement, q.session.bind, parse_dates=["when"])
        ax3.plot(rank_df.when, rank_df['rank'], "o-", label=remark) # rank是pandas内置方法，因此不能用df.rank，只能用df['rank']
        ax3.set_title('历史排名')

    plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']
    plt.subplots_adjust(hspace=0.6, wspace=0.3)
    plt.tight_layout()
    #print(get_backend())
    plt.show()
    

if __name__ == '__main__':
    display()