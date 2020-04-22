from aiohttp import ClientError as async_ClientError, ClientSession, ClientTimeout
from asyncio import TimeoutError as async_TimeoutError, ensure_future, gather, get_event_loop
from json import loads
from mimetypes import guess_extension
from os import listdir, mkdir
from os.path import exists, join, splitext
from re import search
from shutil import copyfile
from string import Template
from tempfile import TemporaryDirectory
from tqdm import tqdm
from urllib.parse import urlencode
from urllib.request import urlopen


class Crawler:
    __HEADERS = {
        'User-Agent': 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/80.0.3987.149 Safari/537.36 '
    }
    __BASE_URL = 'https://image.baidu.com/search/acjson'
    __PAGE_NUM = 50
    __CONCURRENT_NUM = 100
    __CONCURRENT_TIMEOUT = 60
    __OBJURL_TABLE = {'_z2C$q': ':', '_z&e3B': '.', 'AzdH3F': '/'}
    __OBJURL_TRANS = str.maketrans(
        '0123456789abcdefghijklmnopqrstuvw', '7dgjmoru140852vsnkheb963wtqplifca')
    __FILENAME_TEMPLATE = Template('${name}${ext}')

    def __init__(self, timeout: float = __CONCURRENT_TIMEOUT):
        self.__params = {
            'face': 0,
            'ie': 'utf-8',
            'ipn': 'rj',
            'oe': 'utf-8',
            'pn': 0,
            'rn': self.__PAGE_NUM,
            'tn': 'resultjson_com',
        }
        self.__timeout = timeout
        self.__urls = []
        print('----INFO----初始化成功')

    def clear(self) -> None:
        self.__params['pn'] = 0
        self.__urls.clear()

    def get_images_url(self, word: str, num: int, total: int) -> bool:

        def __decode_objurl(url: str) -> str:
            for key, value in self.__OBJURL_TABLE.items():
                url = url.replace(key, value)
            return url.translate(self.__OBJURL_TRANS)

        def __solve_imgdata(img: dict) -> dict:
            urls = {
                'obj_url': [],
                'from_url': []
            }
            if 'objURL' in img:
                urls['obj_url'].append(__decode_objurl(img['objURL']))
                urls['from_url'].append(__decode_objurl(img['fromURL']))
            elif 'replaceUrl' in img and len(img['replaceUrl']) == 2:
                urls['obj_url'].append(img['replaceUrl'][1]['ObjURL'])
                urls['from_url'].append(img['replaceUrl'][0]['FromURL'])
            urls['obj_url'].append(img['thumbURL'])
            urls['from_url'].append('')
            return urls

        async def __fetch(pn: int) -> None:
            nonlocal loaded
            params = self.__params.copy()
            params['pn'] = pn
            length = 0

            async with ClientSession(timeout=ClientTimeout(total=self.__timeout)) as session:
                async with session.get(self.__BASE_URL, params=params, headers=self.__HEADERS) as res:
                    if res.status == 200:
                        text = await res.text()
                        text = loads(text.replace(r'\'', ''), strict=False)

                        for img in text['data']:
                            if 'thumbURL' in img and img['thumbURL'] != '':
                                self.__urls.append(__solve_imgdata(img))
                                length += 1
                    else:
                        print('----ERROR---获取图片url失败')

            loaded += length
            pbar.update(total - loaded + length if loaded > total else length)

        loaded = 0
        self.__params['pn'] = 0
        self.__params['queryWord'] = word
        self.__params['word'] = word

        print('----INFO----开始获取图片url')

        with urlopen((self.__BASE_URL + '?%s') % urlencode(self.__params)) as r:
            if r.status != 200:
                print('----ERROR---获取图片url失败')
                return False

            display_num = search(r'\"displayNum\":(\d+)',
                                 r.read().decode('utf-8'))
            display_num = int(display_num.group(1))
            total = min(total, display_num)
            if display_num < num:
                print('----WARM----图片数量不足, 只有', display_num, '张')

        with tqdm(total=total, desc='获取url', miniters=1) as pbar:
            loop = get_event_loop()
            tasks = [ensure_future(__fetch(i))
                     for i in range(0, total, self.__PAGE_NUM)]
            tasks = gather(*tasks)
            loop.run_until_complete(tasks)

            pbar.update(total - loaded)

        print('----INFO----获取图片url成功')
        return True

    def download_images(self, rule: tuple, num: int = None, folder: str = 'download') -> bool:

        async def __check_type(mime_type: str) -> (bool, str):
            allow = False
            ext = guess_extension(mime_type)
            if ext in ('.jpe', '.jpeg'):
                ext = '.jpg'
            if ext in rule:
                allow = True
            return allow, ext

        async def __fetch(session, obj_url: str, from_url: str, idx: int) -> bool:
            headers = self.__HEADERS.copy()
            headers.update({'Referer': from_url})
            try:
                async with session.get(obj_url, headers=headers, allow_redirects=False) as res:
                    if res.status == 200 and 'content-type' in res.headers:
                        allow, ext = await __check_type(res.headers['content-type'].partition(';')[0].strip())
                        if allow is False:
                            return False
                        with open(join(tmpdirname, self.__FILENAME_TEMPLATE.substitute(name=idx, ext=ext)),
                                  mode='wb') as f:
                            while True:
                                chunk = await res.content.read(16)
                                if not chunk:
                                    break
                                f.write(chunk)
            except (async_ClientError, async_TimeoutError):
                return False
            return True

        async def __fetch_all(url: dict, idx: int) -> None:
            nonlocal success
            nonlocal failed
            allow = False

            for j in range(len(url['obj_url'])):
                async with ClientSession(timeout=ClientTimeout(total=self.__timeout)) as session:
                    allow = await __fetch(session, url['obj_url'][j], url['from_url'][j], idx + 1)
                    if allow is True:
                        break

            if allow is False:
                failed += 1
            elif success < num:
                success += 1
                pbar.update(1)

        if not exists(folder):
            mkdir(folder)

        success = 0
        failed = 0

        if num is None or num > len(self.__urls):
            num = len(self.__urls)

        print('----INFO----开始图片下载')

        with tqdm(total=num, desc='下载图片', miniters=1) as pbar:
            with TemporaryDirectory() as tmpdirname:
                for i in range(0, len(self.__urls), self.__CONCURRENT_NUM):
                    loop = get_event_loop()
                    tasks = [ensure_future(__fetch_all(url, i + idx))
                             for idx, url in enumerate(self.__urls[i:i + self.__CONCURRENT_NUM])]
                    tasks = gather(*tasks)
                    loop.run_until_complete(tasks)

                pbar.update(num - success)

                num_length = len(str(num))
                files = listdir(tmpdirname)
                for idx, filename in enumerate(files):
                    if idx >= num:
                        break
                    success += 1
                    copyfile(join(tmpdirname, filename),
                             join(folder, str(idx + 1).zfill(num_length) + splitext(filename)[1]))

                success = min(num, len(files))

        print('----INFO----', success, '张图片下载成功')
        if failed:
            print('----ERROR---', failed, '张图片下载失败')
            return False
        return True

    def start(self, word: str, num: int, rule: tuple = None) -> None:
        self.clear()
        if rule is None:
            rule = ('.png', '.jpg')

        if self.get_images_url(word, num, int(num * 1.5)):
            self.download_images(rule, num)

        self.clear()


if __name__ == '__main__':
    crawler = Crawler()
    crawler.start('二次元', 20)
