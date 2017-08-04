import sendgrid
import argparse
from lib import *

# TODO verify git repo of start_path

parser = argparse.ArgumentParser(description='Find todos and send them!')
parser.add_argument("--dry", action="store_true", help="Don't email, just print instead.")
parser.add_argument('sg_key')
parser.add_argument('dir')
parser.add_argument('patterns', nargs='*')
args = parser.parse_args()

sg = sendgrid.SendGridAPIClient(apikey=args.sg_key)
email_blames(sg, find_blamers(args.dir, find_upsetters(args.dir, args.patterns)), dry=args.dry)
