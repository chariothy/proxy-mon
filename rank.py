from pandas.core.frame import DataFrame
from utils import ut
from model import Proxy, Delay
import pandas as pd
from display import query_delay
from numpy import float64

import re
reg_proxy_multi = re.compile(r'\|(\d\.?\d?)x(?:\||$)')

from premailer import transform

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

def rank():
    id_proxy = {}
    multi_proxies = {}
    proxies = pd.read_sql(Proxy.__tablename__, ut.conn)
    for _, p in proxies.iterrows():
        #ut.D(p)
        id_proxy[p.id] = p
        match = reg_proxy_multi.search(p.remark)
        if match:
            multi = float(match.groups()[0])
        else:
            multi = 1.0
        if multi not in multi_proxies:
            multi_proxies[multi] = {}
        #ut.D(f'{p.remark}，倍率{multi}')
        
        q = query_delay(p.id)
        df = pd.read_sql(q.statement, q.session.bind, parse_dates=["when"])
        p05 = df.quantile(0.05).value
        p95 = df.quantile(0.95).value
        valid_df = df[(df.value >= p05) & (df.value <= p95)]
        multi_proxies[multi][p.id] = [
            p.id,
            valid_df.mean().value,
            valid_df.median().value,
            valid_df.count().value / df.count().value * 100,
            df[df.value.isnull()].count().proxy_id / df.count().value * 100,
            df.std().value,
            p.remark,
            p.type,
            df.count().value,
            0
        ]
        
    multi_proxie_score = {}
    columns = {0: 'id', 1:'vmean', 2:'vmed', 3:'vper', 4:'outper', 5:'std', 6:'remark', 7:'type', 8:'count', 9:'score'}
    column_asc = {'vmean': True, 'vmed': True, 'vper': False, 'outper': True, 'std': True}
    
    for multi in multi_proxies:
        #ut.D(f'倍率{multi}组排序')
        dfm = DataFrame(multi_proxies[multi]).T
        dfm.rename(columns=columns,inplace=True)
        #ut.D(dfm)
        for col in column_asc.keys():
            sorted_dfm = dfm.sort_values(by=[col], ignore_index=True, ascending=column_asc[col])
            for i, p in sorted_dfm.iterrows():
                # 排序成绩相加
                multi_proxies[multi][p.id][-1] += i
    
    data = {}
    top = 2
    for multi in multi_proxies:
        #ut.D(f'倍率{multi}组TOP3')
        dfr = DataFrame(multi_proxies[multi]).T
        dfr.rename(columns=columns,inplace=True)
        #print(dfr)
        sorted_dfr = dfr.sort_values(by=['score'], ignore_index=True)
        #print(sorted_dfr.head(3))
        data[multi] = sorted_dfr.head(top).T.to_dict().values()
    
    template = tmp_env.get_template('rank.html')
    html = template.render({'data': data})
    #su.D(html)
    html = transform(html)
    ut.send_email(f'最新TOP{top}代理报告', html_body=html)
    
if __name__ == '__main__':
    rank()
