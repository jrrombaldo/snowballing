import rispy
import argparse
import os

from snowballing.logging import log
from snowballing.config import config
from snowballing import database, threading

def parse_cli_args():
    parser = argparse.ArgumentParser(
        description=' Snowballing and metadata searcing...',
        epilog='happy research! :)')


    # TODO papers lookup, snowballing, summary

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



if __name__ == "__main__":
    args = parse_cli_args()

    log.info(f"starting execution with:\n \t{args.threads} threads\n \tfile \
        {args.ris_file.name}\n \t{'using' if args.tor else 'not'} \
            tor networks\n \tdepth of {args.depth}\n \tsnowball direction of {args.direction}\t")
    
    log.info("searching for bibliography")
    threading.lookup_bibliography_metadata(
        get_papers_from_ris(args.ris_file),args.threads, args.tor)


    log.info("snowballing extracted papers")
    threading.snowball_papers(args.threads, args.tor, args.direction, args.depth)


    # database.get_summary()
