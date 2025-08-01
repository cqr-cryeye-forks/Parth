#!/usr/bin/env python3

import argparse
import concurrent.futures
import sys

from .core.colors import green, end, info, bad
from .core.importer import importer
from .core.scanner import scanner
from .core.utils import save_result
from .plugins.commoncrawl import commoncrawl
from .plugins.otx import otx
from .plugins.wayback import wayback


def arg_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--host',
        help='target host',
    )
    parser.add_argument(
        '--input-file', help='import from file',
    )
    parser.add_argument(
        '--output',
        help='output file',
    )
    parser.add_argument(
        '--dupes',
        help='uniq parameters',
        action='store_true',
    )
    parser.add_argument(
        '--save_params',
        help='save parameters',
        action='store_true',
    )
    parser.add_argument(
        '--pipe',
        help='only display these issues',
    )
    return parser.parse_args()


def fetch_urls(host):
    available_plugins = {'commoncrawl': commoncrawl, 'otx': otx, 'wayback': wayback}
    page = 0
    progress = 0
    requests = {}
    while len(available_plugins) > 0 and page <= 10:
        threadpool = concurrent.futures.ThreadPoolExecutor(max_workers=len(available_plugins))
        futures = (threadpool.submit(func, host, page) for func in available_plugins.values())
        for each in concurrent.futures.as_completed(futures):
            if progress < 98:
                progress += 3
            this_result = each.result()
            if not this_result[1]:
                progress += ((10 - page) * 10 / 3)
                del available_plugins[this_result[2]]
            for url in this_result[0]:
                requests[url] = []
            # print(f'{info} Progress: {progress:d}%', end='\r')
        page += 1
    print(f'{info} Progress: {100:d}%', end='\r')
    return requests


def main():
    args = arg_parser()

    result = []
    all_params = []

    requests = None
    if args.host:
        requests = fetch_urls(args.host)
    elif args.input_file:
        requests = importer(args.input_file)
    elif not sys.stdin.isatty():
        requests = 1
        for line in sys.stdin:
            this_result, all_params = scanner(
                {line.rstrip('\r\n'): []},
                args.save_params,
                args.dupes
            )
            if args.pipe and this_result:
                if args.pipe in this_result[0]['issues']:
                    print(this_result[0]['url'])
            else:
                result.extend(this_result)
        if args.pipe:
            quit()
    else:
        print('%s No targets specified.' % bad)

    if requests:
        if requests != 1:
            result, all_params = scanner(requests, args.save_params, args.dupes)
        if args.output:
            save_result(result, args.output)
            print(f'{info} Result saved to {args.output}')
        else:
            for each in result:
                print(f'{green}+{end} {each["url"]}')
                print(f'    {green}- issues:{end}   {", ".join(each["issues"])}')
                print(f'    {green}- location:{end} {each["location"]}')
                if each['data']:
                    print(f'{green}- data:{end} {each["data"]}')

    if args.save_params:
        suffix = args.input_file or args.host
        with open('params-' + suffix.strip('.history').strip('.txt') + '.txt', 'w+') as f:
            f.write('\n'.join(all_params))
