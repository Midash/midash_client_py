#!/usr/bin/python3.4
# -*- coding: utf-8 -*-
__version__ = "0.2.11"
global TERMINATE
TERMINATE = False
logo = r'''___  ______________  ___   _____ 
|  \/  |_   _|  _  \/ _ \ /  ___|
| .  . | | | | | | / /_\ \\ `--. 
| |\/| | | | | | | |  _  | `--. \
| |  | |_| |_| |/ /| | | |/\__/ /
\_|  |_/\___/|___/ \_| |_/\____/ 
                                 '''






#########################################################
#########################################################
#########################################################

from platform import system as system_name # Returns the system/OS name
from os import system as system_call       # Execute a shell command
import time

def ping(host):
    """
    Returns True if host (str) responds to a ping request.
    Remember that some hosts may not respond to a ping request even if the host name is valid.
    """

    # Ping parameters as function of OS
    parameters = "-n 1" if system_name().lower()=="windows" else "-c 1"

    # Pinging
    return system_call("ping " + parameters + " " + host) == 0

def wait_for_internet_connection():
    ips = ['midash.net']

    while True:
        for ip in ips:
            if ping(ip):
                return
            else:
                print ("Could not connect to server. Trying again in 5 seconds.")
                time.sleep(5)

wait_for_internet_connection()

#########################################################
#########################################################
#########################################################







# ----------------------------------------------------------------------------------------------------------------------
# region IMPORTS
# ----------------------------------------------------------------------------------------------------------------------

import traceback
import os
import sys
import time
import subprocess
import urllib.request
import json
from pprint import PrettyPrinter
import psutil
import wmi
from bs4 import BeautifulSoup
from socketIO_client import SocketIO, BaseNamespace
from colorama import init

init()

from colorama import Fore, Back, Style
import yaml
import uuid
import platform
from sluggify import slugify
from datetime import datetime
import logging
import requests
import zipfile
from distutils.version import StrictVersion
from subprocess import Popen
import socket
import urllib.request

# endregion







# ----------------------------------------------------------------------------------------------------------------------
# region GLOBALS
# ----------------------------------------------------------------------------------------------------------------------
# determine if application is a script file or frozen exe
if getattr(sys, 'frozen', False):
    realpath = os.path.dirname(os.path.realpath(sys.executable))
elif __file__:
    print ("Running as python script.")
    realpath = os.path.dirname(os.path.realpath(__file__))

rp = realpath

log = logging.getLogger("MIDAS")
log.setLevel(logging.DEBUG)
hdlr = logging.FileHandler(os.path.join(rp, "midas_client.log"))
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
log.addHandler(hdlr)

