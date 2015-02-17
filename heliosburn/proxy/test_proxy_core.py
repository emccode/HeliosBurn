import unittest
from threading import Thread
import subprocess
import time
import testserver
import urllib2
from urllib2 import HTTPError
import logging


class TestServer(Thread):
    """
    Thread interface class to contain the CherryPy testserver.
    """
    def run(self):
        testserver.main()


class ProxyCoreTest(unittest.TestCase):
    """
    Unit tests of the proxycore component.
    These create and destroy temporary instances of both proxycore and testserver.py, if the ports are in use prior to
    the tests running, the tests will fail.
    """

    def setUp(self):
        """
        Create temporary testserver.py and proxycore.py instances
        """
        logging.warning("Spawning TestServer in a thread")
        self.testserver_thread = TestServer()
        self.testserver_thread.start()
        time.sleep(1)  # Let cherrypy engine thread start and begin listening

        logging.warning("Starting proxy_core")
        self.proxy_core_process = subprocess.Popen(["/usr/bin/python2.7", "proxy_core.py", "unittests"])  # TODO: fix this, obviously :)
        time.sleep(1)  # Let twisted factory begin listening

    def tearDown(self):
        """
        Tear down temporary testserver.py and proxycore.py instances
        """
        logging.warning("Shutting down TestServer gracefully")
        time.sleep(1)  # Let cherrypy engine be idle before sending /die
        urllib2.urlopen("http://127.0.0.1:8080/die")
        time.sleep(1)  # Let cherrypy thread exit cleanly

        self.proxy_core_process.kill()

    def test_proxy_200(self):
        """
        Test HTTP 200 from client->proxy->testserver
        """
        x = urllib2.urlopen("http://127.0.0.1:8880")
        self.assertEqual(x.msg, "OK")  # TODO: can urllib2 return the status_code(200) instead of "OK"?

    def test_proxy_400(self):
        """
        Test HTTP 404 from client->proxy->testserver
        """
        self.assertRaises(HTTPError, urllib2.urlopen, "http://127.0.0.1:8880/fail/404")

    def test_proxy_request_header(self):
        """
        Test for header injected into request, echo'd back by testserver.py
        """
        x = urllib2.urlopen("http://127.0.0.1:8880")
        body = x.fp.read()
        self.assertNotEquals(body.find('Unit-Test-Request'), -1)

    def test_proxy_response_header(self):
        """
        Test for header injected into response
        """
        x = urllib2.urlopen("http://127.0.0.1:8880")
        self.assertIn('Unit-Test-Response', x.headers)

    def test_proxy_request_body(self):
        """
        Test for string injected into request body, echo'd back by testserver.py
        """
        x = urllib2.urlopen("http://127.0.0.1:8880")
        body = x.fp.read()
        self.assertNotEquals(body.find('unit testing body request'), -1)

    def test_proxy_response_body(self):
        """
        Test for string injected into response body
        """
        x = urllib2.urlopen("http://127.0.0.1:8880")
        body = x.fp.read()
        self.assertNotEquals(body.find('unit testing body response'), -1)