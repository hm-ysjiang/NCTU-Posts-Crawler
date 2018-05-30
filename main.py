import codecs
import configparser
import os
import platform
import requests
from bs4 import BeautifulSoup
from datetime import datetime

url_pref = 'https://infonews.nctu.edu.tw/index.php' \
           '?topflag=1&SuperType=2&SuperTypeNo=2&type=%A6%E6%ACF&action=detail&id='
text = ''


def readconfig() -> list:
    config = configparser.ConfigParser()
    config.read('config.ini')
    sect_last = config['Last_Index']
    year = sect_last['year']
    month = sect_last['month']
    idx = sect_last['index']

    safe_break = config['Setting']['safe_break']
    return [int(year), int(month), int(idx), int(safe_break)]


def write_config(idx: list, safe_break: int):
    config = configparser.ConfigParser()
    config['Last_Index'] = {}
    config['Last_Index']['year'] = str(idx[0])
    config['Last_Index']['month'] = str(idx[1])
    config['Last_Index']['index'] = str(idx[2])

    config['Setting'] = {}
    config['Setting']['safe_break'] = str(safe_break)
    with open('config.ini', 'w') as file:
        config.write(file)


def generate_id(idx: list) -> str:
    return str(idx[0]) + ('0' * (2 - len(str(idx[1])))) + str(idx[1]) + ('0' * (5 - len(str(idx[2])))) + str(idx[2])


def notemptypage(idx: list):
    url_id = generate_id(idx)
    cont = requests.get(url_pref + url_id).text
    paragraph = BeautifulSoup(cont, 'html.parser').find('div', id='changeWidh')
    return paragraph.text != '\n'


def run(idx: list) -> bool:
    global text

    url_id = generate_id(idx)
    r = requests.get(url_pref + url_id)
    r.encoding = 'big5'
    cont = r.text

    soup = BeautifulSoup(cont, 'html.parser')
    title = soup.find('b', class_='style2')
    paragraph = soup.find('div', id='changeWidh')

    if paragraph.text != '\n':
        text += '\n--------'
        text += '\nid: {0}'.format(url_id)
        text += '\nTitle:\n'
        text += title.text
        text += '\nContent:\n'
        text += paragraph.text
        text += '\n--------'
        return True
    return False


def start():
    global text

    date = datetime.now()
    timetuple = date.timetuple()
    config = readconfig()
    index = config[:3]

    print('Current time:' + str(date)[:16])
    print('Start from id ' + generate_id(index))
    print('--------')

    if notemptypage(index):
        text += 'Current time:' + str(date)[:16]
        while True:
            if run(index):
                index[2] += 1
                continue
            # Switch to next month
            elif index[1] != timetuple[1]:
                index[2] = 1
                index[1] += 1
                continue
            # Happy New Year!
            elif index[0] != timetuple[0]:
                index[2] = 1
                index[1] = 1
                index[0] += 1
                continue
            # No post available
            else:
                print(*index)
                # safe_break_check
                flag = False
                for i in range(config[3]):
                    if notemptypage([index[0], index[1], index[2] + i + 1]):
                        index[2] += i + 1
                        flag = True
                        break
                if flag:
                    continue
                del flag

                print('End at id {0}, set config...'.format(generate_id(index)))
                write_config(index, config[3])
                print('Writing contents to external file...')
                with codecs.open('content.txt', 'w', encoding='utf8') as file:
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
                write_config(index, config[3])
                start()
        if not flag:
            print('--------')
            print('UP-TO-DATE. Exiting program...')
        del flag

    if platform.system() == 'Windows':
        os.system('start content.txt')
    elif platform.system() == 'Darwin':
        os.system('open content.txt')
    else:
        os.system('xdg-open content.txt')


if __name__ == '__main__':
    start()
