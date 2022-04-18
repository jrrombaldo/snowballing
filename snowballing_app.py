import rispy
import argparse
import os

from snowballing.logging import log
from snowballing.config import config
from snowballing import database, threading


def parse_cli_args():
    parser = argparse.ArgumentParser(
        description='This script takes a RIS file with bibliography as input and perform a series of papers searchs',
        epilog='happy research! :)')


    tor_help = 'use TOR networks, where each task on each paper will have dedicated TOR cirtuit, meaning a new internet IP'
    threads_help = 'Number of threads running in parallel. Default (25)'

    subparsers = parser.add_subparsers(dest="script", required=True, help="Scripts available")


    lookup = subparsers.add_parser('lookup', help='given a RIS file, search for papers metadata')
    lookup.add_argument('--tor', action="store_true", help = tor_help)
    lookup.add_argument('--threads', action="store", help = threads_help, type=int)
    lookup.add_argument('ris_file', metavar='<RIS file>', type=argparse.FileType('r'),
        help='RIS format file containing bibliography')

    
    snowballing = subparsers.add_parser('snowballing', help='snowball encountered papers (at lookup phase)')
    snowballing.add_argument('--tor', action="store_true", help = tor_help)
    snowballing.add_argument('--threads', action="store", help = threads_help, type=int)
    snowballing.add_argument("--depth", help=f'Number of iteractions', action='store', type=int, default=1)


    summary = subparsers.add_parser('summary', help='print a summary of snowball\'ed papers')


    args = parser.parse_args()
    return args

def get_papers_from_ris(ris_file):
    return rispy.load(ris_file, skip_unknown_tags=False)



if __name__ == "__main__":
    args = parse_cli_args()
    # log.info(f"starting execution with:\n \t{args.threads} threads\n \tfile \
    #     {args.ris_file.name}\n \t{'using' if args.tor else 'not'} \
    #         tor networks\n \tdepth of {args.depth}\n \tsnowball direction of {args.direction}\t")

    if args.script == 'lookup':
        log.info("Searching for papers bibliography")
        threading.paper_metadata_lookup(
            get_papers_from_ris(args.ris_file),args.threads, args.tor)

    if args.script == 'snowballing':
        log.info("Snowballing encountered papers")
        threading.paper_snowball(args.threads, args.tor, 'both', 1)

    if args.script == 'summary':
        database.get_summary()





    # database.get_summary()
