

from torpy import TorClient
from torpy.cli.socks import SocksServer
from torpy.circuit import CircuitExtendError
import multiprocessing
import time

from retry import retry
import socks

import requests

from scholarly import scholarly, ProxyGenerator


from torpy.utils import register_logger

import logging
logging.basicConfig(level=logging.DEBUG)
logging.getLogger("torpy").setLevel(logging.WARNING)

hops=3
ip='localhost'
port=19999
url = 'http://ifconfig.me/ip'


proxies = {
    'http': f'socks5://{ip}:{port}',
    'https': f'socks5://{ip}:{port}',
}

def print_ip(proxy = False):
    
    if proxy:
        return requests.get(url, proxies=proxies).text
    else:
        return requests.get(url).text


def start_tor():
    # register_logger(True)
    with TorClient().create_circuit(hops_count=hops) as circuit, SocksServer(circuit,ip, port ) as socks_srv:
        socks_srv.start()

@retry(
    (requests.exceptions.ConnectionError, 
        ConnectionRefusedError, 
        socks.ProxyConnectionError,
        CircuitExtendError), delay=5, tries=7 )

def till_tor_is_ready():
    print ("checking connection ... ")
    requests.get(url, proxies=proxies)
    print ("connection completed")


import snowballing.TorSiceCar as TorSiceCar

if __name__ =='__main__':

    # tor = TorSiceCar.TorThread(port)
    # tor.start()


    print ('without tor', print_ip())
    print ('with tor', print_ip(proxy=True))


    print ("perparing  scholarly  ")

    proxy_gen = ProxyGenerator()
    success = proxy_gen.SingleProxy(
        http = f'socks5://{ip}:{port}', 
        https = f'socks5://{ip}:{port}')
    scholarly.use_proxy(proxy_gen)

    print ("searching with scholarly  ")
    scholarly.search_single_pub("Carlos Rombaldo")
    # search_query = scholarly.search_pubs('Perception of physical stability and center of mass of 3D objects')
    # scholarly.pprint(next(search_query))


    # search_query = scholarly.search_author('Steven A Cholewiak')
    # first_author_result = next(search_query)
    # scholarly.pprint(first_author_result)

    tor.terminate()








