import rispy
import threading
import traceback
import argparse
from torpy.http.requests import tor_requests_session
from multiprocessing.pool import ThreadPool

from snowballing.logging import log
from snowballing.config import config
from snowballing.scholarsemantic import ScholarSemantic


def parse_cli_args():
    parser = argparse.ArgumentParser(
        description=' Snowballing and metadata searcing...',
        epilog='happy research! :)')

    parser.add_argument('--direction', 
        metavar='<snowballing approach>',
        required=False,
        default='both',
        choices=['backward', 'forward', 'both'],
        help='type of snowballing ...'
    )

    parser.add_argument("--depth",
        help=f'Snowballing depth ...',
        metavar='depth number', 
        action='store',
        required=False,
        type=int,
        default=1)
    
    parser.add_argument("--threads",
        help=f'Number of threads (one thread per paper). Default ({config["threadpool_default_size"]})',
        metavar='<number of threads>', 
        action='store',
        required=False,
        type=int,
        default=config["threadpool_default_size"])

    parser.add_argument('--tor', 
        help='use TOR networks, which thread will create a connection and will have different internet IP',
        action='store_true', 
        required=False,
        default=False)

    parser.add_argument('ris_file', 
        metavar='<RIS file>', 
        type=argparse.FileType('r'),
        help='RIS format file containing bibliography')

    args = parser.parse_args()
    return args


def get_papers_from_ris(ris_file):
    return rispy.load(ris_file, skip_unknown_tags=False)



def get_internet_ip_addr(http_session):
    return http_session.get(config["http"]["internet_ip_url"]).text


# def snowball_task(paper_id, paper_title, thread_pool, curr_depth, max_depth, direction, use_tor):
#     try:
#         if use_tor:
#             with tor_requests_session() as tor_session:
#                 threading.current_thread().name = get_internet_ip_addr(tor_session)
#                 scholar = ScholarSemantic(tor_session)
#                 paper_id = getattr(scholar, func_name)(ris_paper)
#         else:
#             scholar = ScholarSemantic()
#             getattr(scholar, func_name)(ris_paper)

#     except Exception:
#         log.error(f"something went wrong with function {func_name} and paper {ris_paper}, resulting at following error:\n{traceback.format_exc()}")

def search_paper_task(func_name, ris_paper, use_tor):
    try:
        if use_tor:
            with tor_requests_session() as tor_session:
                threading.current_thread().name = get_internet_ip_addr(tor_session)
                scholar = ScholarSemantic(tor_session)
                paper_id = getattr(scholar, func_name)(ris_paper)
        else:
            scholar = ScholarSemantic()
            getattr(scholar, func_name)(ris_paper)

    except Exception:
        log.error(f"something went wrong with function {func_name} and paper {ris_paper}, resulting at following error:\n{traceback.format_exc()}")



if __name__ == "__main__":
    args = parse_cli_args()
    print (args)

    # func_name = None
    # if args.module == 'search':                                        func_name = 'search_scholar_by_ris_paper'
    # if args.module == 'snowballing' and args.approach == 'backward' :  func_name = 'snowballing_backward'
    # if args.module == 'snowballing' and args.approach == 'forward' :   func_name = 'snowballing_forward'
    # if args.module == 'snowballing' and args.approach == 'both' :      func_name = 'snowballing_bidrectional'

    func_name = 'search_scholar_by_ris_paper'


    log.info(f"starting execution with {args.threads} threads and file {args.ris_file.name} {'using' if args.tor else 'not'} tor networks")
    
    
    with ThreadPool(args.threads) as thread_pool:
        
        #  searching for RIS papers
        for paper in get_papers_from_ris(args.ris_file):
            thread_pool.apply_async(search_paper_task, (func_name, paper, args.tor))
        
        thread_pool.close()
        thread_pool.join()

    
        # performing snowballing ....
        # for paper_tuple in ScholarSemantic().get_papers_to_snowball(args.direction):
        #    print (paper_tuple)

     