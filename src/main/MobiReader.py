import shutil
from xml.dom import minidom

import mobi


class MobiReader:
    def __init__(self, mobi_path):
        tempdir, filepath = mobi.extract(mobi_path)

        dom = minidom.parse(f'{tempdir}/mobi7/content.opf')

        self.title = self.__get_text(dom, 'dc:title')
        self.authors = self.__get_text(dom, 'dc:creator', ', ')
        self.cover_tmp_path = f'{tempdir}/mobi7/{self.__get_cover(dom)}'
        self._dir = tempdir

    def __get_text(self, dom, tag, separator=''):
        results = []
        for node in dom.getElementsByTagName(tag):
            results.append(node.firstChild.data)
        return separator.join(results)

    def __get_cover(self, dom):
        for node in dom.getElementsByTagName('item'):
            if node.attributes['id'].value == 'cover_img':
                return node.attributes['href'].value
        for node in dom.getElementsByTagName('item'):
            if node.attributes['id'].value == 'item1':
                return node.attributes['href'].value
        return None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # shutil.rmtree(self._dir)
        pass
