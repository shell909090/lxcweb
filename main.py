#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
@date: 2011-05-05
@author: shell.xu
'''
import os, sys, web, base64, logging
from os import path

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

logger = logging.getLogger('main')
DEBUG = not path.isfile('RELEASE')
web.config.debug = DEBUG
web.config.rootdir = path.dirname(__file__)
web.config.username = 'admin'
web.config.password = 'admin123'

def serve_file(filepath):
    class ServeFile(object):
        def GET(self):
            with open(filepath) as fi:
                return fi.read()
    return ServeFile

import lxcweb
urls = (
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
    auth = web.ctx.env.get('HTTP_AUTHORIZATION')
    if auth and auth.startswith('Basic '):
        auth = auth[6:]
        username, password = base64.decodestring(auth).split(':', 1)
        if username == web.config.username and password == web.config.password:
            return handler()
    web.header('WWW-Authenticate', 'Basic realm="user login"')
    web.ctx.status = '401 Unauthorized'
    return
app.add_processor(auth_proc)

# if web.config.get('sesssion') is None:
#     web.config.session = web.session.Session(
#         app, web.session.DBStore(web.config.db, 'sessions'))

if __name__ == '__main__':
    if len(sys.argv) > 1:
        cmd = sys.argv.pop(1)
        if cmd == 'profile':
            app.run(web.profiler)
        elif cmd == 'test':
            from test import tester
            tester.testall(app)
    else: app.run()
else: application = app.wsgifunc()