try:
    from pprint import PrettyPrinter

    pp = PrettyPrinter(indent=4)

    MINER_ID = slugify(platform.node() + "_" + str(uuid.getnode()))

    # endregion

    MINER_PASS = r"M#I4g50j#$i$$D7&7|%h#4'5Gd`/jh$~d7\56g25I#S2h#$@"
    SOCKET_NAMESPACE = r"/miner"

    # Server ip adress. Must be public static ip or DNS managed domain.
    # Change only if server moves to another ip
    SERVER_IP = "app.midash.net"
    # Server port.
    SERVER_PORT = 14864
    # Server protocol. HTTPS is encrypted, HTTP is unencrypted. HTTP is only used for development purposes.
    SERVER_PROTOCOL = "https"


    # ----------------------------------------------------------------------------------------------------------------------
    # region UTILS
    # ----------------------------------------------------------------------------------------------------------------------
    def conf(attr=None, default=None):
        conf_path = os.path.join(rp, 'config.yaml')
        if not os.path.exists(conf_path):
            print (Fore.RED, "Unable to find config.yaml file at path:", conf_path)
            time.sleep(20)
            log.error("Unable to find config.yaml file at path: {}".format(conf_path))
        with open(conf_path, 'r', encoding='utf-8') as f:
            data = yaml.load(f.read())
        if attr == None:
            return data
        else:
            try:
                return data[attr]
            except KeyError:
                return default



    def temp_status(temp, warn, crit):
        if temp == 0:
            return 'danger'
        if temp < warn:
            return "success"
        elif temp >= warn and temp < crit:
            return "warning"
        else:
            return "danger"


    def pre_flight_checks():
        print("Check version...")
        try:
            new_version = \
            requests.get(r"http://{}:{}/client_info".format(SERVER_IP, str(SERVER_PORT))).json()[
                'latest_version']
        except:
            new_version = None
        if new_version != None:
            if StrictVersion(__version__) < StrictVersion(new_version):
                print("New version available. Updating.")
                self_update()
                return False
        else:
            print("Unable to connect to check version.")
        print("Update not required")

        #####################
        '''
        print("Check updater version...")
        try:
            new_version = \
                requests.get(r"http://{}:{}/updater_info".format(SERVER_IP, str(SERVER_PORT))).json()[
                    'latest_version']
        except:
            new_version = None
        if new_version != None:
            if StrictVersion(__version__) < StrictVersion(new_version):
                print("New updater version available. Updating.")
                update_updater()
                return True
        else:
            print("Unable to connect to check version.")
        print("Updater is up to date not required")
        '''
        ###########

        config = conf()
        if "MINER_API" not in config:
            conf_add("MINER_API", "EthDcrMiner64")
            print ("MINER_API was not found in config file, added update default: EthDcrMiner64")

        if "MINER_API_PORT" not in config:
            print("MINER_API was not found in config file, added update default: 3333")
            conf_add("MINER_API_PORT", 3333)


        return True

    def conf_add(key, value):
        with open(os.path.join(rp, 'config.yaml'), 'a+', encoding='utf-8') as f:
            f.write("\n{}: {}\n".format(key, str(value)))

    def self_update():
        try:
            updater_cmd = '{}'.format(os.path.join(rp, "midas_client_updater.exe"))
            print("Starting updater:", updater_cmd)
            os.startfile(updater_cmd)
            print("Hara-kiri...")
            time.sleep(1)
            global TERMINATE
            TERMINATE = True
            sts = Popen("taskkill /F /IM midas_client_startup.exe /T", shell=True)
            #sys.exit()
        except Exception as e:
            print("Unable to run updater.")
            print(e)
            time.sleep(2)


    def update_updater():
        try:
            realpath = os.path.dirname(os.path.realpath(__file__))

            local_filename = os.path.join(rp, 'midas_updater_update.zip')
            r = requests.get(r"http://{}:{}".format(SERVER_IP, str(SERVER_PORT)) + "/updater_update/windows", stream=True)
            f = open(local_filename, 'wb')
            file_size = int(r.headers['Content-Length'])
            print("Updater update. File size:", file_size)
            print("")
            chunk = int(file_size / 100)
            num_bars = file_size / chunk
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

            print("Delete archive")
            os.remove(local_filename)

        except Exception as e:
            print ("Unable to update updater:", e)



    # endregion
    # ----------------------------------------------------------------------------------------------------------------------
    # region DATA GATHERING
    # ----------------------------------------------------------------------------------------------------------------------
    def getData_EthDcrMiner64(return_data, GPU_TEMP_WARN, GPU_TEMP_CRIT):
        """
        {"result":
        ["9.3 - ETH", "21", "182724;51;0", "30502;30457;30297;30481;30479;30505", "0;0;0", "off;off;off;off;off;off",
         "53;71;57;67;61;72;55;70;59;71;61;70", "eth-eu1.nanopool.org:9999", "0;0;0;0"]}
         "9.3 - ETH"				- miner version.
        "21"					- running time, in minutes.
        "182724"				- total ETH hashrate in MH/s, number of ETH shares, number of ETH rejected shares.
        "30502;30457;30297;30481;30479;30505"	- detailed ETH hashrate for all GPUs.
        "0;0;0"					- total DCR hashrate in MH/s, number of DCR shares, number of DCR rejected shares.
        "off;off;off;off;off;off"		- detailed DCR hashrate for all GPUs.
        "53;71;57;67;61;72;55;70;59;71;61;70"	- Temperature and Fan speed(%) pairs for all GPUs.
        "eth-eu1.nanopool.org:9999"		- current mining pool. For dual mode, there will be two pools here.
        "0;0;0;0"				- number of ETH invalid shares, number of ETH pool switches, number of DCR invalid shares, number of DCR pool switches.
        """

        TCP_IP = '127.0.0.1'
        TCP_PORT = conf("MINER_API_PORT")
        BUFFER_SIZE = 1024
        MESSAGE = '{"id":0,"jsonrpc":"2.0","method":"miner_getstat1"}'

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((TCP_IP, TCP_PORT))
        s.send(MESSAGE.encode('utf-8'))
        data = s.recv(BUFFER_SIZE).decode('utf-8')
        s.close()

        result = json.loads(data)['result']

        temps_fans = result[6].split(";")
        #print (result)
        #print (temps_fans)
        temps= temps_fans[0::2]
        fans = temps_fans[1::2]
        hashrates = result[3].split(";")
        working_gpus = len(hashrates)

        for i in range(0, working_gpus):
            #print ("GPU", i)
            return_data['GPUs'].append({
                "name": "GPU{}".format(str(i)),
                "parent": "",
                "temperature": int(temps[i]),
                "status": temp_status(int(temps[i]), GPU_TEMP_WARN, GPU_TEMP_CRIT),
                "speed_sps": int(hashrates[i]),
                "gpu_power_usage": 0,
                "fan_speed": int(fans[i])
            })

        # print ("Gathered data.")
        failed_gpus = conf('GPU_INSTALLED_COUNT') - working_gpus
        for fgpu in range(0, failed_gpus):
            return_data['GPUs'].append({
                "name": "GPU",
                "parent": "unknown",
                "temperature": 0,
                "status": "danger",
                "gpu_power_usage": 0,
                "speed_sps": 0
            })

        return return_data


    def getData_ewbf(return_data, GPU_TEMP_WARN, GPU_TEMP_CRIT):
        try:
            api_response = urllib.request.urlopen('http://127.0.0.1:{}/getstat'.format(conf("MINER_API_PORT")))
            api_json = api_response.read()
            api_data = json.loads(api_json.decode('utf-8'))
            api_data['GPUs'] = api_data.pop('result')
            return_data = api_data

            for gpu in return_data['GPUs']:
                gpu['status'] = temp_status(gpu['temperature'], GPU_TEMP_WARN, GPU_TEMP_CRIT)
        except ConnectionRefusedError:
            print ("Unable to connect to EWBF miner, connection refused. Make sure to use --api option in EWBF miner.")

        return return_data

    getDataProcs = {
        'EthDcrMiner64': getData_EthDcrMiner64,
        'ewbf': getData_ewbf
    }


    def OHM_Data(return_data, GPU_TEMP_WARN, GPU_TEMP_CRIT):
        if not "OpenHardwareMonitor.exe" in (p.name() for p in psutil.process_iter()):
            # print ("Open Hardware Monitor is not running, starting it now...")
            subprocess.Popen([os.path.join(realpath, "OpenHardwareMonitor", "OpenHardwareMonitor.exe")], shell=True)
            while not "OpenHardwareMonitor.exe" in (p.name() for p in psutil.process_iter()):
                print("Waiting for OHM to start...", end='\r')
                time.sleep(10)

        # print ("WMI request...")
        w = wmi.WMI(namespace="root\OpenHardwareMonitor")
        # print ("Temp infos...")
        temperature_infos = w.Sensor()
        for sensor in temperature_infos:
            if sensor.SensorType == u'Temperature':
                if "gpu" in sensor.Name.lower():
                    # print(sensor.Name, sensor.parent, sensor.Value)
                    return_data['GPUs'].append({
                        "name": sensor.Name,
                        "parent": sensor.parent,
                        "temperature": sensor.Value,
                        "status": temp_status(sensor.Value, GPU_TEMP_WARN, GPU_TEMP_CRIT),
                        "speed_sps": 0,
                        "gpu_power_usage": 0
                    })
                elif "cpu" in sensor.Name.lower():
                    # print(sensor.Name, sensor.parent, sensor.Value)
                    return_data['CPUs'].append({
                        "name": sensor.Name,
                        "parent": sensor.parent,
                        "temperature": sensor.Value
                    })
        # print ("Gathered data.")
        working_gpus = len(return_data['GPUs'])
        failed_gpus = conf('GPU_INSTALLED_COUNT') - working_gpus
        for fgpu in range(0, failed_gpus):
            return_data['GPUs'].append({
                "name": "GPU",
                "parent": "unknown",
                "temperature": 0,
                "status": "danger",
                "gpu_power_usage": 0,
                "speed_sps": 0
            })

        return return_data


    def getData(*args, **kwargs):
        MINER_API = kwargs.get('MINER_API')
        #print (MINER_API)
        if MINER_API not in getDataProcs:
            getData_proc = OHM_Data
        else:
            getData_proc = getDataProcs[MINER_API]

        kwargs.pop("MINER_API")

        return getData_proc(*args, **kwargs)


    # endregion





    # ----------------------------------------------------------------------------------------------------------------------
    # region CLASSES
    # ----------------------------------------------------------------------------------------------------------------------
    class UI_Namespace(BaseNamespace):
        def on_connect(self):
            pass


    class Miner_Namespace(BaseNamespace):



        def on_connect(self):
            print('[Connected]')
            self.login()

        def on_reconnect(self):
            print('[Reconnected]')
            self.login()

        def on_disconnect(self):
            print('[Disconnected]')

        def on_login_success(self, data=None):
            print("Login success", data)

        def on_login_fail(self, data=None):
            print("Login fail", data)

        def login(self):
            print("Logging in...")
            self.emit("login", {"user_id": MINER_ID,
                                "password": MINER_PASS,
                                "friendly_name": MINER_NAME,
                                "token": TOKEN
                                })

        def on_get_system_info(self, data):
            print("Last system info requested at:", datetime.now(), end="\r")

            config = conf()

            GPU_TEMP_WARN = config['GPU_TEMP_WARN']
            GPU_TEMP_CRIT = config['GPU_TEMP_CRIT']

            return_data = {}
            return_data['GPUs'] = []
            return_data['CPUs'] = []

            try:
                return_data = getData(return_data, GPU_TEMP_WARN, GPU_TEMP_CRIT, MINER_API=config['MINER_API'])
            except ConnectionRefusedError:
                return_data = None
                print("Unable to get data from given miner. Make sure it's running and it's API turned on, or set MINER_API to None to use OHM")
            except:
                return_data = None
                print ("Unable to get data from given miner. Make sure it's running and it's API turned on, or set MINER_API to None to use OHM")
                traceback.print_exc()

            if return_data != None:
                #pp.pprint(return_data)

                # GPU_Max_Temp
                max_temperature = 0
                for gpu in return_data['GPUs']:
                    if gpu['temperature'] > max_temperature:
                        max_temperature = gpu['temperature']
                return_data['GPU_Max_Temp'] = max_temperature

                # GPU_Avg_Power
                total_power = 0
                for gpu in return_data['GPUs']:
                    total_power = total_power + gpu['gpu_power_usage']
                return_data['GPU_Avg_Power'] = total_power / len(return_data['GPUs'])

                # GPU_Total_Speed
                total_sol = 0
                for gpu in return_data['GPUs']:
                    total_sol = total_sol + gpu['speed_sps']
                return_data['GPU_Total_Speed'] = total_sol

                # Miner overall status
                return_data['miner_status_color'] = "secondary"
                # if 0 in [return_data['GPU_Max_Temp'], return_data['GPU_Avg_Power'], return_data['GPU_Total_Speed']]:
                if 0 in [return_data['GPU_Max_Temp']]:
                    return_data['miner_status_color'] = "warning"
                if return_data['GPU_Max_Temp'] > GPU_TEMP_WARN:
                    return_data['miner_status_color'] = "warning"
                if return_data['GPU_Max_Temp'] > GPU_TEMP_CRIT:
                    return_data['miner_status_color'] = "danger"

                return_data['friendly_name'] = MINER_NAME
                return_data['client_version'] = __version__

                self.emit("system_info", return_data)

        def on_update(self, data):
            try:
                self._io._close()
            except Exception as e:
                log.error("Unable to stop socketIO: {}".format(e))
            self_update()

            return

        def on_set_config(self, data):
            current_config = conf()
            for key, value in data['new_config_items']:
                current_config[key]=value

            with open(os.path.join(rp, 'config.yaml'), 'w', encoding='utf-8') as f:
                f.write(yaml.dump(current_config, default_flow_style=False))


    # endregion


    if conf("USE_PC_NAME") != 0:
        MINER_NAME = platform.node()
    else:
        MINER_NAME = conf('MINER_NAME')
        if MINER_NAME == None:
            print("MINER_NAME is not set in config and USE_PC_NAME is set to false. Me need miner name!")
            MINER_NAME = input("Please, enter this MINER_NAME: ")
            with open(os.path.join(rp, 'config.yaml'), 'a+', encoding='utf-8') as f:
                f.write("\n\n# Added during first launch \n MINER_NAME: {}\n\n".format(MINER_NAME))

    TOKEN = conf('TOKEN')





    def main():
        RESTART_DELAY = conf("RESTART_DELAY")
        if RESTART_DELAY == None:
            RESTART_DELAY = 60

        print(Fore.LIGHTYELLOW_EX)
        print(logo, "\nVersion:", __version__, "\n")
        print(Fore.WHITE)
        print("Miner ID is:", MINER_ID)
        print("Miner Name is:", MINER_NAME)
        print("Restart Delay:", RESTART_DELAY, "minutes")
        print("")

        time.sleep(conf("STARTUP_DELAY", 5))

        while not TERMINATE:
            try:
                #log.info("(Re)Starting.")
                if pre_flight_checks():
                    addr = "{}://{}".format('http', socket.gethostbyname(SERVER_IP))
                    print("Wait for connection: {}:{}".format(addr, SERVER_PORT))
                    socketIO = SocketIO(addr, SERVER_PORT)

                    miner_namespace = socketIO.define(Miner_Namespace, SOCKET_NAMESPACE)
                    # ui_namespace = socketIO.define(UI_Namespace, SOCKET_NAMESPACE)

                    socketIO.wait(seconds=RESTART_DELAY * 60)
                else:
                    print("Update required.")

            except:
                print(Back.YELLOW, Fore.WHITE)
                print("CRITICAL ERROR!")
                traceback.print_exc()
                log.error(traceback.format_exc())
                print("Trying to restart socket connection.")
                print(Back.BLACK, Fore.WHITE)
                time.sleep(2)

    if __name__ == '__main__':
        try:
            main()
        except:
            log.error(traceback.format_exc())
except Exception as e:
    log.error("Unknown error: {}".format(e))
    log.error(traceback.format_exc())