# -*- coding: utf-8 -*-

import os
import re
import unittest


class StyleTests(unittest.TestCase):

    def test(self):
        for name in self.getFiles():
            with open(name, 'r') as f:
                self.doTest(name, f.read())


    def getFiles(self):
        for path, directoryNames, fileNames in os.walk('.'):
            for name in fileNames:
                if name.endswith('.py'):
                    yield os.path.join(path, name)


    def doTest(self, name, text):
        for expression, message in self.TESTS:
            match = re.search(expression, text)
            if match:
                line = text.count('\n', 0, match.start() + 1) + 1
                groups = {}
                for index, group in enumerate(match.groups(), start=1):
                    groups[str(index)] = group
                message = message % groups
                assert False, ('"%s" in %s, line %d' % (message, name, line))


    # FIXME: Fails for issues in the last line.
    TESTS = (
        (r'\t', 'tab used'),
        (r'\n.{80,}\n', 'line too long'),
        (r' \n', 'trailing space'),
        (r'def __init__\(.*\):\n\s*"""\n?Create', '__init__ does not create'),
        (r'(?i)meas[s]ur', "it's 'mea*su*re', not 'mea*ss*ure'"),
        (r'(?i)measur[m]', "it's 'measur*e*ment', not 'measur**ment'"),
        (r'(?i)\btupel\b', "it's 'tup*le*', not 'tup*el*'"),
        (r'`(True|False|None)`[^`]', '%(1)s in single backticks '),
        (r"""\n[^#].*?[^'"*]NOS[E][^'"*]""", r"unitalicized 'NOSE'"),
        (r'(?i)read(?: |\n\s*)only', "it's read-only, with a hyphen"),
        (r'(?i)\ban(?: |\n\s*(?:#:?\s*)?)'
            '(?::\w+:`(?:[^aeiou~]|~(?:\w|\.)*\.[^aeiou]\w*`)'
            '|(?!fci|xml|x11)\w(?<![aeiou]))',
            "questionable 'an'"),
        (r'(?i)\ba(?: |\n\s*(?:#:?\s*)?)'
            '(?::\w+:`(?:[aeiou]|~(?:\w|\.)*\.[aeiou]\w*`)'
            '|(?:(?=fci|xml|x11)|(?!use|usage)[aeiou]))',
            "questionable 'a'"),
    )
