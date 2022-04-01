from util.config import config
from util.logging import log
import retry
import requests
import os
import json

class ScholarSemantic(object):
    def __init__(self, http_session=requests.Session()):
        self.http_session = http_session

    # @retry(
    #     Exception,
    #     delay=config["http"]["retry_delay"],
    #     tries=config["http"]["retry_attempts"],
    # )
    def __http_request(self, method, url, json_body=None):
        # log.debug(f"executing HTTP {method} on {url} with body {json_body}")

        http_reponse = self.http_session.request(
            method,
            url=url,
            json=json_body,
            headers=config["http"]["headers"],
            verify=config["http"]["cert_validation"],
            proxies=config["http"]["proxies"],
        )

        if http_reponse.status_code != 200:
            raise Exception(f"funny status code{http_reponse.get('status_code')}")

        json_return = http_reponse.json()
        json_return["status_code"] = http_reponse.status_code

        # log.debug(f"returned {json_return}")
        return json_return

    def _search_paper_from_scholar_website(self, nvivo_paper):
        data = config["WEBSITE"]["request_body"]
        data["queryString"] = nvivo_paper["primary_title"]

        http_result = self.__http_request(
            config["WEBSITE"]["method"], config["WEBSITE"]["url"], data
        )

        log.debug(
            f"[WEB]\tmatch {'FOUND' if http_result.get('totalResults') > 0 else 'NOT FOUND'} within {http_result.get('totalResults')} result(s) for {nvivo_paper['primary_title']}"
        )

        if http_result.get("totalResults") and http_result.get("totalResults") > 0:
            return http_result.get("results")[0].get("id")
        else:
            return None

    def _search_paper_from_scholar_API(self, nvivo_paper):
        result = self.__http_request(
            config["API"]["search"]["method"],
            config["API"]["search"]["url"].format(
                query=nvivo_paper["primary_title"],
                fields_to_return=config["API"]["search"]["fields_to_return"],
            ),
        )

        matched_paper = None
        # checking for matches among returned papers
        if result.get("total") and result.get("total") > 0:
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
            f"[API]\tmatch {'FOUND' if matched_paper else 'NOT FOUND'} within {result.get('total')} result(s) for {nvivo_paper['primary_title']}"
        )

        if matched_paper:
            return matched_paper.get("paperId")
        else:
            return None

    def get_paper_details(self, scholar_paper_id):
        return self.__http_request(
            config["API"]["paper"]["method"],
            config["API"]["paper"]["url"].format(
                paper=scholar_paper_id,
                fields_to_return=config["API"]["paper"]["fields_to_return"],
            ),
        )

    def search_scholar_by_nvivo_paper(self, nvivo_paper):
        paper_id = paper_detail = None

        paper_id = self._search_paper_from_scholar_API(nvivo_paper)
        if not paper_id:
            paper_id = self._search_paper_from_scholar_website(nvivo_paper)

        if paper_id:
            paper_detail = self._write_found_result(
                nvivo_paper.get("primary_title"), paper_id
            )

        if paper_id and paper_detail:
            self._write_found_result(nvivo_paper.get("primary_title"), paper_detail)
        else:
            self._write_notfound_result(nvivo_paper.get("primary_title"))

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

    def _write_notfound_result(self, paper_title):
        with open(f"{self._result_directory()}/not_found.txt", "a") as file:
            file.write(f"{paper_title}\r\n")

    def _write_found_result(self, paper_title, paper_details_json):
        with open(f"{self._result_directory()}/{paper_title}.json", "a") as file:
            file.write(json.dumps(paper_details_json, indent=4, sort_keys=True))