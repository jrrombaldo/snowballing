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
            for sql_cmd in tables.read().split(";"):
                conn.cursor().execute(sql_cmd)
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

def get_summary():
    conn =  prepare_db()

    cur = conn.cursor()
    result = cur.execute('SELECT sum(reference) AS total_references, sum(citations) as total_citations FROM snowballing').fetchone()
    total_references = result[0]
    total_citations = result[1]

    result = cur.execute("SELECT stat, count (*) FROM papers WHERE source ='SB' GROUP BY stat ORDER BY 1").fetchall()
    snowballing_found = result[0][1]
    snowballing_not_found = result[1][1]

    result = cur.execute("SELECT stat, count (*) FROM papers WHERE source ='RIS' GROUP BY stat ORDER BY 1").fetchall()
    ris_found = result[0][1]
    ris_not_found = result[1][1]

    log.info(f"\
            \r\n\tpaper found \t\t= {ris_found}\
            \r\n\tpapers NOT found \t= {ris_not_found} \
            \r\n\treferences \t\t= {total_references}\
            \r\n\tcitations \t\t= {total_citations}\
            \r\n\tsnowballing found \t= {snowballing_found}\
            \r\n\tsnowballing NOT found \t= {snowballing_not_found}\r\n")

    result = cur.execute("SELECT reference, citations, title FROM snowballing").fetchall()
    for paper in result:
        print (f"\t{paper[0]}\t{paper[1]}\t{paper[2]}")
    
    