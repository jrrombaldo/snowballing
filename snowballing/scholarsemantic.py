from snowballing.config import config
from snowballing.logging import log
from retry import retry
import requests
from requests import exceptions
import os
import json


class Non200HTTPStatusCode(Exception):
    pass


class ScholarSemantic(object):
    def __init__(self, http_session=requests.Session()):
        self.http_session = http_session

    @retry(
        (Non200HTTPStatusCode, 
            requests.exceptions.ConnectionError, 
            requests.exceptions.Timeout, 
            requests.exceptions.ConnectTimeout, 
            requests.exceptions.ReadTimeout),
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

    def extract_paper_details(self, paper_id, paper_title):
        log.debug(f"extracting paper {paper_id}, {paper_title}")
        paper_detail =  self.__http_request(
            config["API"]["paper"]["method"],
            config["API"]["paper"]["url"].format(
                paper_id=paper_id,
                fields_to_return=config["API"]["paper"]["fields_to_return"],
            ),
        )

        if  paper_detail:
            log.error(f'Paper NOT FOUND {paper_id}')
            self._write_found_result(paper_id, paper_detail)
        else:
            self._write_notfound_result(paper_title)

        log.debug(f"[details] {'FOUND' if paper_detail else 'NOT FOUND'} papers details for {paper_id}")

        return paper_detail

        
    def search_scholar_by_ris_paper(self, ris_paper):
        paper_id = paper_detail = None

        paper_id = self._search_paper_from_scholar_API(ris_paper)
        if not paper_id:
            paper_id = self._search_paper_from_scholar_website(ris_paper)

        if not paper_id:
            self._write_notfound_result(ris_paper.get("primary_title"))
        else:
            self.extract_paper_details(paper_id, ris_paper.get("primary_title"))



    def get_references_and_citations_to_snowball(self, paper_detail, direction):
        where_to_look = []
        if direction == 'both' or 'forward': where_to_look.append('citations')
        if direction == 'both' or 'forward': where_to_look.append('references') 
        
        papers_to_snowball = []
        for look_at in where_to_look:
            for ref in paper_detail.get(look_at):
                if not ref.get('paperId'): 
                    self._write_notfound_result(ref.get('title'))
                else:
                    papers_to_snowball.append((ref.get('paperId'),ref.get('title') ))
        return papers_to_snowball



    def get_extracted_papers_to_snowball(self, direction):
        papers = []
        for paper_file in os.listdir(self._result_directory()):
            if paper_file.endswith(".json"):
                with open(os.path.join(self._result_directory(),paper_file)) as json_paper:
                    papers.extend(self.get_references_and_citations_to_snowball(json.load(json_paper), direction))
        
        return papers

    
    def snowball(self, paper_id, paper_title, direction):
        log.debug(f'snowballing for {paper_id}, {paper_title}, direction = {direction}')
        if paper_id == None:
            self._write_notfound_result(paper_title)
            return

        if os.path.exists(os.path.join(self._result_directory(),f'{paper_id}.json')):
            log.debug(f'already extracted -> {paper_id}, {paper_title}')
            return

        paper_detail = self.extract_paper_details(paper_id, paper_title)

        if  paper_detail:
            references = self.get_references_and_citations_to_snowball(paper_detail, direction)
            log.debug(f'found {len(references)} references for {paper_id}, {paper_title}')
        else:
            return
        

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



