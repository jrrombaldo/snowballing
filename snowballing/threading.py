import threading
import traceback
from torpy.http.requests import tor_requests_session
from multiprocessing.pool import ThreadPool

from snowballing.logging import log
from snowballing.config import config
from snowballing.scholarsemantic import ScholarSemantic


def get_internet_ip_addr(http_session):
    return http_session.get(config["http"]["internet_ip_url"]).text

def thread_task(paper):
    try:
        with tor_requests_session() as tor_session:
            threading.current_thread().name = get_internet_ip_addr(tor_session)
            scholar = ScholarSemantic(tor_session)
            scholar.search_scholar_by_nvivo_paper(paper)

    except Exception:
        log.error(
            f"something went wrong with paper {paper}\n resulting at {traceback.format_exc()}"
        )


def start_threadpoll(papers, threadpool_size = config["threadpool_default_size"]):
    log.info(f"starting execution with {threadpool_size} threads ...")
    with ThreadPool(threadpool_size) as thread_pool:
        thread_pool.map(thread_task, papers)