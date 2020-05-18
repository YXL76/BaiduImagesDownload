from aiohttp import ClientError as async_ClientError, ClientSession, ClientTimeout
from asyncio import TimeoutError as async_TimeoutError, ensure_future, gather, get_event_loop
from json import loads
import logging
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

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(logging.Formatter(
    '%(asctime)s [%(levelname)s] %(message)s'))
logger.addHandler(stream_handler)


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
            'rn': Crawler.__PAGE_NUM,
            'tn': 'resultjson_com',
        }
        self.__timeout = timeout
        logger.info('初始化成功')

    @staticmethod
    def decode_objurl(url: str) -> str:
        for key, value in Crawler.__OBJURL_TABLE.items():
            url = url.replace(key, value)
        return url.translate(Crawler.__OBJURL_TRANS)

    @staticmethod
    def solve_imgdata(img: dict) -> dict:
        url = {
            'obj_url': [],
            'from_url': []
        }

        if 'objURL' in img:
            url['obj_url'].append(Crawler.decode_objurl(img['objURL']))
            url['from_url'].append(Crawler.decode_objurl(img['fromURL']))

        elif 'replaceUrl' in img and len(img['replaceUrl']) == 2:
            url['obj_url'].append(img['replaceUrl'][1]['ObjURL'])
            url['from_url'].append(img['replaceUrl'][1]['FromURL'])

        url['obj_url'].append(img['middleURL'])
        url['from_url'].append('')

        url['obj_url'].append(img['thumbURL'])
        url['from_url'].append('')

        return url

    def get_images_url(self, word: str, num: int) -> (bool, bool, list):

        async def __fetch(pn: int) -> None:
            nonlocal net
            params = self.__params.copy()
            params['pn'] = pn

            async with ClientSession(timeout=ClientTimeout(total=self.__timeout)) as session:
                try:
                    async with session.get(Crawler.__BASE_URL, params=params, headers=Crawler.__HEADERS) as res:
                        if res.status == 200:
                            text = await res.text()
                            logger.debug(text)
                            text = loads(text.replace(r'\'', ''), strict=False)

                            for img in text['data']:
                                if 'thumbURL' in img and img['thumbURL'] != '':
                                    urls.append(Crawler.solve_imgdata(img))
                        else:
                            logger.debug('status' + str(res.status))
                            net = False
                except (async_ClientError, async_TimeoutError):
                    net = False

        net = True
        eng = True
        urls = []

        self.__params['pn'] = 0
        self.__params['queryWord'] = word
        self.__params['word'] = word

        logger.info('开始获取图片url')

        with urlopen((Crawler.__BASE_URL + '?%s') % urlencode(self.__params)) as r:
            if r.status != 200:
                net = False
            else:
                display_num = search(r'\"displayNum\":(\d+)',
                                     r.read().decode('utf-8'))
                display_num = int(display_num.group(1))
                num = min(num, display_num)

        if net is True:
            loop = get_event_loop()
            tasks = [ensure_future(__fetch(i))
                     for i in range(0, num, Crawler.__PAGE_NUM)]
            tasks = gather(*tasks)
            loop.run_until_complete(tasks)

        if net is False:
            logger.error('网络连接失败')

        length = len(urls)

        if length != 0:
            logger.info('获取图片url结束')

        if length < num:
            eng = False
            logger.warning('获取图片url结束')
            num = length

        return net, eng, urls[0:num]

    @staticmethod
    async def __check_type(mime_type: str, rule: tuple) -> (bool, str):
        allow = False
        ext = guess_extension(mime_type)
        if ext in ('.jpe', '.jpeg'):
            ext = '.jpg'
        if ext in rule:
            allow = True
        return allow, ext

    def download_images(self, urls: list,
                        rule: tuple = ('.png', '.jpg'), path: str = 'download') -> (int, int):

        async def __fetch(session, obj_url: str, from_url: str, idx: int) -> bool:
            headers = Crawler.__HEADERS.copy()
            headers.update({'Referer': from_url})
            try:
                async with session.get(obj_url, headers=headers, allow_redirects=False) as res:
                    if res.status == 200 and 'content-type' in res.headers:
                        allow, ext = await Crawler.__check_type(res.headers['content-type'].partition(';')[0].strip(), rule)

                        if allow is False:
                            return False

                        with open(join(tmpdirname, Crawler.__FILENAME_TEMPLATE.substitute(name=idx, ext=ext)),
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
            for j in range(len(url['obj_url'])):
                async with ClientSession(timeout=ClientTimeout(total=self.__timeout)) as session:
                    allow = await __fetch(session, url['obj_url'][j], url['from_url'][j], idx + 1)
                    if allow is True:
                        pbar.update(1)
                        break

        success = 0

        try:
            mkdir(path)
        except FileExistsError:
            logger.warning('文件夹已存在')

        logger.info('开始图片下载')

        pbar = tqdm(total=len(urls), ascii=True, miniters=1)

        with TemporaryDirectory() as tmpdirname:
            for i in range(0, len(urls), Crawler.__CONCURRENT_NUM):
                loop = get_event_loop()
                tasks = [ensure_future(__fetch_all(url, i + idx))
                         for idx, url in enumerate(urls[i:i + Crawler.__CONCURRENT_NUM])]
                tasks = gather(*tasks)
                loop.run_until_complete(tasks)

            files = listdir(tmpdirname)
            num_length = len(str(len(files)))
            for idx, filename in enumerate(files):
                success += 1
                copyfile(join(tmpdirname, filename),
                         join(path, str(idx + 1).zfill(num_length) + splitext(filename)[1]))

        pbar.close()

        logger.info(str(success) + '张图片下载成功')

        failed = len(urls) - success
        if failed:
            logger.error(str(failed) + '张图片下载失败')

        return success, failed


if __name__ == '__main__':
    logger.setLevel(logging.DEBUG)
    crawler = Crawler()
    net, num, urls = crawler.get_images_url('二次元', 20)
    crawler.download_images(urls)
