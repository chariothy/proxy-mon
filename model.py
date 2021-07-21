# coding: utf-8
from sqlalchemy import Column, DECIMAL, Date, Float, String, TIMESTAMP, text, JSON, BOOLEAN, VARCHAR, INTEGER, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql.functions import rank
from sqlalchemy.sql.sqltypes import Boolean

from datetime import datetime, timedelta

Base = declarative_base()

def to_dict(self):
    return {c.name: getattr(self, c.name, None)
        for c in self.__table__.columns}
Base.to_dict = to_dict


class Proxy(Base):
    __tablename__ = 'proxy_list'
    __table_args__ = {'comment': '代理信息'}

    id = Column(INTEGER, primary_key=True, comment='ID')
    type = Column(VARCHAR(10), nullable=False, comment='类型')
    addr = Column(VARCHAR(50), nullable=False, comment='地址')
    port  = Column(INTEGER, nullable=False, comment='端口')
    rank  = Column(INTEGER, nullable=True, comment='排名')
    active  = Column(BOOLEAN, nullable=False, server_default='1', comment='使用')
    remark = Column(VARCHAR(50), nullable=False, comment='备注')


class Delay(Base):
    __tablename__ = 'proxy_delay'
    __table_args__ = {'comment': 'PING延迟'}

    id = Column(INTEGER, primary_key=True, comment='ID')
    proxy_id = Column(INTEGER, nullable=False, comment='代理ID')
    when = Column(TIMESTAMP, nullable=False, server_default=func.now(), comment='时间')
    value = Column(INTEGER, nullable=True, comment='延迟')
    
    
def query_delay(session, proxy_id:int):
    return session \
        .query(Delay.proxy_id, Proxy.type, Delay.when, Delay.value) \
        .join(Delay, Proxy.id == Delay.proxy_id) \
        .where(Delay.when > (datetime.now()-timedelta(days = 3))) \
        .where(Proxy.id == proxy_id) \
        .order_by(Delay.when)
        
        
def query_proxy(session):
    return session \
        .query(Proxy) \
        .where(Proxy.active == 1) \
        .order_by(Proxy.id)