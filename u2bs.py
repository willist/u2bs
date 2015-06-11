"""http://code.activestate.com/recipes/491261/
"""
import httplib
import md5
import os
import StringIO
import time
import urllib2


class ThrottlingProcessor(urllib2.BaseHandler):
    """Prevents overloading the remote web server by delaying requests.

    Causes subsequent requests to the same web server to be delayed
    a specific amount of seconds. The first request to the server
    always gets made immediately.

    Note: this will block.
    """
    __shared_state = {}

    def __init__(self, throttleDelay=5):
        """The number of seconds to wait between subsequent requests"""
        # Using the Borg design pattern to achieve shared state
        # between object instances:
        self.__dict__ = self.__shared_state
        self.throttleDelay = throttleDelay
        if not hasattr(self, 'lastRequestTime'):
            self.lastRequestTime = {}

    def default_open(self, request):
        currentTime = time.time()

        delta = currentTime - self.lastRequestTime.get(request.host, 0)

        if delta < self.throttleDelay:
            self.throttleTime = self.throttleDelay - delta
            time.sleep(self.throttleTime)
        self.lastRequestTime[request.host] = currentTime

        return None

    def _response(self, request, response):
        if hasattr(self, 'throttleTime'):
            response.info().addheader(
                "x-throttling", "%s seconds" % self.throttleTime)
            del(self.throttleTime)
        return response

    http_response = https_response = _response


class CacheHandler(urllib2.BaseHandler):
    """Stores responses in a persistant on-disk cache.

    If a subsequent GET request is made for the same URL, the stored
    response is returned, saving time, resources and bandwith"""

    def __init__(self, cacheLocation):
        """The location of the cache directory"""
        self.cacheLocation = cacheLocation
        if not os.path.exists(self.cacheLocation):
            os.makedirs(self.cacheLocation)

    def default_open(self, request):
        if request.get_method() != "GET":
            return None

        full_url = request.get_full_url()

        if CachedResponse.ExistsInCache(self.cacheLocation, full_url):
            # print "CacheHandler: Returning CACHED response for %s" %
            # request.get_full_url()
            return CachedResponse(self.cacheLocation, request.get_full_url())
        else:
            return None # let the next handler try to handle the request

    def _response(self, request, response):
        if request.get_method() != "GET":
            return response

        if 'x-fs-cache' not in response.info():
            CachedResponse.StoreInCache(
                self.cacheLocation, request.get_full_url(), response)

        return response

    http_response = https_response = _response


class CachedResponse(StringIO.StringIO):
    """An urllib2.response-like object for cached responses.

    To determine wheter a response is cached or coming directly from
    the network, check the x-fs-cache header rather than the object type."""

    @staticmethod
    def FileNameGenerator(cacheLocation, url):
        hashed_url = md5.new(url).hexdigest()
        path = os.path.join(cacheLocation, hashed_url)
        headers_file = '{0}.headers'.format(path)
        body_file = '{0}.body'.format(path)

        return headers_file, body_file

    @staticmethod
    def ExistsInCache(cacheLocation, url):
        headers_file, body_file = CachedResponse.FileNameGenerator(
            cacheLocation, url)

        return (os.path.exists(headers_file) and os.path.exists(body_file))

    @staticmethod
    def StoreInCache(cacheLocation, url, response):
        headers_file, body_file = CachedResponse.FileNameGenerator(
            cacheLocation, url)

        f = open(headers_file, "w")
        headers = str(response.info())
        f.write(headers)
        f.close()

        f = open(body_file, "w")
        f.write(response.read())
        f.close()

    def __init__(self, cacheLocation, url, setCacheHeader=True):
        self.cacheLocation = cacheLocation
        hashed_url = md5.new(url).hexdigest()
        headers_file, body_file = CachedResponse.FileNameGenerator(
            cacheLocation, url)

        StringIO.StringIO.__init__(self, file(body_file).read())

        self.url = url
        self.code = 200
        self.msg = "OK"
        headerbuf = file(headers_file).read()

        if setCacheHeader:
            headerbuf += "x-fs-cache: %s/%s\r\n" % (
                self.cacheLocation, hashed_url)
        self.headers = httplib.HTTPMessage(StringIO.StringIO(headerbuf))

    def info(self):
        return self.headers

    def geturl(self):
        return self.url
