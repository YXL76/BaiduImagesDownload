# BaiduImagesDownload

[![Python package](https://github.com/YXL76/BaiduImagesDownload/workflows/Python%20package/badge.svg)](https://github.com/YXL76/BaiduImagesDownload/actions)
[![codecov](https://codecov.io/gh/YXL76/BaiduImagesDownload/branch/master/graph/badge.svg)](https://codecov.io/gh/YXL76/BaiduImagesDownload)
[![Codacy Badge](https://app.codacy.com/project/badge/Grade/0dce5ee6b45f427fa5aa782907408d19)](https://www.codacy.com/manual/YXL76/BaiduImagesDownload?utm_source=github.com&utm_medium=referral&utm_content=YXL76/BaiduImagesDownload&utm_campaign=Badge_Grade)

> `BaiduImagesDownload`是一个快速、简单百度图片爬取工具

```python
from BaiduImagesDownload import Crawler

net, num, urls = Crawler.get_images_url('二次元', 20)
Crawler.download_images(urls)
```

目录

- [BaiduImagesDownload](#baiduimagesdownload)
  - [安装](#安装)
  - [使用](#使用)
    - [基本](#基本)
    - [下载设置](#下载设置)
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
from BaiduImagesDownload import Crawler

# original为True代表优先下载原图
net, num, urls = Crawler.get_images_url('二次元', 20, original=True)
Crawler.download_images(urls)
```

### 下载设置

```python
from BaiduImagesDownload import Crawler

# rule设置允许的图片格式，默认为('.png', '.jpg')
# timeout为超时时间，默认为60(s)
net, num, urls = Crawler.get_images_url('二次元', 20)
Crawler.download_images(urls, rule=('.png', '.jpg'), timeout=60)
```

## 文档

### get_images_url

```python
class Crawler:

    @staticmethod
    def get_images_url(word: str, num: int, original: bool = True,
                       timeout: int = __CONCURRENT_TIMEOUT) -> (bool, bool, list):
```

参数

- `word: str`: 搜索关键词
- `num: int`: 搜索数量
- `original： bool, optional`：是否下原图，默认为`True`
- `timeout: int, optional`: 请求 timeout, 默认为`60(s)`

返回

- `net: bool`: 网络连接是否成功，成功为 True，失败为 False
- `num: bool`: 图片数量是否满足，满足为 True，不足为 False
- `urls: list`: 获取的 urls，每项为一个`dict`，其中有两个键`obj_url`，`from_url`。`obj_url`为对应图片的`url`，`from_url`为`Referer`

### download_images

```python
class Crawler:

    @staticmethod
    def download_images(urls: list, rule: tuple = ('.png', '.jpg'),
                        path: str = 'download', timeout: int = __CONCURRENT_TIMEOUT,
                        concurrent: int = __CONCURRENT_NUM, command: bool = True) -> (int, int):
```

参数

- `urls: list`: 需要爬的图片列表，格式与`get_images_url`返回的相同
- `rule: tuple, optional`: 允许下载的格式，默认为`('.png', '.jpg')`
- `path: str, optional`: 图片下载的路径，默认为`'download'`
- `timeout: int, optional`: 请求 timeout, 默认为`60(s)`
- `concurrent: int, optional`: 并行下载的数量，默认为`100`
- `command: bool, optional`: 是否在控制台显示进度条，默认为`True`

返回

- `success: int`: 下载成功的数量
- `failed: int`: 下载失败的数量

### 日志

可以设置日志的等级以及输出，具体请查看[logging](https://docs.python.org/3.8/library/logging.html)

```python
import logging
from BaiduImagesDownload import logger

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
