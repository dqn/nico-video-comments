import sys
import requests
import json
import urllib.parse
import xmltodict
from bs4 import BeautifulSoup

VERSION = '20061206'
SCORES = '1'

OUTPUT_FILE = './comments.json'

def login(session, mail, password):
    url = 'https://account.nicovideo.jp/api/v1/login'
    qs = urllib.parse.urlencode({
        'show_button_twitter': 1,
        'site': 'niconico',
    })
    params = {
        'mail': mail,
        'password': password,
    }
    session.post('{}?{}'.format(url, qs), params=params)

def is_logined(session):
    url = 'http://www.nicovideo.jp/'
    res = session.get(url)

    return res.headers['x-niconico-authflag'] == '1'

def get_flv(session, video_id):
    url = 'http://flapi.nicovideo.jp/api/getflv/{}'.format(video_id)
    return session.get(url)

def get_threadkey(session, thread_id):
    url = 'http://flapi.nicovideo.jp/api/getthreadkey'
    params = {
        'thread': thread_id,
    }
    return session.get(url, params=params)

def execute(mail, password, video_id, count):
    session = requests.session()
    login(session, mail, password)

    if not is_logined(session):
        return print('failed to login.')

    qs_to_dict = lambda qs: dict(urllib.parse.parse_qsl(qs))
    text_to_soup = lambda t: BeautifulSoup(t, 'lxml')

    flv = qs_to_dict(get_flv(session, video_id).text)

    params = {
        'version': VERSION,
        'scores': SCORES,
        'thread': flv.get('thread_id'),
        'res_from': -1 * int(count)
    }

    if flv['needs_key'] == '1':
        # needs_key が 1 の場合、追加でパラメータが必要。
        soup = text_to_soup(get_threadkey(session, flv.get('thread_id')).text)
        threadkey = qs_to_dict(soup.html.body.p.text)

        params['threadkey'] = threadkey.get('threadkey'),
        params['force_184'] = threadkey.get('force_184'),
        params['user_id'] = flv.get('user_id'),

    url = '{}thread'.format(flv.get('ms'))
    soup = text_to_soup(session.get(url, params=params).text)

    return [xmltodict.parse(str(chat)).get('chat') for chat in soup.select('chat')]

def usage():
    print('Usage: python fetch.py [mail] [password] [video id] [count]')

def main():
    if len(sys.argv) != 5:
        return usage()

    comment_list = execute(
        sys.argv[1],
        sys.argv[2],
        sys.argv[3],
        sys.argv[4]
    )

    with open(OUTPUT_FILE, mode='w') as f:
        f.write(json.dumps(comment_list, indent=2))
    print(OUTPUT_FILE)

if __name__ == '__main__':
    main()
