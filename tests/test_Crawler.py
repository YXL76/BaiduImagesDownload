import sys
from os import getcwd
from json import loads

sys.path.append(getcwd())

from BaiduImagesDownload.crawler import Crawler


def test_decode_objurl():
    assert Crawler.decode_objurl(
        'ippr_z2C$qAzdH3FAzdH3Fckalbbjclcddc_z&e3Bv1g_z&e3Bf5i7vf_z&e3Bv54AzdH3Ft4w2jfAzdH3Fdadaac89AzdH3F8dbw8dbajvdc9knvbb091m0blbdnu910_z&e3B3rj2') == 'http://5b0988e595225.cdn.sohucs.com/images/20200514/128a1280ec254b3c8874d6789823f4d7.jpeg'


def test_solve_imgdata():
    url = Crawler.solve_imgdata(
        loads(
            r"""{"thumbURL": "thumbURL","middleURL": "middleURL","replaceUrl": [{"ObjURL": "ObjURL-0","FromURL": "FromURL-0"},{"ObjURL": "ObjURL-1","FromURL": "FromURL-1"}]}""", strict=False),
        True)
    assert url['obj_url'][0] == 'ObjURL-1'
    assert url['obj_url'][1] == 'middleURL'
    assert url['obj_url'][2] == 'thumbURL'
    assert url['from_url'][0] == 'FromURL-1'
    assert url['from_url'][1] == ''
    assert url['from_url'][2] == ''


def test_get_images_url():
    pass


def test_download_images():
    pass
