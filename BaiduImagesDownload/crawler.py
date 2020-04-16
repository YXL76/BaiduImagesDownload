from requests_html import HTMLSession


class Crawler:
    __headers = {
        'User-Agent': 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/80.0.3987.149 Safari/537.36 '
    }
    __base_url = 'https://image.baidu.com/search/index'
    __session = HTMLSession()

    def __init__(self, interval: float = 0.1):
        self.__interval = interval
        self.__params = {
            'ie': 'utf-8',
            'oe': 'utf-8',
            'pn': 0,
            'tn': 'baiduimage'
        }
        self.__urls = []
        print('----INFO----初始化成功')

    def clear(self):
        self.__urls = []

    def get_images_url(self, word: str, num: int) -> bool:
        loaded = 0
        self.__params['pn'] = 0
        self.__params['queryWord'] = word
        self.__params['word'] = word

        while loaded < num:
            res = self.__session.get(self.__base_url, params=self.__params, headers=self.__headers)
            if res.status_code != 200:
                print('----ERROR---获取图片url失败')
                return False
            res.html.render()
            imgs = res.html.find('img.main_img')
            for i in imgs:
                self.__urls.append(i.attrs['data-imgurl'])
            length = len(imgs)
            loaded += length
            self.__params['pn'] += length

        print('----INFO----获取图片url成功')
        return True

    def download_images(self):
        pass

    def start(self, word: str, num: int):
        if self.get_images_url(word, num):
            self.download_images()


if __name__ == '__main__':
    crawler = Crawler()
    crawler.start('二次元', 10)
