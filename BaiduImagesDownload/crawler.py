import json
import os
import requests
from mimetypes import guess_extension
from requests.exceptions import ProxyError
from string import Template
from time import sleep
from tqdm import tqdm
from urllib.parse import urlsplit


class Crawler:
    __headers = {
        'User-Agent': 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/80.0.3987.149 Safari/537.36 '
    }
    __BASE_URL = 'https://image.baidu.com/search/acjson'
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
            'rn': 30,
            'tn': 'resultjson_com',
        }
        self.__urls = []
        print('----INFO----初始化成功')

    def clear(self):
        self.__params['pn'] = 0
        self.__urls.clear()

    @staticmethod
    def __mkdir_download(folder: str):
        if not os.path.exists(folder):
            os.mkdir(folder)

    @staticmethod
    def __decode_objurl(self, url: str):
        for key, value in self.__OBJURL_TABLE:
            url = url.replace(key, value)
        return url.translate(self.__OBJURL_TRANS)

    def get_images_url(self, word: str, num: int) -> bool:
        loaded = 0
        self.__params['pn'] = 0
        self.__params['queryWord'] = word
        self.__params['word'] = word

        res = requests.get(self.__BASE_URL, params=self.__params, headers=self.__headers)
        if res.status_code != 200:
            print('----ERROR---获取图片url失败')
            return False
        content = res.content.decode('utf-8')
        print(content.replace('\\', ''))
        content = json.loads(content.replace('\\', ''), strict=False)
        if content['listNum'] < num:
            num = content['listNum']
            print('----WARM----图片数量不足')

        with tqdm(total=num, desc='获取url') as pbar:
            while loaded < num:
                res = requests.get(self.__BASE_URL, params=self.__params, headers=self.__headers)
                print(res.url)
                if res.status_code != 200:
                    print('----ERROR---获取图片url失败')
                    return False
                content = json.loads(res.content)
                length = 0
                for img in content['data']:
                    if 'thumbURL' in img:
                        self.__urls.append(img)
                        length += 1
                self.__params['pn'] += 30
                if (loaded + length) >= num:
                    pbar.update(num - loaded)
                else:
                    pbar.update(length)
                loaded += length
                sleep(self.__interval)

            self.__urls = self.__urls[0:num]

        print('----INFO----获取图片url成功')
        sleep(0.5)
        return True

    def download_images(self, num: int = None, folder: str = 'download'):
        self.__mkdir_download(folder)
        failed = []
        for i in tqdm(range(len(self.__urls)), desc='下载图片'):
            img = self.__urls[i]
            urls = []
            if 'replaceUrl' in img:
                for url in img['replaceUrl']:
                    urls.append(url['ObjURL'])
            urls.append(img['thumbURL'])
            res = ''
            for url in urls:
                split_url = urlsplit(url)
                referer = {
                    'Referer': split_url.scheme + '://' + split_url.netloc
                }
                headers = self.__headers.copy()
                headers.update(referer)
                try:
                    res = requests.get(url, headers=headers)
                    if res.status_code == 200:
                        break
                except ProxyError:
                    pass
            if res == '':
                failed.append(i + 1)
                continue

            ext = guess_extension(
                res.headers['content-type'].partition(';')[0].strip())
            if ext in ('.jpe', '.jpeg'):
                ext = '.jpg'
            with open(os.path.join(folder, self.__FILENAME_TEMPLATE.substitute(name=(i + 1), ext=ext)), 'wb') as f:
                f.write(res.content)
            sleep(self.__interval)

        if failed:
            print('----ERROR---第', ', '.join(failed), '张图片下载失败')
        print('----INFO----图片下载结束')

    def start(self, word: str, num: int):
        self.clear()
        if self.get_images_url(word, num * 2):
            self.download_images(num)


if __name__ == '__main__':
    crawler = Crawler()
    crawler.start('小姐姐', 200)
