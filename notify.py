import requests
import json
from utils import ut
import time
import hmac
import base64
import hashlib
import urllib.parse


def create_sign_for_dingtalk(secret: str):
    """
    docstring
    """
    timestamp = str(round(time.time() * 1000))
    secret_enc = secret.encode('utf-8')
    string_to_sign = '{}\n{}'.format(timestamp, secret)
    string_to_sign_enc = string_to_sign.encode('utf-8')
    hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
    sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
    return timestamp, sign


DINGTALK_API_URL="https://oapi.dingtalk.com/robot/send?access_token={}"
DINGTAIL_HEADERS = {'Content-Type': 'application/json'}

def do_notify_by_ding_talk(config, data):
    """发消息给钉钉机器人
    """
    token = config['token']
    secret = config['secret']
    
    assert token and secret

    url = DINGTALK_API_URL.format(token)
    timestamp, sign = create_sign_for_dingtalk(secret)
    url += f'&timestamp={timestamp}&sign={sign}'
    
    #APP.debug(f'钉钉机器人 数据===> {data}')
    return requests.post(url=url, headers = DINGTAIL_HEADERS, data=json.dumps(data))


DINGTAIL_SUBJECT = "[PROXY_RANK] 最新测试结果"
DINGTAIL_BODY = """## <font color=#000080>TOP SERVERS：</font>\n
{body}\n
### 详情请见 [Dash](https://ss.thy.pub:66)\n
"""


def notify_by_ding_talk(data):
    """发消息给钉钉机器人
    """
    body = '\n'.join((f"- 【{c[1]['alias']}】 {c[1]['curl_rank']}" for c in data.iterrows()))
    dt_msg = {
        "msgtype": 'markdown',
        "markdown": {
            'title': DINGTAIL_SUBJECT,
            'text': DINGTAIL_BODY.format(body=body)
        }
    }
    res = do_notify_by_ding_talk(ut['dingtalk'], dt_msg)
    ut.debug(f'钉钉推送结果：{res.json()}')
