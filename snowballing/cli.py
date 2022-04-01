import argparse


def parse_cli_args():
    parser = argparse.ArgumentParser(
        description=' Snowballing and metadata searcing...',
        epilog='happy research! :)')

    subparsers = parser.add_subparsers(dest="module", required=True, help="operation module")
    
    #  Search module
    ris_parser = subparsers.add_parser('search ', 
    help='perform semanticscholar searchs')
    ris_parser.add_argument('ris_file', 
        metavar='RIS_file', 
        type=argparse.FileType('r'),
        help='RIS file containing studies')

    # Snowballing method
    rayyan_parser = subparsers.add_parser('snowballing', 
        help='whatever it does ...')
    rayyan_parser.add_argument('ris_file', 
        metavar='RIS_file', 
        type=argparse.FileType('r'),
        help='RIS file containing studies'
    )

    args = parser.parse_args()
    return args

        


