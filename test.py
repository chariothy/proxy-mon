from utils import Util
import subprocess
from v2ray import subscribe

util = Util()


a = subscribe(util['proxy.fasklink.subscribe'])
print(a)

#server = a[0]
#print(server)
#args = [util['proxy.fasklink.bin'], '-config', r"C:\programs\v2ray\fastlink-config.json"]

#proc = subprocess.Popen(args)