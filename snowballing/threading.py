
import threading
import traceback

from retry import retry
from torpy.http.requests import tor_requests_session
from multiprocessing.pool import ThreadPool

from snowballing.logging import log
from snowballing.config import config
from snowballing.semanticscholar import SemanticScholar

from contextlib import contextmanager

def get_internet_ip_addr(http_session):
    return http_session.get(config["http"]["internet_ip_url"]).text


@contextmanager
@retry(Exception, delay=15, tries=10)
def get_tor_session():
    """return a working HTTP session and its internet IP address"""
    log.debug("establishing TOR circuit ...")

    with tor_requests_session() as tor_session:
        internet_ip = get_internet_ip_addr(tor_session)
        log.debug(f"thread {threading.current_thread().name} changing to {internet_ip}")
        threading.current_thread().name = internet_ip
        yield tor_session


def task_execution (func_name, func_args, paper_title, use_tor):
    try:
        if use_tor:
            with get_tor_session() as tor_session:
                getattr(SemanticScholar(), func_name)(*func_args)
        else:
            threading.current_thread().name = f'{paper_title[:80]:80}'
            getattr(SemanticScholar(), func_name)(*func_args)

    except Exception:
        log.error(f"SOMETHING WENT WRONG ON [{func_name}] with parameters [{func_args}], resulting at:\n{traceback.format_exc()}")
        update_progress_bar_failed()


def printProgressBar (iteration, total, prefix = '', suffix = '', decimals = 1, length = 100, fill = '█', printEnd = "\r"):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
        printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end = printEnd)
    # Print New Line on Complete
    if iteration == total: 
        print()


total = 0
completed = 0
failed = 0
def update_progress_bar(test=None):
    global completed
    completed += 1
    printProgressBar(completed, total, prefix = 'Progress:', suffix = f'Complete ({completed}/{total}), Failed={failed}', length = 80)
    
def update_progress_bar_failed():
    global failed
    failed =+ 1
    update_progress_bar()


def paper_metadata_lookup(ris_papers, num_threads, use_tor):
    print ('Looking up for metadata ...')
    global total
    total =  len (ris_papers)
    with ThreadPool(num_threads) as thread_pool:
        for paper in ris_papers:
            task_args = ('search_scholar_by_ris_paper', [paper], paper.get('primary_title'), use_tor,)
            thread_pool.apply_async(task_execution, args=task_args, callback=update_progress_bar, error_callback=update_progress_bar_failed)
        
        thread_pool.close()
        thread_pool.join()
        


def paper_snowball(num_threads, use_tor, direction, depth):
    print ('Snowballing ...')
    global total
    with ThreadPool(num_threads) as thread_pool:
        
        for iter in range (0, depth):
            
            papers = SemanticScholar().get_papers_for_snowballing(direction)
            total =  len(papers)
            log.info(f'performing snowballing iteraction {iter} of {depth} on direction {direction}. Papers found {len(papers)}')

            for paper_tuple in papers:
                task_args = ('snowballing', [paper_tuple[0], paper_tuple[1]], paper_tuple[1], use_tor,)
                thread_pool.apply_async(task_execution, args=task_args, callback=update_progress_bar, error_callback=update_progress_bar_failed)

            thread_pool.close()
            thread_pool.join()



