from utils import ut
from model import Proxy, Delay, query_delay, query_proxy
from matplotlib import get_backend
import matplotlib.pyplot as plt
import matplotlib.dates as md
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
        
        remark = id_proxy[proxy_id].remark

        fig, _ = plt.subplots()
        ax1 = fig.add_subplot(2, 1, 1)
        #print(remark, len(x_ticks), len(data[remark]), min_len)
        ax1.plot(df.when, df.value, "o-", label=remark)
        ax1.set_title(f'Delay curve - {remark}')
        ax1.set_xlabel('Time')
        ax1.set_ylabel('Curl Delay')
        xfmt = md.DateFormatter('%H:%M')
        ax1.xaxis.set_major_formatter(xfmt)
        ax1.set_xticks(df.when[::100])
        for label in ax1.xaxis.get_ticklabels():
            label.set_rotation(45)
        plt.grid() 

        ax2 = fig.add_subplot(2, 1, 2)
        # 绘制直方图
        df['value'].plot.hist(bins=30, alpha=0.5, rwidth=0.9, ax=ax2)
        ax3 = ax2.twinx()
        # 绘制密度图
        df['value'].plot(kind='kde', secondary_y=True, ax=ax3)
        #ax3.set_xticklabels([])
        plt.grid()      # 添加网格
        
        p10 = df.quantile(0.1).value
        p90 = df.quantile(0.9).value
        valid_df = df[(df.value >= p10) & (df.value <= p90)]
        txt = f'''
数据量 = {df.count().value}\n
最小值 = {df.min().value}\n
最大值 = {df.max().value}\n
平均值 = {df.mean().value}\n
10%位数 = {p10}\n
中位数 = {df.median().value}\n
90%位数 = {p90}\n
10~90数据量 = {valid_df.count().value}\n
10~90数据占比 = {valid_df.count().value / df.count().value}\n
超时数据量 = {df[df.value.isnull()].count().proxy_id }\n
超时数据占比 = {df[df.value.isnull()].count().proxy_id / df.count().value}\n
标准差 = {df.std().value}\n
平均绝对偏差 = {df.mad().value}\n
偏度 = {df.skew().value}\n
峰度 = {df.kurt().value}\n
最近排名 = {id_proxy[proxy_id].rank}
'''
        fig.text(0.2, 0.1, txt, bbox=dict(facecolor='none', edgecolor='blue', pad=10.0))

    plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']
    plt.tight_layout()
    #print(get_backend())
    plt.show()
    

if __name__ == '__main__':
    display()