import asyncio
import logging
from json import loads
from mimetypes import guess_extension
from os import listdir, makedirs
from os.path import join, splitext
from re import search
from shutil import copyfile
from string import Template
from tempfile import TemporaryDirectory
from typing import Dict, List, NewType, Tuple
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from aiohttp import ClientError as aioClientError
from aiohttp import ClientSession, ClientTimeout
from tqdm import tqdm

URLS = NewType("URLS", Dict[str, list])

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(
    logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s")
)
logger.addHandler(stream_handler)


class Crawler:
    __HEADERS = {
        "User-Agent": "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/80.0.3987.149 Safari/537.36 "
    }
    __BASE_URL = "https://image.baidu.com/search/acjson"
    __PAGE_NUM = 50
    __CONCURRENT_NUM = 100
    __CONCURRENT_TIMEOUT = 60
    __OBJURL_TABLE = {"_z2C$q": ":", "_z&e3B": ".", "AzdH3F": "/"}
    __OBJURL_TRANS = str.maketrans(
        "0123456789abcdefghijklmnopqrstuvw",
        "7dgjmoru140852vsnkheb963wtqplifca",
    )
    __FILENAME_TEMPLATE = Template("${name}${ext}")
    __PARAMS = {
        "face": 0,
        "ie": "utf-8",
        "ipn": "rj",
        "oe": "utf-8",
        "pn": 0,
        "rn": __PAGE_NUM,
        "tn": "resultjson_com",
    }

    @staticmethod
    def decode_objurl(url: str) -> str:
        """
        解密url
        :param url: 从百度图片json接口中获取的加密url
        :return: 解密后的url
        """

        for key, value in Crawler.__OBJURL_TABLE.items():
            url = url.replace(key, value)
        return url.translate(Crawler.__OBJURL_TRANS)

    @staticmethod
    def solve_imgdata(img: dict, original: bool) -> dict:
        """
        从json数据中提取url

        #param img: 获取的json数据项
        :return: 提取的url
        """
        url = {"obj_url": [], "from_url": []}

        if original is True:
            if "objURL" in img:
                url["obj_url"].append(Crawler.decode_objurl(img["objURL"]))
                url["from_url"].append(Crawler.decode_objurl(img["fromURL"]))

            elif "replaceUrl" in img and len(img["replaceUrl"]) == 2:
                url["obj_url"].append(img["replaceUrl"][1]["ObjURL"])
                url["from_url"].append(img["replaceUrl"][1]["FromURL"])

        if "middleURL" in img and img["middleURL"] != "":
            url["obj_url"].append(img["middleURL"])
            url["from_url"].append("")

        url["obj_url"].append(img["thumbURL"])
        url["from_url"].append("")

        return url

    @staticmethod
    def get_images_url(
        word: str,
        num: int,
        original: bool = True,
        timeout: int = __CONCURRENT_TIMEOUT,
    ) -> Tuple[bool, bool, list]:
        """
        从百度图片的json接口中获取图片的url

        :param word: 搜索关键词
        :param num: 搜索数量
        :param original: 是否下载原图
        :param timeout: 请求timeout, 默认60(s)
        :return: (
                    网络连接是否成功，成功为True，失败为False
                    图片数量是否满足，满足为True，不足为False
                    获取的urls
                 )
        """

        async def __fetch(pn: int) -> None:
            nonlocal net
            par = params.copy()
            par["pn"] = pn

            async with ClientSession(
                timeout=ClientTimeout(total=timeout)
            ) as session:
                try:
                    async with session.get(
                        Crawler.__BASE_URL,
                        params=par,
                        headers=Crawler.__HEADERS,
                    ) as res:
                        if res.status == 200:
                            text = await res.text()
                            logger.debug(text)
                            text = loads(text.replace(r"\'", ""), strict=False)

                            for img in text["data"]:
                                if "thumbURL" in img and img["thumbURL"] != "":
                                    urls.append(
                                        Crawler.solve_imgdata(img, original)
                                    )
                        else:
                            logger.debug("status" + str(res.status))
                            net = False
                except (aioClientError, asyncio.TimeoutError):
                    net = False

        net = True
        eng = True
        urls = []

        params = Crawler.__PARAMS.copy()
        params["queryWord"] = word
        params["word"] = word

        logger.info("开始获取图片url")

        req = Request((Crawler.__BASE_URL + "?%s") % urlencode(params))
        with urlopen(req) as r:
            if r.status != 200:
                net = False
            else:
                display_num = search(
                    r"\"displayNum\":(\d+)", r.read().decode("utf-8")
                )
                display_num = int(display_num.group(1))
                num = min(num, display_num)

        if net is True:
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            loop = asyncio.get_event_loop()
            tasks = [
                asyncio.ensure_future(__fetch(i))
                for i in range(0, num, Crawler.__PAGE_NUM)
            ]
            tasks = asyncio.gather(*tasks)
            loop.run_until_complete(tasks)

        if net is False:
            logger.error("网络连接失败")

        length = len(urls)

        if length != 0:
            logger.info("获取图片url结束")

        if length < num:
            eng = False
            logger.warning("获取图片url结束")
            num = length

        return net, eng, urls[0:num]

    @staticmethod
    async def __check_type(mime_type: str, rule: tuple) -> Tuple[bool, str]:
        """
        判断MIME type是否符合下载的格式要求
        MIME type和拓展名的对应关系：
        https://developer.mozilla.org/en-US/docs/Web/HTTP/Basics_of_HTTP/MIME_types/Common_types

        :param mime_type: 当前图片的MIME type
        :param rule: 允许下载的格式
        :return: (
                    是否允许，允许为True，禁止为False
                    MIME type对应的拓展名
                 )
        """

        allow = False
        ext = guess_extension(mime_type)
        if ext in (".jpe", ".jpeg"):
            ext = ".jpg"
        if ext in rule:
            allow = True
        return allow, ext

    @staticmethod
    def download_images(
        urls: List[URLS],
        rule: tuple = (".png", ".jpg"),
        path: str = "download",
        timeout: int = __CONCURRENT_TIMEOUT,
        concurrent: int = __CONCURRENT_NUM,
        command: bool = True,
    ) -> Tuple[int, int]:
        """
        下载图片到指定文件夹中

        :param urls: 满足格式的urls
        :param rule: 允许下载的格式
        :param path: 图片下载的路径
        :param timeout: 请求timeout, 默认60(s)
        :param concurrent: 并行下载的数量，默认100
        :param command: 是否在控制台显示进度条
        :return: (
                    下载成功的数量
                    下载失败的数量
                 )
        """

        async def __fetch(
            session, obj_url: str, from_url: str, idx: int
        ) -> bool:
            headers = Crawler.__HEADERS.copy()
            headers.update({"Referer": from_url})
            try:
                async with session.get(
                    obj_url, headers=headers, allow_redirects=False
                ) as res:
                    if res.status == 200 and "content-type" in res.headers:
                        allow, ext = await Crawler.__check_type(
                            res.headers["content-type"]
                            .partition(";")[0]
                            .strip(),
                            rule,
                        )

                        if allow is False:
                            return False

                        with open(
                            join(
                                tmpdirname,
                                Crawler.__FILENAME_TEMPLATE.substitute(
                                    name=idx, ext=ext
                                ),
                            ),
                            mode="wb",
                        ) as f:
                            while True:
                                chunk = await res.content.read(16)
                                if not chunk:
                                    break
                                f.write(chunk)
            except (aioClientError, asyncio.TimeoutError):
                return False

            return True

        async def __fetch_all(url: dict, idx: int) -> None:
            for j in range(len(url["obj_url"])):
                async with ClientSession(
                    timeout=ClientTimeout(total=timeout)
                ) as session:
                    allow = await __fetch(
                        session, url["obj_url"][j], url["from_url"][j], idx + 1
                    )
                    if allow is True:
                        if command is True:
                            pbar.update(1)
                        break

        success = 0

        try:
            makedirs(path)
        except FileExistsError:
            logger.warning("文件夹已存在")

        logger.info("开始图片下载")

        if command is True:
            pbar = tqdm(total=len(urls), ascii=True, miniters=1)

        with TemporaryDirectory() as tmpdirname:
            for i in range(0, len(urls), concurrent):
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                loop = asyncio.get_event_loop()
                tasks = [
                    asyncio.ensure_future(__fetch_all(url, i + idx))
                    for idx, url in enumerate(urls[i: i + concurrent])
                ]
                tasks = asyncio.gather(*tasks)
                loop.run_until_complete(tasks)

            files = listdir(tmpdirname)
            num_length = len(str(len(files)))
            for idx, filename in enumerate(files):
                success += 1
                copyfile(
                    join(tmpdirname, filename),
                    join(
                        path,
                        str(idx + 1).zfill(num_length) + splitext(filename)[1],
                    ),
                )

        if command is True:
            pbar.close()

        logger.info(str(success) + "张图片下载成功")

        failed = len(urls) - success
        if failed:
            logger.error(str(failed) + "张图片下载失败")

        return success, failed


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    net_, num_, urls_ = Crawler.get_images_url("二次元", 20, original=False)
    Crawler.download_images(urls_, path="download/test")
