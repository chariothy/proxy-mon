CONFIG = {
    'log': {
        'level': 'DEBUG',   # 与log库的level一致，包括DEBUG, INFO, ERROR
                            #   DEBUG   - Enable stdout, file, mail （如果在dest中启用）
                            #   INFO    - Enable file, mail         （如果在dest中启用）
                            #   ERROR   - Enable mail               （如果在dest中启用）
        'dest': {
            'stdout': 1, 
            'file': 1, 
            'mail': 1       # 0     - 不使用； 
                            # 1     - 使用，收件人使用mail中设置的to；
                            # 字符串 - 直接指定收件人， Ex. : 'Henry TIAN <chariothy@gmail.com>'
        },
        'sql': 1
    },
    'mail': {
        'from': 'Henry TIAN <15050506668@163.com>',
        'to': 'Henry TIAN <6314849@qq.com>'
    },
    'smtp': {
        'host': 'smtp.163.com',
        'port': 25,
        'user': '15050506668@163.com',
        'pwd': '123456'
    },
    'dingtalk': {                       # 通过钉钉机器人发送通知，具体请见钉钉机器人文档
        'token': 'DINGTALK_BOT_TOKEN',
        'secret' : 'DINGTALK_BOT_SECRET' # 钉钉机器人的三种验证方式之一为密钥验证
    },
    'use_proxy': False,
    'sqlite': {
        'db': 'logs/benchmark.dat'
    },
    'website': 'https://www.google.com/',
    'curl_count': 10,
    'gateways': {
        'guest': '10.8.6.1',
        'admin': '10.8.9.1',
        'device': '10.8.7.1',
        'mobile': '10.8.8.1'
    },
    'scp_data_dir': 'henry@10.8.9.88:/www/proxy-mon/data/',
    'top_n': 4,
    'history_path': './data/history.csv',
    'after_scp_data': 'ssh henry@10.8.9.88 docker restart proxy-dash'
}