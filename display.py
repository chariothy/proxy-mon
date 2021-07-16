from utils import ut
from model import Proxy, Delay
from matplotlib import get_backend
import matplotlib.pyplot as plt
import matplotlib.dates as md
from datetime import datetime, timedelta
from pybeans import alignment

delays = ut.session \
    .query(Delay.proxy_id, Proxy.remark, Proxy.type, Delay.when, Delay.value) \
    .join(Delay, Proxy.id == Delay.proxy_id) \
    .where(Delay.when > (datetime.now()-timedelta(days = 3))) \
    .order_by(Proxy.id) \
    .all()

data = {}
id_remark = {}
first_proxy = None
x_ticks = []

for i, d in enumerate(delays):
    if first_proxy is None:
        first_proxy = d.remark
    if d.remark not in data:
        data[d.remark] = []
        id_remark[d.proxy_id] = d.remark
        print(str(d.proxy_id).ljust(3), '|', alignment(d.remark, 30), '|', end=' ')
        if len(data.keys()) % 5 == 0:
            print()
            #print('-'*175)
    if d.remark == first_proxy:
        x_ticks.append(d.when)
    data[d.remark].append(d.value)
    #print(d.remark, d.type, d.value, d.when)

print()

input_correct = False
while not input_correct:
    proxy_ids = input('输入要显示的代理id，以逗号分隔：')
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
        
print('选中代理：', end='')
min_len = 9999
for accepted_id in accepted_ids:
    remark = id_remark[accepted_id]
    print(remark, end=', ')
    if len(data[remark]) < min_len:
        min_len = len(data[remark])
print()

for accepted_id in accepted_ids:
    remark = id_remark[accepted_id]
    fig, ax = plt.subplots()
    #print(remark, len(x_ticks), len(data[remark]), min_len)
    ax.plot(x_ticks[:min_len], data[remark][:min_len], "o-", label=remark)
    ax.set_title(f'Delay curve - {remark}')
    ax.set_xlabel('Time')
    ax.set_ylabel('Curl Delay')
    ax.set_xticks(x_ticks)
    xfmt = md.DateFormatter('%H:%M')
    ax.xaxis.set_major_formatter(xfmt)
    ax.set_xticks(x_ticks[::10])

    for label in ax.xaxis.get_ticklabels():
        label.set_rotation(45)

plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']
plt.tight_layout()
#print(get_backend())
plt.show()