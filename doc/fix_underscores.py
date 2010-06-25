# -*- coding: utf-8 -*-

"""
Renames the ``_images`` and ``_static`` directories created by *Sphinx* into
``images`` and ``static`` and adjusts all links. That is necessary to use the
documentation as a GitHub Page since GitHub does not copy files beginning with
an underscore to the page directory.

The script isn't particularly elegant, but it works.
"""

import os
import re


def main():
    renamePaths()
    fixLinks()


def renamePaths():
    if os.path.exists('build/html/_images'):
        os.rename('build/html/_images', 'build/html/images')

    if os.path.exists('build/html/_static'):
        os.rename('build/html/_static', 'build/html/static')


def fixLinks():
    for root, dirs, files in os.walk('build/html'):
        for f in files:
            if f.endswith('.html'):
                fixLinksIn(root + '/' + f)


def fixLinksIn(f):
    with open(f, 'r') as inFile:
        contents = inFile.read()

    contents = re.sub('_(static|images)', '\\1', contents)

    with open(f, 'w') as outFile:
        outFile.write(contents)



if __name__ == '__main__':
    main()
