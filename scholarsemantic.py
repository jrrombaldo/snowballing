from datetime import date
import logging
from pprint import pprint
from time import sleep
import rispy
import requests
import json
from torpy.http.requests import tor_requests_session
from retry import retry
from multiprocessing.pool import ThreadPool
import threading
from torpy.http.requests import tor_requests_session

import queue
papers_queue = queue.Queue()



# class ScholaSemantic(object):
#      def __init__(self, http_session):
#          self.sess = 










def search_paper_from_site(title, year, authors):
    fields = 'authors,paperId,externalIds,url,title,abstract,venue,year,referenceCount,citationCount,influentialCitationCount,isOpenAccess,fieldsOfStudy,s2FieldsOfStudy'
    url = f'https://www.semanticscholar.org/api/1/search'
    data = {
           "queryString":title,
           "page":1,
           "pageSize":10,
           "sort":"relevance",
           "authors":authors,
           "coAuthors":[],
           "venues":[],
        #    "yearFilter":year
        }
    headers = {"Content-Type": "application/json"}
    resp = requests.post(url, json = data, headers=headers, proxies=proxies,  verify=False)
    print (f'{resp.json().get("totalResults")}\t-\t{resp.status_code}\t-\t{title}')

    return resp.json()




def search_paper_from_API(paper_details, session=None):
    fields = 'authors,paperId,externalIds,url,title,abstract,venue,year,referenceCount,citationCount,influentialCitationCount,isOpenAccess,fieldsOfStudy,s2FieldsOfStudy'
    url = f'https://api.semanticscholar.org/graph/v1/paper/search?query={paper_details}&fields={fields}&offset=0&limit=99'
    if session:
        resp = session.get(url)
    else:
        resp = requests.get(url)
        # with tor_requests_session() as session:
        #     resp = session.get(url)
    print (f'{resp.json().get("total")}\t-\t{resp.status_code}\t-\t{paper_details}')

    ret = resp.json()
    ret["status_code"] = resp.status_code

    return ret

    # with tor_requests_session() as session:
    #     return session.get(url).json()


def extract_author_surname(author):
    if ", " in author:
        return author.split(", ")[0]
    else:
        return author.split(" ")[-1]

def get_authors_surname_from_nvivo_authors(authors): 
    return [extract_author_surname(author) for author in authors]
    


def find_match_within_search_results(nvivo_paper, scholar_papers):
    nvivo_authors = get_authors_surname_from_nvivo_authors(nvivo_paper.get("first_authors"))

    for scholar_paper in scholar_papers:
        # checking if title matches
        if scholar_paper.get('title').lower() == nvivo_paper.get("primary_title").lower():
            # break if any of authors does not match
            for nvivo_author in nvivo_authors:
                if nvivo_author not in str(scholar_paper.get('authors')):
                    break
            
            return scholar_paper
    return None


@retry(Exception, delay=50, tries=5 )
def search_for_paper_on_semanticscholar(nvivo_paper, session=None):
    print (f'searching for {nvivo_paper.get("primary_title")}')
    paper_found = None

    resp = search_paper_from_API(nvivo_paper["primary_title"], session)# " " + paper["year"] + " "+ " ".join(authors) )

    if resp.get("status_code") != 200: raise Exception(f"funny status code{resp.get('status_code')}")

    if resp.get("total") and resp.get("total") > 0: 
        paper_found = find_match_within_search_results(nvivo_paper, resp.get("data"))

    print (f" {'found' if paper_found else 'NOT FOUND'} a match within {resp.get('total')} result(s)\n\t{nvivo_paper['primary_title']}\n")

    if paper_found:
        with open(f"results/{nvivo_paper['primary_title']}.json", 'w') as file:
            file.write(json.dumps(paper_found, indent=4, sort_keys=True))
            # print ("\t",[ author.get('name') for author in paper_found.get('authors')])
            # print ("\t",get_authors_surname_from_nvivo_authors(nvivo_paper.get("first_authors")))
    else:
        with open(f"results/not_found.txt", 'a') as file:
            file.write(f"{resp.get('status_code')} - {nvivo_paper['primary_title']}")
            file.write('\n')




# def thread_task ():
#     with tor_requests_session() as session:
#         print (f"thread ready, internet ip = {session.get('http://ifconfig.me/ip').text}")
#         while True:
#             paper = papers_queue.get()
#             # match = search_for_paper_on_semanticscholar(paper, session)
#             papers_queue.task_done()

# for x in range (1,50):
#     threading.Thread(target=thread_task, daemon=True).start()


with open('empirical.ris','r') as risFile:
    papers = rispy.load(risFile, skip_unknown_tags=False)
  
    for paper in papers:
        print ("="*100)
        sleep(20)
        match = search_for_paper_on_semanticscholar(paper)
        
    #     papers_queue.put(paper)

#     with ThreadPool(75) as pool:
#         pool.map(search_for_paper_on_semanticscholar, papers)
       

# papers_queue.join()
    



# threading, 
# logging
# read and write into nvivo csv