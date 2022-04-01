import argparse


def parse_cli_args():
    parser = argparse.ArgumentParser(
        description=' Snowballing and metadata searcing...',
        epilog='happy research! :)')


    subparsers = parser.add_subparsers(dest="module", required=True, help="operation module")
    
    #  Search module
    ris_parser = subparsers.add_parser('search', 
    help='perform semanticscholar searchs')


    # Snowballing method
    rayyan_parser = subparsers.add_parser('snowballing', 
        help='whatever it does ...')
    rayyan_parser.add_argument('--approach', 
        metavar='<snowballing approach>',
        required=True,
        choices=['backward', 'forward', 'both'],
        help='type of snowballing ...'
    )

    parser.add_argument('ris_file', 
        metavar='<RIS file>', 
        type=argparse.FileType('r'),
        help='RIS format file containing bibliography')
    
    parser.add_argument("--threads",
        help='Number of threads (one thread per paper). Default (75)',
        metavar='<nuumber of threads>', 
        action='store',
        required=False,
        type=int,
        default=1)
    
    parser.add_argument('--tor', 
        help='use TOR networks, which thread will create a connection and will have different internet IP',
        action='store_true', 
        required=False,
        default=False)

    args = parser.parse_args()
    return args

        


