from utils import ut
from model import Proxy, Delay
from matplotlib import get_backend
import matplotlib.pyplot as plt
import matplotlib.dates as md
from datetime import datetime, timedelta
from pybeans import alignment


def get_selected_data(proxy_id:tuple):
    return ut.session \
        .query(Delay.proxy_id, Proxy.type, Delay.when, Delay.value) \
        .join(Delay, Proxy.id == Delay.proxy_id) \
        .where(Delay.when > (datetime.now()-timedelta(days = 3))) \
        .where(Proxy.id == proxy_id) \
        .order_by(Delay.when) \
        .all()
    
    
def get_all_proxies():
    return ut.session \
        .query(Proxy) \
        .all()


data = {}
id_remark = {}
x_ticks = []

for i, p in enumerate(get_all_proxies()):
    data[p.remark] = dict(x=[], y=[])
    id_remark[p.id] = p.remark
    print(str(p.id).ljust(3), '|', alignment(p.remark, 30), '|', end=' ')
    if len(data.keys()) % 5 == 0:
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
        if proxy_id_int not in id_remark:
            print(f'>>> {proxy_id}不是正确的代理ID')
            input_correct = False
            break
        accepted_ids.append(proxy_id_int)
        
print('>>> 选中代理：', ', '.join([id_remark[id] for id in accepted_ids]))

for proxy_id in accepted_ids:
    delays = get_selected_data(proxy_id)
    remark = id_remark[proxy_id]
    for d in delays:
        data[remark]['x'].append(d.when)
        data[remark]['y'].append(d.value)

    fig, ax = plt.subplots()
    #print(remark, len(x_ticks), len(data[remark]), min_len)
    ax.plot(data[remark]['x'], data[remark]['y'], "o-", label=remark)
    ax.set_title(f'Delay curve - {remark}')
    ax.set_xlabel('Time')
    ax.set_ylabel('Curl Delay')
    xfmt = md.DateFormatter('%H:%M')
    ax.xaxis.set_major_formatter(xfmt)
    ax.set_xticks(data[remark]['x'][::50])

    for label in ax.xaxis.get_ticklabels():
        label.set_rotation(45)

plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']
plt.tight_layout()
#print(get_backend())
plt.show()