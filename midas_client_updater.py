'''
TODO

- Restart once in a while.
'''

version = "1.0.1"

print ("Updater version", version)

import os
import requests
import yaml
import zipfile
import traceback
import time
from subprocess import Popen


# Server ip adress. Must be public static ip or DNS managed domain.
# Change only if server moves to another ip
SERVER_IP = "midash.net"
# Server port.
SERVER_PORT = 14864
# Server protocol. HTTPS is encrypted, HTTP is unencrypted. HTTP is only used for development purposes.
SERVER_PROTOCOL = "https"

try:
    realpath = os.path.dirname(os.path.realpath(__file__))
    rp = realpath

    def conf(attr=None):
        with open (os.path.join(rp, 'config.yaml'), 'r', encoding='utf-8') as f:
            data = yaml.load(f.read())
        if attr == None:
            return data
        else:
            return data[attr]

    time.sleep(6)
    print ("Making sure midas_client_startup.exe is dead...")
    sts = Popen("taskkill /F /IM midas_client_startup.exe /T", shell=True).wait()
    time.sleep(2)
    local_filename = os.path.join(rp, 'midas_client_update.zip')
    r = requests.get(r"http://{}:{}".format(SERVER_IP, str(SERVER_PORT))+"/client_update/windows", stream=True)
    f = open(local_filename, 'wb')
    file_size = int(r.headers['Content-Length'])
    print("Update. File size:", file_size)
    print("")
    chunk = int(file_size / 100)
    num_bars = file_size / chunk
    # bar = progressbar.ProgressBar(maxval=num_bars).start()
    i = 0
    for chunk in r.iter_content(chunk):
        f.write(chunk)
        # bar.update(i)
        print("Loading: ", int(i / num_bars * 100), "%", end="\r")
        i += 1
    print("Loading: ", 100, "%", end="\r")
    f.close()
    print("")

    print("Extracting...")
    zip_ref = zipfile.ZipFile(local_filename)  # create zipfile object
    zip_ref.extractall(rp)  # extract file to dir
    zip_ref.close()  # close file

    print ("Delete archive")
    os.remove(local_filename)

    restart_cmd = '{}'.format(os.path.join(rp, "midas_client_startup.exe"))
    print ("Update finished. Restarting application with command:", restart_cmd)

    os.startfile(restart_cmd)

    print ("Kill self")
    time.sleep(4)
    sts = Popen("taskkill /F /IM midas_client_updater.exe /T", shell=True)
except:
    with open(os.path.join(rp, "updater.log"), 'a+') as f:
        f.write (traceback.print_exc())
    print ("Error during update. Read updater.log for more details. Closing in 2 seconds.")
    time.sleep(2)

