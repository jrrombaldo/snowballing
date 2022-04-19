from snowballing.config import config
from snowballing.logging import log
from snowballing import database
from retry import retry
import requests
import torpy
import os
import json
import traceback


class Non200HTTPStatusCode(Exception):
    pass


class SemanticScholar(object):
    def __init__(self, http_session=requests.Session()):
        self.http_session = http_session

    @retry(
        (Non200HTTPStatusCode, 
            requests.exceptions.ConnectionError, 
            requests.exceptions.Timeout,
            requests.exceptions.ConnectTimeout, 
            requests.exceptions.ReadTimeout,
            torpy.circuit.CellTimeoutError,
            torpy.circuit.CircuitExtendError,),
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
            raise Non200HTTPStatusCode(f"funny status code {http_reponse.status_code}")

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

        log.debug(f"[WEB_SEARCH]\tmatch {'FOUND' if paper_id else 'NOT FOUND'} within {http_result.get('totalResults')} result(s), id = {paper_id}")
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

        log.debug(f"[SEACRH_API]\tmatch {'FOUND' if matched_paper else 'NOT FOUND'} within {result.get('total')} result(s), id = {paper_id}")
        return paper_id

    def _extract_paper_details(self, paper_id, paper_title):
        paper_detail =  self.__http_request(
            config["API"]["paper"]["method"],
            config["API"]["paper"]["url"].format(
                paper_id=paper_id,
                fields_to_return=config["API"]["paper"]["fields_to_return"],
            ),
        )

        log.debug(f"[PAPER_API] {'FOUND' if paper_detail else 'NOT FOUND'} paper for {paper_id}")
        return paper_detail
      
    def search_scholar_by_ris_paper(self, ris_paper):
        paper_id = paper_detail = None
        # try:
        paper_id = self._search_paper_from_scholar_API(ris_paper)
        if not paper_id:
            paper_id = self._search_paper_from_scholar_website(ris_paper)

        if not paper_id:
            database.save_paper_not_found_from_ris(ris_paper)
            #  self._write_notfound_result(f'[SEARCH_API]\t{ris_paper.get("primary_title")}')
        else:
            paper_detail = self._extract_paper_details(paper_id, ris_paper.get("primary_title"))
            if paper_detail:
                database.save_paper(paper_id,ris_paper.get("primary_title"), ris_paper, paper_detail, 'RIS', 'FOUND')
            else:
                database.save_paper_details_not_found(ris_paper.get("primary_title"), 'RIS', ris_paper)
        # except:
        #     log.error(f'something went wrong when searching for: \n[{ris_paper}] \n encountered the following error:\n\n{traceback.format_exc()}')
    

    def get_papers_for_snowballing(self, direction):
        return database.get_next_snowball_set()
    

    def snowballing(self, paper_id, paper_title):
        # try:
        if paper_id == None:
            database.save_paper_not_found_from_snowballing(paper_title)
            return

        if database.already_exist(paper_id):
            log.debug(f'[SNOWBALLING] already extracted -> {paper_id}, {paper_title}')
            return

        paper_detail = self._extract_paper_details(paper_id, paper_title)

        if  paper_detail:
            database.save_paper(paper_id, paper_title, None, paper_detail, 'SB', 'FOUND')
        else:
            database.save_paper_details_not_found(paper_title, 'SB', None, paper_id)

        log.debug(f"[SNOWBALLING] {'FOUND' if paper_detail else 'NOT FOUND'} {paper_title}, {paper_id}")
        # except:
        #     log.error(f'encountered the following error on snowballing [{paper_id}], [{paper_title}]:\n\n{traceback.format_exc()}')

    def _extract_author_name_from_fullname(self, author):
        if ", " in author:
            return author.split(", ")[0]
        else:
            return author.split(" ")[-1]

    def _extract_authors_surname_from_ris_authors(self, authors):
        return [self._extract_author_name_from_fullname(author) for author in authors]
