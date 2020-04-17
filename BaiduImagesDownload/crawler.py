from json import loads
from mimetypes import guess_extension
from os import mkdir
from os.path import exists, join
from requests.exceptions import ProxyError
from re import search
from requests import get
from string import Template
from time import sleep
from tqdm import tqdm
from urllib.parse import urlsplit


class Crawler:
    __HEADERS = {
        'User-Agent': 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/80.0.3987.149 Safari/537.36 '
    }
    __BASE_URL = 'https://image.baidu.com/search/acjson'
    __PAGE_NUM = 50
    __OBJURL_TABLE = {'_z2C$q': ':', '_z&e3B': '.', 'AzdH3F': '/'}
    __OBJURL_TRANS = str.maketrans('0123456789abcdefghijklmnopqrstuvw', '7dgjmoru140852vsnkheb963wtqplifca')
    __FILENAME_TEMPLATE = Template('${name}${ext}')

    def __init__(self, interval: float = 0.01):
        self.__interval = interval
        self.__params = {
            'face': 0,
            'ie': 'utf-8',
            'ipn': 'rj',
            'oe': 'utf-8',
            'pn': 0,
            'rn': self.__PAGE_NUM,
            'tn': 'resultjson_com',
        }
        self.__urls = []
        print('----INFO----初始化成功')

    @staticmethod
    def __mkdir_download(folder: str) -> None:
        if not exists(folder):
            mkdir(folder)

    def __decode_objurl(self, url: str) -> str:
        for key, value in self.__OBJURL_TABLE.items():
            url = url.replace(key, value)
        return url.translate(self.__OBJURL_TRANS)

    def __solve_imgdata(self, img: dict) -> dict:
        urls = {
            'obj_url': [],
            'from_url': []
        }
        if 'objURL' in img:
            urls['obj_url'].append(self.__decode_objurl(img['objURL']))
            urls['from_url'].append(self.__decode_objurl(img['fromURL']))
        if 'replaceUrl' in img and len(img['replaceUrl']) == 2:
            urls['obj_url'].append(img['replaceUrl'][1]['ObjURL'])
            urls['from_url'].append(img['replaceUrl'][0]['FromURL'])
        urls['obj_url'].append(img['thumbURL'])
        urls['from_url'].append('')
        return urls

    def __check_type(self, mime_type: str):
        pass

    def clear(self) -> None:
        self.__params['pn'] = 0
        self.__urls.clear()

    def get_images_url(self, word: str, num: int) -> bool:
        loaded = 0
        self.__params['pn'] = 0
        self.__params['queryWord'] = word
        self.__params['word'] = word

        res = get(self.__BASE_URL, params=self.__params, headers=self.__HEADERS)
        if res.status_code != 200:
            print('----ERROR---获取图片url失败')
            return False

        display_num = search(r'\"displayNum\":(\d+)', res.content.decode('utf-8'))
        display_num = int(display_num.group(1))
        if display_num < num:
            num = display_num
            print('----WARM----图片数量不足, 只有', num, '张')

        with tqdm(total=num, desc='获取url') as pbar:
            while loaded < num:
                res = get(self.__BASE_URL, params=self.__params, headers=self.__HEADERS)
                if res.status_code != 200:
                    print('----ERROR---获取图片url失败')
                    return False

                content = loads(res.content.decode('utf-8').replace(r'\'', ''), strict=False)

                length = 0
                for img in content['data']:
                    if 'objURL' in img:
                        self.__urls.append(self.__solve_imgdata(img))
                        length += 1

                self.__params['pn'] += self.__PAGE_NUM
                loaded += length
                if loaded >= num:
                    pbar.update(num - loaded + length)
                else:
                    pbar.update(length)

                sleep(self.__interval)

        print('----INFO----获取图片url成功')
        self.__urls = self.__urls[0:num]
        sleep(0.4)
        return True

    def download_images(self, num: int = None, folder: str = 'download') -> bool:
        self.__mkdir_download(folder)
        if num is None:
            num = len(self.__urls)
        elif num > len(self.__urls):
            num = len(self.__urls)
            print('----WARM----图片数量不足, 只有', num, '张')
        failed = []
        headers = self.__HEADERS.copy()
        for i in tqdm(range(num), desc='下载图片'):
            res = None

            for j in range(len(self.__urls[i]['obj_url'])):
                obj_url = self.__urls[i]['obj_url'][j]
                from_url = self.__urls[i]['from_url'][j]
                referer = {
                    'Referer': from_url
                }
                headers.update(referer)
                try:
                    res = get(obj_url, headers=headers)
                    if res.status_code == 200:
                        break
                except ProxyError:
                    pass

            if res is None:
                failed.append(i + 1)
                continue

            ext = guess_extension(
                res.headers['content-type'].partition(';')[0].strip())
            if ext in ('.jpe', '.jpeg'):
                ext = '.jpg'
            with open(join(folder, self.__FILENAME_TEMPLATE.substitute(name=(i + 1), ext=ext)), 'wb') as f:
                f.write(res.content)

            sleep(self.__interval)

        print('----INFO----图片下载结束')
        if failed:
            print('----ERROR---第', ', '.join(failed), '张图片下载失败')
            return False
        return True

    def start(self, word: str, num: int):
        self.clear()
        if self.get_images_url(word, int(num * 1.5)):
            self.download_images(num)


if __name__ == '__main__':
    crawler = Crawler()
    crawler.start('二次元', 200)
