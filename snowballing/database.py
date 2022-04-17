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

def save_paper_not_found_from_ris(ris_paper):
    save_paper(None, ris_paper.get("primary_title"), ris_paper, None, 'RIS', 'NOT_FOUND')

def save_paper_not_found_from_snowballing(paper_title):
    save_paper(None, paper_title, None, None, 'SB', 'NOT_FOUND')

def save_paper_not_found_from_ris(ris_paper):
    save_paper(None, ris_paper.get("primary_title"), ris_paper, None, 'RIS', 'NOT_FOUND')

def save_paper_details_not_found(title, source, ris=None, paper_id=None):
    save_paper(paper_id, title, ris, None, source, 'DETAILS_NOT_FOUND')


def already_exist(paper_id):
    sql = 'SELECT id FROM papers WHERE id = ?'
    conn =  prepare_db()
    cur = conn.cursor()
    result = cur.execute(sql, [paper_id])
    found = not result.fetchone() is None
    conn.close()
    return found 


def get_all_papers():
    sql = 'SELECT paper FROM papers WHERE paper is not null'
    conn =  prepare_db()
    # conn.row_factory = lambda cursor, row: row[0]
    cur = conn.cursor()
    result = cur.execute(sql)
    results = [json.loads(paper[0]) for paper in result.fetchall()]
    conn.close()
    return results

