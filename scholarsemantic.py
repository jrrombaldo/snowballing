from concurrent.futures import process
import rispy
import requests
import json
from retry import retry
from multiprocessing.pool import ThreadPool
from torpy.http.requests import tor_requests_session
import logging
import os
import threading
import traceback

logging.basicConfig(format="%(asctime)s %(levelname)-7s  %(threadName)-18s - %(message)s")
logging.getLogger().setLevel(logging.FATAL)  # disable imported module logs
log = logging.getLogger("literature_review")
log.setLevel(logging.DEBUG)


def get_internet_ip_addr(http_session):
    return http_session.get("http://ifconfig.me/ip").text


class ScholarSemantic(object):
    def __init__(
        self, http_session=requests.Session(), proxies=None, http_cert_validation=True
    ):
        self.http_session = http_session
        self.proxies = proxies
        self.http_cert_validation = http_cert_validation
        self.headers = {"Content-Type": "application/json"}

    def _search_paper_from_scholar_website(self, title, authors):
        url = f"https://www.semanticscholar.org/api/1/search"

        data = {
            "queryString": title,
            "page": 1,
            "pageSize": 10,
            "sort": "relevance",
            "authors": authors,
            "coAuthors": [],
            "venues": [],
            #    "yearFilter":year
        }

        resp = self.http_session.post(
            url,
            json=data,
            headers=self.headers,
            proxies=self.proxies,
            verify=self.http_cert_validation,
        )
        log.debug(
            f'results+found={resp.json().get("totalResults")}, http_status_code={resp.status_code}, {title}'
        )

        ret = resp.json()
        ret["status_code"] = resp.status_code
        return ret

    def _search_paper_from_scholar_API(self, paper_details):
        returning_fields = "authors,paperId,externalIds,url,title,abstract,venue,year,referenceCount,citationCount,influentialCitationCount,isOpenAccess,fieldsOfStudy,s2FieldsOfStudy"

        scholar_url = f"https://api.semanticscholar.org/graph/v1/paper/search?query={paper_details}&fields={returning_fields}&offset=0&limit=99"

        resp = self.http_session.get(
            scholar_url,
            proxies=self.proxies,
            verify=self.http_cert_validation,
            headers=self.headers,
        )
        log.debug(
             f'results+found={resp.json().get("total")}, http_status_code={resp.status_code}, {paper_details}'
        )

        ret = resp.json()
        ret["status_code"] = resp.status_code
        return ret

    def _find_paper_match_within_scholar_results(self, nvivo_paper, scholar_papers):
        nvivo_authors = self._extract_authors_surname_from_nvivo_authors(
            nvivo_paper.get("first_authors")
        )

        for scholar_paper in scholar_papers:
            # checking if title matches
            if (
                scholar_paper.get("title").lower()
                == nvivo_paper.get("primary_title").lower()
            ):
                # break if any of authors does not match
                for nvivo_author in nvivo_authors:
                    if nvivo_author not in str(scholar_paper.get("authors")):
                        break

                return scholar_paper
        return None

    def _extract_author_name_from_fullname(self, author):
        if ", " in author:
            return author.split(", ")[0]
        else:
            return author.split(" ")[-1]

    def _extract_authors_surname_from_nvivo_authors(self, authors):
        return [self._extract_author_name_from_fullname(author) for author in authors]

    def _result_directory(self):
        result_dir = "./results"
        if not os.path.exists(result_dir):
            os.makedirs(result_dir)
        return result_dir

    def _write_notfound_result(self, status_code, paper_title):
        with open(f"{self._result_directory()}/not_found.txt", "a") as file:
            file.write(f"{status_code} - {paper_title}")
            file.write("\r\n")

    def _write_found_result(self, paper_title, paper_details_json):
        with open(f"{self._result_directory()}/{paper_title}.json", "w") as file:
            file.write(json.dumps(paper_details_json, indent=4, sort_keys=True))

    @retry(Exception, delay=50, tries=5)
    def search_for_paper_on_semanticscholar(self, nvivo_paper):
        paper_found = None
        log.info(f'searching {nvivo_paper.get("primary_title")}')

        resp = self._search_paper_from_scholar_API(nvivo_paper["primary_title"])

        # trigger retry if status code different of 200. (could use assert and AssertionError ...)
        if resp.get("status_code") != 200:
            raise Exception(f"funny status code{resp.get('status_code')}")

        if resp.get("total") and resp.get("total") > 0:
            paper_found = self._find_paper_match_within_scholar_results(
                nvivo_paper, resp.get("data")
            )

        log.debug(
            f" match {'FOUND' if paper_found else 'NOT FOUND'} within {resp.get('total')} result(s) for {nvivo_paper['primary_title']}"
        )

        if paper_found:
            self._write_found_result(nvivo_paper["primary_title"], paper_found)
        else:
            self._write_notfound_result(
                resp.get("status_code"), nvivo_paper["primary_title"]
            )


def thread_task(paper):
    try:
        with tor_requests_session() as tor_session:
            threading.current_thread().name = get_internet_ip_addr(tor_session)

            scholar = ScholarSemantic(tor_session)
            scholar.search_for_paper_on_semanticscholar(paper)
    except Exception:
        log.error(f'something went wrong with paper {paper}\n resulting at {traceback.format_exc()}')



if __name__ == "__main__":
    with open("empirical.ris", "r") as risFile:
        papers = rispy.load(risFile, skip_unknown_tags=False)

        with ThreadPool(25) as thread_pool:
            thread_pool.map(thread_task, papers)
            thread_pool.join()

