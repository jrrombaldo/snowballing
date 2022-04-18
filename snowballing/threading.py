
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


def snowball_task(paper_id, paper_title, direction, use_tor):
    try:
        if use_tor:
            with get_tor_session() as tor_session:
                references = SemanticScholar(tor_session).snowball(paper_id, paper_title, direction)
        else:
            threading.current_thread().name = f'{paper_title[:80]:80}'
            references = SemanticScholar().snowball(paper_id, paper_title, direction)


    except Exception:
        log.error(f"something went wrong with paper_id {paper_id} and title {paper_title}, resulting at following error:\n{traceback.format_exc()}")


def search_paper_task(ris_paper, use_tor):
    try:
        if use_tor:
            with get_tor_session() as tor_session:
                SemanticScholar(tor_session).search_scholar_by_ris_paper(ris_paper)
        else:
            threading.current_thread().name = f'{ris_paper.get("primary_title")[:80]:80}'
            SemanticScholar().search_scholar_by_ris_paper(ris_paper)
    except Exception:
        log.error(f"something went wrong with paper {ris_paper}, resulting at following error:\n{traceback.format_exc()}")

 

def lookup_bibliography_metadata(ris_papers, num_threads, use_tor):
    with ThreadPool(num_threads) as thread_pool:
        #  searching for RIS papers
        for paper in ris_papers:
            thread_pool.apply_async(
                search_paper_task, (paper, use_tor, )
            )
        
        thread_pool.close()
        thread_pool.join()

def snowball_papers(num_threads, use_tor, direction, depth):
    with ThreadPool(num_threads) as thread_pool:

        for iter in range (0, depth):
            
            papers = SemanticScholar().get_references_and_citations_from_extracted_papers(direction)
            log.info(f'performing snowballing iteraction {iter} of {depth} on direction {direction}. Papers found {len(papers)}')

            for paper_tuple in papers:
                thread_pool.apply_async(
                    snowball_task, (paper_tuple[0], paper_tuple[1], direction, use_tor,)
                )
            thread_pool.close()
            thread_pool.join()



