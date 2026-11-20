import base64
import json
import os
import sys
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from resources.lib import libremote  # noqa: E402

GOT = []


class FakeKodi(BaseHTTPRequestHandler):
    """a Kodi web server: user kodi / pass s3cret, answers the few methods the helper sends"""

    def log_message(self, *a):
        pass

    def do_POST(self):
        auth = self.headers.get('Authorization', '')
        if auth != 'Basic ' + base64.b64encode(b'kodi:s3cret').decode():
            self.send_response(401)
            self.end_headers()
            return
        if self.path != '/jsonrpc':
            self.send_response(404)
            self.end_headers()
            return
        body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        GOT.append(body)
        m = body['method']
        if m in ('VideoLibrary.Scan', 'AudioLibrary.Scan', 'VideoLibrary.Clean', 'AudioLibrary.Clean'):
            out = {'id': 1, 'jsonrpc': '2.0', 'result': 'OK'}
        elif m == 'Application.GetProperties':
            out = {'id': 1, 'jsonrpc': '2.0', 'result': {'name': 'Kodi', 'version': {'major': 21, 'minor': 2,
                                                                                   'tag': 'stable'}}}
        elif m == 'XBMC.GetInfoBooleans':
            out = {'id': 1, 'jsonrpc': '2.0', 'result': {'Library.IsScanningVideo': True}}
        else:
            out = {'id': 1, 'jsonrpc': '2.0', 'error': {'code': -32601, 'message': 'Method not found.'}}
        raw = json.dumps(out).encode()
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)


class LibRemoteTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.srv = HTTPServer(('127.0.0.1', 0), FakeKodi)
        cls.addr = '127.0.0.1:%d' % cls.srv.server_address[1]
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()

    def test_endpoint(self):
        self.assertEqual(libremote.endpoint('192.168.10.10:7080'), 'http://192.168.10.10:7080/jsonrpc')
        self.assertEqual(libremote.endpoint(' http://h:8080/ '), 'http://h:8080/jsonrpc')
        self.assertEqual(libremote.endpoint('https://h/jsonrpc'), 'https://h/jsonrpc')
        self.assertEqual(libremote.display('http://h:8080/jsonrpc'), 'h:8080')
        for bad in ('', '   ', 'ftp://h'):
            with self.assertRaises(libremote.RemoteError):
                libremote.endpoint(bad)

    def test_update_and_clean(self):
        del GOT[:]
        self.assertTrue(libremote.library(self.addr, 'kodi', 's3cret', 'update', 'video'))
        self.assertTrue(libremote.library('http://' + self.addr + '/', 'kodi', 's3cret', 'clean', 'music'))
        self.assertEqual([g['method'] for g in GOT], ['VideoLibrary.Scan', 'AudioLibrary.Clean'])
        self.assertEqual(GOT[1]['params'], {'showdialogs': True})

    def test_version_and_scanning(self):
        self.assertEqual(libremote.version(self.addr, 'kodi', 's3cret'), 'Kodi 21.2')
        self.assertTrue(libremote.scanning(self.addr, 'kodi', 's3cret', 'video'))

    def test_errors(self):
        with self.assertRaises(libremote.RemoteError) as c:
            libremote.version(self.addr, 'kodi', 'wrong')
        self.assertEqual(c.exception.kind, 'auth')
        with self.assertRaises(libremote.RemoteError) as c:
            libremote.call(self.addr, 'kodi', 's3cret', 'No.Such')
        self.assertEqual(c.exception.kind, 'rpc')
        with self.assertRaises(libremote.RemoteError) as c:
            libremote.version('127.0.0.1:1', 'kodi', 's3cret')
        self.assertEqual(c.exception.kind, 'net')


if __name__ == '__main__':
    unittest.main()
