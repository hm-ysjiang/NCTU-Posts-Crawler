import codecs
import configparser
import os
import platform
import requests
import webbrowser
from bs4 import BeautifulSoup
from datetime import datetime

url_pref = 'https://infonews.nctu.edu.tw/index.php' \
           '?topflag=1&SuperType=2&SuperTypeNo=2&type=%A6%E6%ACF&action=detail&id='
text = ''
br = ''


def readconfig() -> list:
    config = configparser.ConfigParser()
    config.read('config.ini')
    sect_last = config['Last_Index']
    year = sect_last['year']
    month = sect_last['month']
    idx = sect_last['index']

    safe_break = config['Setting']['safe_break']
    web_view = config.getboolean('Setting', 'web_view')
    return [int(year), int(month), int(idx), int(safe_break), web_view]


def write_config(idx: list, safe_break: int, web_view: bool):
    config = configparser.ConfigParser()
    config['Last_Index'] = {}
    config['Last_Index']['year'] = str(idx[0])
    config['Last_Index']['month'] = str(idx[1])
    config['Last_Index']['index'] = str(idx[2])

    config['Setting'] = {}
    config['Setting']['safe_break'] = str(safe_break)
    config['Setting']['web_view'] = 'true' if web_view else 'false'
    with open('config.ini', 'w') as file:
        config.write(file)


def generate_id(idx: list) -> str:
    return str(idx[0]) + ('0' * (2 - len(str(idx[1])))) + str(idx[1]) + ('0' * (5 - len(str(idx[2])))) + str(idx[2])


def notemptypage(idx: list):
    url_id = generate_id(idx)
    cont = requests.get(url_pref + url_id).text
    paragraph = BeautifulSoup(cont, 'html.parser').find('div', id='changeWidh')
    return paragraph.text != '\n'


# The return of True means that it had passed the safe_check, aka a real end of posts
def safebreakcheck(idx: list, safe_break: bool) -> bool:
    for i in range(safe_break):
        if notemptypage([idx[0], idx[1], idx[2] + i + 1]):
            for j in range(i):
                print('\n[Safe-Break checking]: Page (id={}) not found'.format(
                    generate_id([idx[0], idx[1], idx[2] + j + 1])), end='')
            idx[2] += i + 1
            return False
    return True


def run(idx: list) -> bool:
    global text, br

    url_id = generate_id(idx)
    print('\nDownloading page (id={0})...'.format(url_id), end='')
    r = requests.get(url_pref + url_id)
    r.encoding = 'big5'
    cont = r.text

    soup = BeautifulSoup(cont, 'html.parser')
    title = soup.find('b', class_='style2')
    paragraph = soup.find('div', id='changeWidh')

    if paragraph.text != '\n':
        text += br + '--------'
        text += br + 'id: {0}'.format(url_id)
        text += br + 'Title:' + br
        text += title.text
        text += br + 'Content:' + br
        text += paragraph.text
        text += br + '--------'
        return True
    print('Not Found.', end='')
    return False


def start():
    global text, br

    date = datetime.now()
    timetuple = date.timetuple()
    config = readconfig()
    index = config[:3]
    web_view = config[4]
    br = '<br>' if web_view else '\n'
    file_name = 'content.html' if web_view else 'content.txt'

    print('Current time:' + str(date)[:16])
    print('Web View: ' + ('On' if web_view else 'Off'))
    print('Start from id ' + generate_id(index))
    print('--------', end='')

    if notemptypage(index):
        text += 'Current time:' + str(date)[:16]
        while True:
            if run(index):
                index[2] += 1
                continue

            # Switch to next month
            elif index[1] != timetuple[1]:
                # safe_break_check
                if not safebreakcheck(index, config[3]):
                    continue

                print('Switching to the next month.', end='')
                index[2] = 1
                index[1] += 1
                continue

            # Happy New Year!
            elif index[0] != timetuple[0]:
                # safe_break_check
                if not safebreakcheck(index, config[3]):
                    continue

                print('Switching to the next year, Happy New Year BTW.', end='')
                index[2] = 1
                index[1] = 1
                index[0] += 1
                continue
            # No post available
            else:
                # safe_break_check
                if not safebreakcheck(index, config[3]):
                    continue

                print('\n--------')
                print('End at id {0}, set config...'.format(generate_id(index)))
                write_config(index, config[3], web_view)
                print('Writing contents to external file...')
                with codecs.open(file_name, 'w', encoding='utf8') as file:
                    file.write(text)
                print('Exiting program...')
                break
    else:
        # safe_break_check
        flag = False
        for i in range(config[3]):
            if notemptypage([index[0], index[1], index[2] + i + 1]):
                index[2] += i + 1
                flag = True
                write_config(index, config[3], web_view)
                start()
        if not flag:
            print('--------')
            print('UP-TO-DATE. Exiting program...')
        del flag

    if platform.system() == 'Windows':
        webbrowser.open_new(file_name)
    elif platform.system() == 'Darwin':
        os.system('open content.txt')
    else:
        os.system('xdg-open content.txt')
    input('\nPress Enter to exit...')


if __name__ == '__main__':
    start()
