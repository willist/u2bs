import os
import shutil
import urllib2
import unittest
from u2bs import CacheHandler, ThrottlingProcessor


class Tests(unittest.TestCase):
    def setUp(self):
        # Clearing cache
        if os.path.exists(".urllib2cache"):
            shutil.rmtree(".urllib2cache")

        # Clearing throttling timeouts
        t = ThrottlingProcessor()
        t.lastRequestTime.clear()

        self.path = 'https://www.python.org/'
        self.cache_header = 'x-fs-cache'
        self.throttling_header = 'x-throttling'

    def testCache(self):
        opener = urllib2.build_opener(CacheHandler(".urllib2cache"))

        resp = opener.open(self.path)
        self.assert_(self.cache_header not in resp.info())

        resp = opener.open(self.path)
        self.assert_(self.cache_header in resp.info())

    def testThrottle(self):
        opener = urllib2.build_opener(ThrottlingProcessor(5))

        resp = opener.open(self.path)
        self.assert_(self.throttling_header not in resp.info())

        resp = opener.open(self.path)
        self.assert_(self.throttling_header in resp.info())

    def testCombined(self):
        opener = urllib2.build_opener(
            CacheHandler(".urllib2cache"), ThrottlingProcessor(1))

        resp = opener.open(self.path)
        self.assert_(self.cache_header not in resp.info())
        self.assert_(self.throttling_header not in resp.info())

        resp = opener.open(self.path)
        self.assert_(self.cache_header in resp.info())
        self.assert_(self.throttling_header not in resp.info())
