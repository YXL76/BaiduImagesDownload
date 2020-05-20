# BaiduImagesDownload

[![Python package](https://github.com/YXL76/BaiduImagesDownload/workflows/Python%20package/badge.svg)](https://github.com/YXL76/BaiduImagesDownload/actions)
[![codecov](https://codecov.io/gh/YXL76/BaiduImagesDownload/branch/master/graph/badge.svg)](https://codecov.io/gh/YXL76/BaiduImagesDownload)
[![Codacy Badge](https://app.codacy.com/project/badge/Grade/0dce5ee6b45f427fa5aa782907408d19)](https://www.codacy.com/manual/YXL76/BaiduImagesDownload?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=YXL76/BaiduImagesDownload&amp;utm_campaign=Badge_Grade)

> `BaiduImagesDownload`是一个快速、简单百度图片爬取工具

```python
from BaiduImagesDownload.crawler import Crawler

net, num, urls = Crawler.get_images_url('二次元', 20)
Crawler.download_images(urls)
```

目录

- [安装](#安装)
- [使用](#使用)
  - [基本](#基本)
  - [设置图片格式](#设置图片格式)
  - [设置timeout](#设置timeout)
- [文档](#文档)
  - [get_images_url](#get_images_url)
  - [download_images](#download_images)
  - [日志](#日志)
- [许可](#许可)

## 安装

```bash
pip install BaiduImagesDownload
```

## 使用

### 基本

```python
from BaiduImagesDownload.crawler import Crawler

net, num, urls = Crawler.get_images_url('二次元', 20)
Crawler.download_images(urls)
```

### 设置图片格式

```python
from BaiduImagesDownload.crawler import Crawler

# rule默认为('.png', '.jpg')
net, num, urls = Crawler.get_images_url('二次元', 20)
Crawler.download_images(urls, rule=('.png', '.jpg'))
```

### 设置timeout

```python
from BaiduImagesDownload.crawler import Crawler

# timeout默认为60(s)
net, num, urls = Crawler.get_images_url('二次元', 20, timeout=60)
Crawler.download_images(urls, rule=('.png', '.jpg'), timeout=60)
```

## 文档

### get_images_url

```python
class Crawler:

    @staticmethod
    def get_images_url(word: str, num: int, timeout: int = __CONCURRENT_TIMEOUT) -> (bool, bool, list):
```

参数

- `word: str`: 搜索关键词
- `num: int`: 搜索数量
- `timeout: int`: 请求timeout, 默认为`60(s)`

返回

- `net: bool`: 网络连接是否成功，成功为True，失败为False
- `num: bool`: 图片数量是否满足，满足为True，不足为False
- `urls: list`: 获取的urls，每项为一个`dict`，其中有两个键`obj_url`，`from_url`。`obj_url`为对应图片的`url`，`from_url`为`Referer`

### download_images

```python
class Crawler:

    @staticmethod
    def download_images(urls: list, rule: tuple = ('.png', '.jpg'),
                        path: str = 'download', timeout: int = __CONCURRENT_TIMEOUT,
                        concurrent: int = __CONCURRENT_NUM) -> (int, int):
```

参数

- `urls: list`: 需要爬的图片列表，格式与`get_images_url`返回的相同
- `rule: tuple, optional`: 允许下载的格式，默认为`('.png', '.jpg')`
- `path: str, optional`: 图片下载的路径，默认为`'download'`
- `timeout: int, optional`: 请求timeout, 默认为`60(s)`
- `concurrent: int, optional`: 并行下载的数量，默认为`100`

返回

- `success: int`: 下载成功的数量
- `failed: int`: 下载失败的数量

### 日志

可以设置日志的等级以及输出，具体请查看[logging](https://docs.python.org/3.8/library/logging.html)

```python
import logging
from BaiduImagesDownload.crawler import logging

# 设置日志的等级为DEBUG
# 默认为INFO
logger.setLevel(logging.DEBUG)

# 设置输出到文件
file_handler = logging.FileHandler('~/BaiduImagesDownload.log')
file_handler.setFormatter(logging.Formatter(
    '[%(asctime)s] [%(levelname)s] %(message)s')) # 设置输出格式
logger.addHandler(file_handler)
```

## 许可

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://github.com/YXL76/BaiduImagesDownload/blob/master/LICENSE)
