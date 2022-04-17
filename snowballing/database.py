import sqlite3
import os
import json
from snowballing.config import config
from snowballing.logging import log


def prepare_db():
    db_existed = os.path.exists(config["db_file"])
    conn = sqlite3.connect(config["db_file"])
    if not db_existed:
        with open('./tables.sql') as tables:
            conn.cursor().execute(tables.read())
            conn.commit()

    return conn


def save_paper(paper_id, title, ris_paper, scholar_paper, source, status = None):
    if  already_exist(paper_id):
        log.error(f'paper already exist, not savaing -> {title}')
        pass

    sql = 'insert into papers (id, title, ris, paper, source, stat) values (?, ? ,?, ?, ?, ?)'
    params  = [paper_id, 
        title, 
        json.dumps(ris_paper), 
        json.dumps(scholar_paper), 
        source, 
        status]

    conn = prepare_db()
    conn.cursor().execute(sql, params)
    conn.commit()
    conn.close()

def save_paper_not_found(ris_paper):
    save_paper(None, ris_paper.get("primary_title"), ris_paper, None, 'RIS', 'NOT_FOUND')

def save_paper_details_not_found(title, source, ris=None):
    save_paper(None, title, ris, None, source, 'DETAILS_NOT_FOUND')


def already_exist(paper_id):
    sql = 'SELECT id FROM papers WHERE id = ?'
    conn =  prepare_db()
    cur = conn.cursor()
    result = cur.execute(sql, [paper_id])
    found = not result.fetchone() is None
    conn.close()
    return found 




    







import rispy
def get_papers_from_ris(ris_file):
    return rispy.load(ris_file, skip_unknown_tags=False)


print (already_exist("no_id"))
print (already_exist('blad'))
print (already_exist(None))


# for paper in get_papers_from_ris(open('./scoped.ris')):
#     save_article(
#         "no_id",
#         paper.get("primary_title"),
#         paper,
#         None,
#         "RIS",
#         'FOUND'
#     )


# conn =  prepare_db()
# cur = conn.cursor()
# cur.execute('select * from papers');
# print (cur.arraysize)