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
    'use_proxy': False,
    'sqlite': {
        'db': 'logs/benchmark.dat'
    },
    'website': 'https://www.google.com/',
    'mysql': {
        'host': 'mysql',
        'port': 3306,
        'db': 'test',
        'user': 'test',
        'pwd': 'test'
    },
    'proxy': {
        'v2ray': {
            'bin': 'v2ray',
            'config_dir': '/app/logs',
            'vendor': 'fastlink',
            'subscribe': 'https://fastlink.ws/link/Q9J0Vmc3ffdhr3r?sub=3'
        },
        'ss': {
            'bin': 'ss-local'
        }
    },
    'max_client': 0,      # 同时使用的客户端，0 - 无限
}