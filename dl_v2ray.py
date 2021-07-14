import requests
import os
import stat
import os.path
import zipfile
import time
from utils import ut

V2RAY_PATH = '/usr/bin'


def formatFloat(num):
    return '{:.2f}'.format(num)


def downloadFile(name, url):
    headers = {'Proxy-Connection': 'keep-alive'}
    r = requests.get(url, stream=True, headers=headers)
    length = float(r.headers['content-length'])
    ut.D(f'Total size = {length}')
    try:
        f = open(name, 'wb')
        count = 0
        count_tmp = 0
        time1 = time.time()
        for chunk in r.iter_content(chunk_size=512):
            if chunk:
                f.write(chunk)
                count += len(chunk)
                if time.time() - time1 > 2:
                    p = count / length * 100
                    speed = (count - count_tmp) / 1024  / 2
                    count_tmp = count
                    ut.D(name + ': ' + formatFloat(p) + '%' + ' Speed: ' + formatFloat(speed) + 'KB/S')
                    time1 = time.time()
    finally:
        f.close()


def get_ver():
    req = requests.get('https://api.github.com/repos/v2fly/v2ray-core/releases/latest')
    data = req.json()
    #ut.D(data)
    ver = data['tag_name']
    ut.D(f'Latest v2ray version: {ver}')
    return ver


def dl_v2ray():
    ver = get_ver()
    ZIP_NAME = f'v2ray-linux-64-{ver}.zip'
    ZIP_PATH = f"/root/{ZIP_NAME}"
    if not os.path.exists(ZIP_PATH):
        link = f'https://github.com/v2fly/v2ray-core/releases/download/{ver}/v2ray-linux-64.zip'
        ut.D(f'Downloading from {link}')
        downloadFile(ZIP_PATH, link)
        ut.D('Downloaded v2ray zip.')
        if zipfile.is_zipfile(ZIP_PATH):  # 检查是否为zip文件
            with zipfile.ZipFile(ZIP_PATH, 'r') as zipf:
                zipf.extractall(V2RAY_PATH)
        else:
            raise ValueError(f'{ZIP_PATH} is not a valid zip file.')
        
        ut.D(f'Unzipped to {V2RAY_PATH}')
        v2ray_bin = f'{V2RAY_PATH}/v2ray'
        st = os.stat(v2ray_bin)
        os.chmod(v2ray_bin, st.st_mode | stat.S_IEXEC)
        ut.D(f'chmod +x {v2ray_bin}')
    else:
        ut.D(f'{ZIP_PATH} exists.')


if __name__ == '__main__':
    dl_v2ray()