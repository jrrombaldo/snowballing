
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


 

def paper_metadata_lookup(ris_papers, num_threads, use_tor):
    with ThreadPool(num_threads) as thread_pool:
        for paper in ris_papers:
            task_args = ('search_scholar_by_ris_paper', [paper], paper.get('primary_title'), use_tor,)
            thread_pool.apply_async(task_execution, args=task_args)
        
        thread_pool.close()
        thread_pool.join()


def paper_snowball(num_threads, use_tor, direction, depth):
    with ThreadPool(num_threads) as thread_pool:

        for iter in range (0, depth):
            
            papers = SemanticScholar().get_references_and_citations_from_extracted_papers(direction)
            log.info(f'performing snowballing iteraction {iter} of {depth} on direction {direction}. Papers found {len(papers)}')

            for paper_tuple in papers:
                task_args = ('snowball', [paper_tuple[0], paper_tuple[1]], paper_tuple[1], use_tor,)
                thread_pool.apply_async(task_execution, args=task_args)

            thread_pool.close()
            thread_pool.join()



