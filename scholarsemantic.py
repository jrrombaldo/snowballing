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
from pprint import pprint


log_format_str = "%(asctime)s %(levelname)-7s  %(threadName)-18s - %(message)s"
logging.basicConfig(format=log_format_str)

logging.getLogger().setLevel(logging.FATAL)  # disable imported module logs

log = logging.getLogger("scholar-semantic")
log.setLevel(logging.DEBUG)

log.addHandler(logging.FileHandler("scholar-semantic.log"))
for log_handler in log.handlers:
    log_handler.setFormatter(logging.Formatter(log_format_str))


def get_internet_ip_addr(http_session):
    return http_session.get("http://ifconfig.me/ip").text


class ScholarSemantic(object):
    def __init__(
        self, http_session=requests.Session(), proxies=None, http_cert_validation=True
    ):
        self.http_session = http_session
        self.proxies = proxies
        self.http_cert_validation = http_cert_validation

    @retry(Exception, delay=60, tries=4)
    def http_request(self, method, url, json_body=None):
        # log.debug(f"executing HTTP {method} on {url} with body {json_body}")

        headers = {"Content-Type": "application/json"}

        http_reponse = self.http_session.request(
            method,
            url=url,
            json=json_body,
            headers=headers,
            verify=self.http_cert_validation,
            proxies=self.proxies,
        )

        if http_reponse.status_code != 200:
            raise Exception(f"funny status code{http_reponse.get('status_code')}")

        json_return = http_reponse.json()
        json_return["status_code"] = http_reponse.status_code

        # log.debug(f"returned {json_return}")
        return json_return

    def search_paper_from_scholar_website(self, nvivo_paper):
        scholar_website_url = f"https://www.semanticscholar.org/api/1/search"

        data = {
            "queryString": nvivo_paper["primary_title"],
            "page": 1,
            "pageSize": 10,
            "sort": "relevance",
            # "authors": self._extract_authors_surname_from_nvivo_authors(
            #     nvivo_paper.get("first_authors")
            # ),
            "authors": [],
            "coAuthors": [],
            "venues": [],
            #    "yearFilter":year
        }

        http_result = self.http_request("POST", scholar_website_url, data)

        log.debug(
            f"Results_found={http_result.get('totalResults')}, http_status_code={http_result.get('status_code')}, {nvivo_paper['primary_title']}"
        )

        # TODO search for matching among results
        self._write_found_result("_" + nvivo_paper["primary_title"], http_result)
        return http_result

    def search_paper_from_scholar_API(self, nvivo_paper):
        returning_fields = "authors,paperId,externalIds,url,title,abstract,venue,year,referenceCount,citationCount,influentialCitationCount,isOpenAccess,fieldsOfStudy,s2FieldsOfStudy"
        scholar_url = f"https://api.semanticscholar.org/graph/v1/paper/search?query={nvivo_paper['primary_title']}&fields={returning_fields}&offset=0&limit=99"

        result = self.http_request("GET", scholar_url)

        if not result.get("total") or result.get("total") < 1:
            return None  # search returned no result

        # checking for matches among returned papers
        matched_paper = None

        nvivo_authors = self._extract_authors_surname_from_nvivo_authors(
            nvivo_paper.get("first_authors")
        )

        for scholar_paper in result.get("data"):
            # search for a papers (among result) tha that maches both title and authors
            if scholar_paper.get("title").lower() == nvivo_paper.get(
                "primary_title"
            ).lower() and all(
                nvivo_author.lower() in str(scholar_paper.get("authors")).lower()
                for nvivo_author in nvivo_authors
            ):
                matched_paper = scholar_paper
                break

        log.debug(
            f"match {'FOUND' if matched_paper else 'NOT FOUND'} within {result.get('total')} result(s) for {nvivo_paper['primary_title']}"
        )

        if matched_paper:
            self._write_found_result(nvivo_paper["primary_title"], matched_paper)
            return matched_paper
        else:
            self._write_notfound_result(
                result.get("status_code"), nvivo_paper["primary_title"]
            )
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


def thread_task(paper):
    try:
        with tor_requests_session() as tor_session:
            threading.current_thread().name = get_internet_ip_addr(tor_session)
            scholar = ScholarSemantic(tor_session)
            scholar.search_paper_from_scholar_API(paper)
            scholar.search_paper_from_scholar_website(paper)

    except Exception:
        log.error(
            f"something went wrong with paper {paper}\n resulting at {traceback.format_exc()}"
        )


if __name__ == "__main__":

    THREAD_POOL_SIZE = 75
    with open("scoped.ris", "r") as risFile:
        papers = rispy.load(risFile, skip_unknown_tags=False)
        log.info(f"starting execution with {THREAD_POOL_SIZE} threads ...")
        with ThreadPool(THREAD_POOL_SIZE) as thread_pool:
            thread_pool.map(thread_task, papers)
            thread_pool.join()

    # with open("test.ris", "r") as risFile:
    #     for paper in rispy.load(risFile, skip_unknown_tags=False):
    #         scholar = ScholarSemantic(requests.session())
    #         scholar.search_paper_from_scholar_API(paper)
    #         # scholar.search_paper_from_scholar_website(paper)


"""
change both query by API and website to return the paperID, then have a method (API) to extract the paper details from ID
lastly, read and update NVIVO CSV to add the details back.
"""
