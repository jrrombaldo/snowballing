
from json.tool import main
import util.config as config
import requests
import multiprocessing

from torpy import TorClient
from torpy.cli.socks import SocksServer
from torpy.utils import register_logger
from retry.api import retry_call

from requests.exceptions import ConnectionError, ConnectTimeout
from torpy.circuit import CircuitExtendError
from socks import ProxyConnectionError


from util.config import config


class TorThread():
    def __init__(self, port):
        self.port = port
        self.ip = config['tor']['proxy_ip']
        self.hc_url = config['tor']['health_check_host']
        self.hops = config['tor']['hops']

        self.proxies = {
            'http': f'socks5://{self.ip}:{self.port}',
            'https': f'socks5://{self.ip}:{self.port}',
        }

    def __check_till_proxy_is_ready(self):
        print ("checking connection ... ")
        print (requests.get(self.hc_url, proxies=self.proxies).text)
        print ("connection completed")

    def _proxy_proccess(ip, port, hops ):
        # register_logger(True)
        with TorClient().create_circuit(hops_count=hops) as circuit:
            with SocksServer(circuit, ip, port ) as socks_srv:
                socks_srv.start()


    def start(self, ):
        self.tor_proc =  multiprocessing.Process(
            target=TorThread._proxy_proccess, 
            args=(self.ip, self.port, self.hops))

        self.tor_proc.start()
        # tor_proc.join()

        retry_call(self.__check_till_proxy_is_ready,
            exceptions=(ConnectionError, ConnectTimeout, CircuitExtendError, 
                        ProxyConnectionError, ConnectionRefusedError, ),
            tries=10,
            delay=5)

    def terminate(self):
        self.tor_proc.terminate()
