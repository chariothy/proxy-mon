from pandas.core.frame import DataFrame
from utils import Util
ut = Util('proxy-rank')

from model import Proxy, Delay, Rank, query_delay, query_proxy
import pandas as pd
from numpy import float64
from datetime import datetime, timedelta

import re
reg_proxy_multi = re.compile(r'\|(\d\.?\d?)x(?:\||$)')

from premailer import transform
from pybeans import today

def my_finalize(thing):
    if thing is None:
        return ''
    elif type(thing) in (float, float64):
        return round(thing, 2)
    else:
        #ut.D(f'##### {type(thing)}')
        return thing

import os
from jinja2 import Environment, FileSystemLoader
tmp_env = Environment(loader=FileSystemLoader(os.getcwd() + '/templates'), finalize=my_finalize)


def clear_old_data(days:int=3):
    ut.D(f'############ 清除{days}天前的CURL数据 ############')
    ut.session.query(Delay).where(Delay.when < (datetime.now()-timedelta(days = days))).delete()
    ut.D(f'############ 清除{days*10}天前的排名数据 ############')
    ut.session.query(Rank).where(Rank.when < (datetime.now()-timedelta(days = days*10))).delete()
    ut.session.commit()
    
    
def rank():
    id_proxy = {}
    multi_proxies = {}
    proxies = query_proxy(ut.session).all()
    for p in proxies:
        #ut.D(p)
        id_proxy[p.id] = p
        match = reg_proxy_multi.search(p.remark)
        if match:
            multi = float(match.groups()[0])
        else:
            multi = 1.0
        
        q = query_delay(ut.session, p.id)
        df = pd.read_sql(q.statement, q.session.bind, parse_dates=["when"])
        p01 = df.value.quantile(0.01)
        p99 = df.value.quantile(0.95)
        vdf = df[(df.value >= p01) & (df.value <= p99)]
        if vdf.proxy_id.count() < 100:
            continue
        if multi not in multi_proxies:
            multi_proxies[multi] = {}
            #ut.D(f'{p.remark}，倍率{multi}')
        multi_proxies[multi][p.id] = [
            p.id,
            vdf.value.mean(),
            vdf.value.median(),
            df[df.value.isnull()].proxy_id.count() / df.value.count() * 100,
            vdf.value.std(),
            p.remark,
            p.type,
            vdf.value.count(),
            df.value.count(),
            0,
            0 if p.avg_rank is None else round(p.avg_rank),
            0,
            0   # 必须放在最后一个
        ]
    #ut.D(multi_proxies)
    columns = {
        'id': None,
        'vmean': True,  # valid mean
        'vmed': True,   # valid med
        'outper': True, # timeout percentage
        'std': True,
        'remark': None,
        'type': None,
        'vcount': None,
        'count': None,
        'drank': None, # delta rank
        'arank': None,  # avg rank
        'nrank': None, # new rank
        'score': None
    }
    column_name = {k:v for k,v in enumerate(columns)}
    
    for multi in multi_proxies:
        dfm = DataFrame(multi_proxies[multi]).T
        dfm.rename(columns=column_name,inplace=True)
        #ut.D(f'倍率{multi}组排序\n', dfm)
        for col in columns:
            if columns[col] is not None:
                sorted_dfm = dfm.sort_values(by=[col], ignore_index=True, ascending=columns[col])
                for i, p in sorted_dfm.iterrows():
                    # 排序成绩相加
                    multi_proxies[multi][p.id][-1] += i
    
    data = {}
    top = 2
    today_str = today()
    for multi in multi_proxies:
        ut.D(f'倍率{multi}组TOP3')
        dfr = DataFrame(multi_proxies[multi]).T
        dfr.rename(columns=column_name,inplace=True)
        #print(dfr)
        sorted_dfr = dfr.sort_values(by=['score'], ignore_index=True)
        print(sorted_dfr.head(5))
        for i, sp in sorted_dfr.iterrows():
            new_rank = i + 1
            sp.nrank = new_rank
            old_rank = multi_proxies[multi][sp.id][-3]
            if old_rank is not None:
                sp.drank = new_rank - old_rank
            
            rank_mod = ut.session \
                .query(Rank) \
                .where(Rank.proxy_id == sp.id) \
                .where(Rank.when == today_str) \
                .one_or_none()
            if not rank_mod:
                rank_mod = Rank()
                rank_mod.proxy_id = sp.id
                rank_mod.when = today_str
            rank_mod.rank = new_rank
            ut.session.add(rank_mod)
        data[multi] = sorted_dfr.T.to_dict().values()
    
    if data:
        #TODO: Report all NONE proxy
        ut.session.commit()
        template = tmp_env.get_template('rank.html')
        html = template.render({'data': data})
        #su.D(html)
        html = transform(html)
        #print(html)
        ut.D('发送邮件：', ut.send_email(f'代理服务器统计报告', html_body=html))
    
if __name__ == '__main__':
    rank()
    if os.environ.get('PROXY_RANK_ENV') == 'prod':
        clear_old_data()
