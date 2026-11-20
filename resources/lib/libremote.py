# -*- coding: utf-8 -*-
"""Skin settings > Libraries > Update and clean on another Kodi (0.3.114, skin 0.56.53; no Kodi imports): the skin's
library update / clean go to another Kodi (a headless one, for instance) over its web server's JSON-RPC
(http://host:port/jsonrpc, HTTP basic login) instead of running here. tests/test_libremote.py."""
import base64
import json

try:
    from urllib.request import Request, urlopen
    from urllib.error import HTTPError, URLError
except ImportError:  # pragma: no cover
    Request = urlopen = HTTPError = URLError = None

KINDS = ('video', 'music')
# showdialogs: the other Kodi shows its own progress bar (top bar task) as when you start it there
METHODS = {('update', 'video'): ('VideoLibrary.Scan', {'showdialogs': True}),
           ('update', 'music'): ('AudioLibrary.Scan', {'showdialogs': True}),
           ('clean', 'video'): ('VideoLibrary.Clean', {'showdialogs': True}),
           ('clean', 'music'): ('AudioLibrary.Clean', {'showdialogs': True})}
SCANNING = {'video': 'Library.IsScanningVideo', 'music': 'Library.IsScanningMusic'}


class RemoteError(Exception):
    """kind: 'address' (no address set / unusable), 'auth' (401), 'net' (no answer), 'rpc' (an error answer)"""

    def __init__(self, kind, detail=''):
        Exception.__init__(self, '%s: %s' % (kind, detail))
        self.kind = kind
        self.detail = detail


def endpoint(address):
    """'192.168.10.10:8080', 'http://host:8080/' or 'http://host:8080/jsonrpc' -> 'http://host:8080/jsonrpc'"""
    a = (address or '').strip()
    if not a:
        raise RemoteError('address')
    if '://' not in a:
        a = 'http://' + a
    if not a.lower().startswith(('http://', 'https://')):
        raise RemoteError('address', a)
    a = a.rstrip('/')
    if not a.lower().endswith('/jsonrpc'):
        a += '/jsonrpc'
    return a


def display(address):
    """the address as the row shows it: without the scheme and /jsonrpc"""
    try:
        a = endpoint(address)
    except RemoteError:
        return ''
    return a.split('://', 1)[1][:-len('/jsonrpc')]


def payload(method, params=None, rid=1):
    body = {'jsonrpc': '2.0', 'method': method, 'id': rid}
    if params:
        body['params'] = params
    return json.dumps(body).encode('utf-8')


def call(address, user, password, method, params=None, timeout=8, opener=None):
    """the JSON-RPC result of method on the other Kodi; RemoteError when it cannot be had"""
    req = Request(endpoint(address), data=payload(method, params), headers={'Content-Type': 'application/json'})
    if user or password:
        token = base64.b64encode(('%s:%s' % (user or '', password or '')).encode('utf-8')).decode('ascii')
        req.add_header('Authorization', 'Basic ' + token)
    try:
        raw = (opener or urlopen)(req, timeout=timeout).read()
    except HTTPError as e:
        raise RemoteError('auth' if e.code == 401 else 'net', 'HTTP %d' % e.code)
    except (URLError, OSError, ValueError) as e:
        raise RemoteError('net', str(getattr(e, 'reason', e)))
    try:
        data = json.loads(raw.decode('utf-8'))
    except ValueError:
        raise RemoteError('rpc', 'not JSON-RPC')
    if 'error' in data:
        raise RemoteError('rpc', (data['error'] or {}).get('message', ''))
    return data.get('result')


def library(address, user, password, action, kind, opener=None):
    """send update / clean of the video / music library; True when the other Kodi said OK"""
    method, params = METHODS[(action, kind)]
    return call(address, user, password, method, params, opener=opener) == 'OK'


def version(address, user, password, opener=None):
    """'Kodi 21.2' (the other Kodi's name and version) - the connection test"""
    r = call(address, user, password, 'Application.GetProperties', {'properties': ['name', 'version']},
             opener=opener) or {}
    v = r.get('version') or {}
    tag = '' if v.get('tag') in (None, '', 'stable') else ' ' + str(v.get('tag'))
    return '%s %s.%s%s' % (r.get('name') or 'Kodi', v.get('major', '?'), v.get('minor', '?'), tag)


def scanning(address, user, password, kind, opener=None):
    r = call(address, user, password, 'XBMC.GetInfoBooleans', {'booleans': [SCANNING[kind]]}, opener=opener) or {}
    return bool(r.get(SCANNING[kind]))
