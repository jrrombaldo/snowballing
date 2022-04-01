import rispy
import threading
import traceback
from torpy.http.requests import tor_requests_session
from multiprocessing.pool import ThreadPool

from snowballing.logging import log
from snowballing.config import config
from snowballing.scholarsemantic import ScholarSemantic


def get_internet_ip_addr(http_session):
    return http_session.get(config["http"]["internet_ip_url"]).text

def search_paper(paper, tor):
    try:
        if tor:
            with tor_requests_session() as tor_session:
                threading.current_thread().name = get_internet_ip_addr(tor_session)
                scholar = ScholarSemantic(tor_session)
                scholar.search_scholar_by_ris_paper(paper)
        else:
            scholar = ScholarSemantic()
            scholar.search_scholar_by_ris_paper(paper)


    except Exception:
        log.error(
            f"something went wrong with paper {paper}\n resulting at {traceback.format_exc()}"
        )

def snowballing(paper, tor):
    try:
        if tor:
            with tor_requests_session() as tor_session:
                threading.current_thread().name = get_internet_ip_addr(tor_session)
                scholar = ScholarSemantic(tor_session)
                scholar.search_scholar_by_ris_paper(paper)
        else:
            scholar = ScholarSemantic()
            scholar.search_scholar_by_ris_paper(paper)

    except Exception:
        log.error(
            f"something went wrong with paper {paper}\n resulting at {traceback.format_exc()}"
        )

def start_threadpoll(papers, tor, threadpool_size):
    log.info(f"starting execution with {threadpool_size} threads ...")
    with ThreadPool(threadpool_size) as thread_pool:
        # thread_pool.map(search_paper, papers, True)
        for paper in papers:
            thread_pool.apply_async(search_paper, (paper, tor,))
        
        thread_pool.close()
        thread_pool.join()



if __name__ == "__main__":
    papers = rispy.load(open("test.ris"), skip_unknown_tags=False)
    start_threadpoll(papers, True, 75)

