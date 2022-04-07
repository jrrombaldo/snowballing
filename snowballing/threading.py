import threading
import traceback

from retry import retry
from torpy.http.requests import tor_requests_session
from multiprocessing.pool import ThreadPool

from snowballing.logging import log
from snowballing.config import config
from snowballing.semanticscholar import SemanticScholar


def get_internet_ip_addr(http_session):
    return http_session.get(config["http"]["internet_ip_url"]).text

# @retry(Exception, delay=0, tries=15)
# def get_tor_session():
#     """return a working HTTP session and its internet IP address"""

#     with tor_requests_session() as tor_session:
#         threading.current_thread().name = get_internet_ip_addr(tor_session)
#         yield tor_session



def snowball_task(paper_id, paper_title, thread_pool, curr_depth, max_depth, direction, use_tor):
    try:
        if curr_depth == max_depth: return
        references = None

        if use_tor:
            with tor_requests_session() as tor_session:
                threading.current_thread().name = get_internet_ip_addr(tor_session)
                references = SemanticScholar(tor_session).snowball(paper_id, paper_title, direction)
        else:
            references = SemanticScholar().snowball(paper_id, paper_title, direction)

        if references:
            for paper_tuple in references:
                thread_pool.apply_async(snowball_task, (paper_tuple[0], paper_tuple[1], thread_pool, curr_depth+1, max_depth, direction, use_tor))
        return

    except Exception:
        log.error(f"something went wrong with paper_id {paper_id} and title {paper_title}, resulting at following error:\n{traceback.format_exc()}")


def search_paper_task(ris_paper, use_tor):
    try:
        if use_tor:
            with tor_requests_session() as tor_session:
                threading.current_thread().name = get_internet_ip_addr(tor_session)
                SemanticScholar(tor_session).search_scholar_by_ris_paper(ris_paper)
        else:
            SemanticScholar().search_scholar_by_ris_paper(ris_paper)
    except Exception:
        log.error(f"something went wrong with paper {ris_paper}, resulting at following error:\n{traceback.format_exc()}")

 

def lookup_bibliography_metadata(ris_papers, num_threads, use_tor):
    with ThreadPool(num_threads) as thread_pool:
        #  searching for RIS papers
        for paper in ris_papers:
            thread_pool.apply_async(
                search_paper_task, (paper, use_tor)
            ).get(timeout=config['threadpool_thread_timeout'])
        
        thread_pool.close()
        thread_pool.join()
        print (thread_pool)


def snowball_papers(num_threads, use_tor, direction, depth):
    with ThreadPool(num_threads) as thread_pool:
        # performing snowballing ....
        for paper_tuple in SemanticScholar().get_references_and_citations_from_extracted_papers(direction):
            thread_pool.apply_async(
                snowball_task, (paper_tuple[0], paper_tuple[1], thread_pool, 0, depth, direction, use_tor)
            ).get(timeout=config['threadpool_thread_timeout'])

        thread_pool.close()
        thread_pool.join()

