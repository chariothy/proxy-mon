from pandas import DataFrame
from utils import ut, tmp_env
from pybeans import utils as pu

import pandas as pd
from datetime import datetime, timedelta

#from model import Proxy, Delay, Rank, query_delay, query_proxy

from premailer import transform
from pybeans import today
from notify import notify_by_ding_talk

import arrow
import os
import re
REG_DATE = re.compile(r'(\d{8})_\d{6}.json')

RANK_CONDITIONS = dict(
    avg = dict(asc=True, weight=3),
    std = dict(asc=True, weight=1),
    lost = dict(asc=True, weight=3)
)

def clear_old_data(days:int=3):
    ut.D(f'############ 清除{days}天前的CURL数据 ############')
    ut.session.query(Delay).where(Delay.when < (datetime.now()-timedelta(days = days))).delete()
    ut.D(f'############ 清除{days*10}天前的排名数据 ############')
    ut.session.query(Rank).where(Rank.when < (datetime.now()-timedelta(days = days*10))).delete()
    ut.session.commit()
    

def report(data):
    template = tmp_env.get_template('rank.html')
    html = template.render(dict(
        rank_conditions = RANK_CONDITIONS,
        data = data
    ))
    #su.D(html)
    html = transform(html)
    #print(html)
    result = ut.send_email(f'代理服务器统计报告', html_body=html)
    ut.D('发送邮件：', f'失败：{result}' if result else '成功')
    
    notify_by_ding_talk(data)
    
    
def rank_v1():
    import re
    reg_proxy_multi = re.compile(r'\|(\d\.?\d?)x(?:\||$)')

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
        report(data)


def df_from_json(data_path:str):
    result = pu.load_json(data_path)
    df = pd.json_normalize(
        result,
        record_path=['raw'],
        meta=['alias', 'id']
    ).rename(columns={0: 'curl'})
    #print(df)
    return df


def history(df_agg):
    today_int = int(pu.today('%Y%m%d'))
    df_agg['date'] = today_int
    df_agg['pos'] = df_agg.index
    today_cnt = 0
    history_path = ut['history_path']
    if os.path.exists(history_path):
        dfh = pd.read_csv(history_path, index_col=0, parse_dates=['date'])
        # 去除更新订阅后消失的节点，！记得换机场时要备份history，否则会被全部自动删除
        dfh = dfh[dfh.alias.isin(df_agg.alias)]
        if dfh.pos.count() == 0:
            raise RuntimeError('History中不存在任何新节点')
        # 只保留最近一个月的记录
        dfh = dfh[dfh.date>arrow.now().shift(months=-1).format('YYYY-MM-DD')]
        today_cnt = dfh[dfh.date==today_int].pos.count()
        if today_cnt == 0:
            all_frame = pd.concat([df_agg, dfh])
            all_frame.to_csv(history_path)
    else:
        df_agg.to_csv(history_path)
    ut.run(f'scp {history_path} {ut["scp_data_dir"]}')  # 复制到网站服务器
    ut.run(ut['after_scp_data'])


def rank(df:DataFrame):
    df_agg=df.groupby(['alias', 'id']).agg(avg=('curl','mean'),std=('curl','std'),valid=('curl','count'),total=('curl','size'))
    df_agg['lost'] = df_agg['total'] - df_agg['valid']
    df_agg.reset_index(inplace=True)
    df_agg['curl_rank'] = 0
    #print(df_agg)
    
    for col in RANK_CONDITIONS:
        condition = RANK_CONDITIONS[col]
        percentile = f'{col}_pct'
        df_agg[percentile] = df_agg[col].rank(method='min', ascending=condition['asc'])
        df_agg['curl_rank'] += df_agg[percentile] * condition['weight']

    return df_agg.sort_values(by=['curl_rank']).reset_index()
    

if __name__ == '__main__':
    df_agg = rank(df_from_json('./data/20211111_092739.json'))
    history(df_agg)
    #report(df_agg.head(4))
    
    