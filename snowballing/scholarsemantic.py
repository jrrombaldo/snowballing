from snowballing.config import config
from snowballing.logging import log
from retry import retry
import requests
import os
import json


class ScholarSemantic(object):
    def __init__(self, http_session=requests.Session()):
        self.http_session = http_session

    @retry(
        Exception,
        delay=config["http"]["retry_delay"],
        tries=config["http"]["retry_attempts"],
    )
    def __http_request(self, method, url, json_body=None):
        http_reponse = self.http_session.request(
            method,
            url=url,
            json=json_body,
            headers=config["http"]["headers"],
            verify=config["http"]["cert_validation"],
            proxies=config["http"]["proxies"],
        )

        if http_reponse.status_code != 200:
            raise Exception(f"funny status code {http_reponse.status_code}")

        json_return = http_reponse.json()
        json_return["status_code"] = http_reponse.status_code

        return json_return

    def _search_paper_from_scholar_website(self, ris_paper):
        data = config["WEBSITE"]["request_body"]
        data["queryString"] = ris_paper["primary_title"]

        http_result = self.__http_request(
            config["WEBSITE"]["method"], config["WEBSITE"]["url"], data
        )

        paper_id = None
        if http_result.get("totalResults") and http_result.get("totalResults") > 0:
            paper_id =  http_result.get("results")[0].get("id")

        log.debug(f"[WEB]\tmatch {'FOUND' if paper_id else 'NOT FOUND'} within {http_result.get('totalResults')} result(s) for {ris_paper['primary_title']}, id = {paper_id}")
        return paper_id

    def _search_paper_from_scholar_API(self, ris_paper):
        result = self.__http_request(
            config["API"]["search"]["method"],
            config["API"]["search"]["url"].format(
                query=ris_paper["primary_title"],
                fields_to_return=config["API"]["search"]["fields_to_return"],
            ),
        )

        matched_paper = None
        # checking for matches among returned papers
        if result.get("total") and result.get("total") > 0:
            ris_authors = self._extract_authors_surname_from_ris_authors(
                ris_paper.get("first_authors")
            )

            for scholar_paper in result.get("data"):
                # search for a papers (among result) tha that maches both title and authors
                if scholar_paper.get("title").lower() == ris_paper.get(
                    "primary_title"
                ).lower() and all(
                    ris_author.lower() in str(scholar_paper.get("authors")).lower()
                    for ris_author in ris_authors
                ):
                    matched_paper = scholar_paper
                    break

        paper_id = None
        if matched_paper: paper_id = matched_paper.get("paperId")

        log.debug(f"[API]\tmatch {'FOUND' if matched_paper else 'NOT FOUND'} within {result.get('total')} result(s) for {ris_paper['primary_title']}, id = {paper_id}")
        return paper_id

    def _get_paper_details(self, scholar_paper_id):
        paper_details =  self.__http_request(
            config["API"]["paper"]["method"],
            config["API"]["paper"]["url"].format(
                paper_id=scholar_paper_id,
                fields_to_return=config["API"]["paper"]["fields_to_return"],
            ),
        )
        log.debug(f"[details] FOUND papers details for {scholar_paper_id}")
        return paper_details

    def snowballing_backward(self, paper_id):
        print("snowballing_backward not there yet")

    def snowballing_forward(self, paper_id):
        print("snowballing_forward not there yet")
    
    def snowballing_bidrectional(self, paper_id):
        print("snowballing_bidrectional not there yet")


    def search_scholar_by_ris_paper(self, ris_paper):
        paper_id = paper_detail = None

        paper_id = self._search_paper_from_scholar_API(ris_paper)
        if not paper_id:
            paper_id = self._search_paper_from_scholar_website(ris_paper)

        if paper_id:
            paper_detail = self._get_paper_details(paper_id)

        if paper_id and paper_detail:
            self._write_found_result(ris_paper.get("primary_title"), paper_detail)
        else:
            self._write_notfound_result(ris_paper.get("primary_title"))

    def _extract_author_name_from_fullname(self, author):
        if ", " in author:
            return author.split(", ")[0]
        else:
            return author.split(" ")[-1]

    def _extract_authors_surname_from_ris_authors(self, authors):
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
        with open(f"{self._result_directory()}/{paper_title.lower()}.json", "a") as file:
            file.write(json.dumps(paper_details_json, indent=4, sort_keys=True))
