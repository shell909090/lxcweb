#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
@date: 2011-05-05
@author: shell.xu
'''
import os, sys, web, base64, logging, ConfigParser
from os import path
from gevent.pywsgi import WSGIServer

def initlog(lv, logfile=None):
    rootlog = logging.getLogger()
    if logfile: handler = logging.FileHandler(logfile)
    else: handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter(
            '%(asctime)s,%(msecs)03d %(name)s[%(levelname)s]: %(message)s',
            '%H:%M:%S'))
    rootlog.addHandler(handler)
    rootlog.setLevel(lv)

def read_config(cfgpaths):
    cfg = ConfigParser.RawConfigParser(allow_no_value=True)
    cfg.read(cfgpaths)
    return dict(cfg.items('main')), dict(cfg.items('users'))

logger = logging.getLogger('main')
DEBUG = not path.isfile('RELEASE')
web.config.debug = DEBUG
web.config.rootdir = path.dirname(__file__)

def serve_file(filepath):
    class ServeFile(object):
        def GET(self):
            with open(filepath, 'rb') as fi:
                return fi.read()
    return ServeFile

def serve_path(dirname):
    class ServePath(object):
        def GET(self, p):
            with open(path.join(dirname, p), 'rb') as fi:
                return fi.read()
    return ServePath

import lxcweb
urls = (
    '/static/(.*)', serve_path('static/'),
    # info actions
    '/', serve_file('static/home.html'),
    '/list.json', lxcweb.ListJson,
    '/info/(.*).json', lxcweb.InfoJson,
    '/ps/(.*).json', lxcweb.PsJson,
    '/ps/.*', serve_file('static/ps.html'),
    '/config/(.*).json', lxcweb.ConfigJson,
    '/fstab/(.*).json', lxcweb.FstabJson,
    '/config/.*', serve_file('static/config.html'),

    # image actions
    '/clone/(.*)/(.*)', lxcweb.Clone,
    '/create/(.*)', lxcweb.Create,
    '/destroy/(.*)', lxcweb.Destroy,
    '/merge/(.*)', lxcweb.Merge,

    # container actions
    '/start/(.*)', lxcweb.Start,
    '/stop/(.*)', lxcweb.Stop,
    '/shutdown/(.*)', lxcweb.Shutdown,
    '/reboot/(.*)', lxcweb.Reboot,

    # runtime actions
    '/attach/(.*)', lxcweb.Attach,
)
app = web.application(urls)

def auth_proc(handler):
    if not web.config.users: return handler()
    auth = web.ctx.env.get('HTTP_AUTHORIZATION')
    if auth and auth.startswith('Basic '):
        auth = auth[6:]
        username, password = base64.decodestring(auth).split(':', 1)
        if username == web.config.users['username'] and \
           password == web.config.users['password']:
            return handler()
    web.header('WWW-Authenticate', 'Basic realm="user login"')
    web.ctx.status = '401 Unauthorized'
    return
app.add_processor(auth_proc)

if __name__ == '__main__':
    maincfg, web.config.users = read_config([
        'lxcweb.conf', '/etc/lxcweb/lxcweb.conf',])
    if web.config.rootdir: os.chdir(web.config.rootdir)
    WSGIServer(
        ('', int(maincfg.get('port') or 9981)),
        app.wsgifunc()).serve_forever()
else: application = app.wsgifunc()
