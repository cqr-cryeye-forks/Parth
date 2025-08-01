# plugins/commoncrawl.py

import json
import re

import requests

surt_re = re.compile(r'^([a-z0-9,.-]+)\)/(.+)$')


def clean_url(raw: str) -> str | None:
    raw = raw.strip()

    if raw.endswith('}'):
        idx = raw.find('{')
        if idx != -1:
            try:
                return json.loads(raw[idx:])['url']
            except Exception:
                pass

    if raw.startswith(('http://', 'https://')):
        return raw

    m = surt_re.match(raw.split(' ')[0])
    if m:
        host = '.'.join(reversed(m.group(1).strip(')/').split(',')))
        return f'http://{host}/{m.group(2)}'

    return None


def commoncrawl(host, page=0):
    try:
        resp = requests.get(
            f'http://index.commoncrawl.org/CC-MAIN-2020-29-index?url=*.{host}&fl=url&page={page}&limit=10000',
            timeout=10
        )
        if resp.text.startswith('<!DOCTYPE html>'):
            return [], False, 'commoncrawl'

        raw_lines = resp.text.splitlines()
        urls = list(filter(None, (clean_url(line) for line in raw_lines)))
        urls = list(set(urls))

        return urls, True, 'commoncrawl'

    except Exception as e:
        return [], False, f'commoncrawl (error: {e})'
