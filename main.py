#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
@date: 2011-05-05
@author: shell.xu
@version: 0.8.1
'''
import os, sys, web, base64, getopt, logging, ConfigParser
from os import path
import utils

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

    # container actions
    '/start/(.*)', lxcweb.Start,
    '/stop/(.*)', lxcweb.Stop,
    '/shutdown/(.*)', lxcweb.Shutdown,
    '/reboot/(.*)', lxcweb.Reboot,
    '/freeze/(.*)', lxcweb.Freeze,
    '/unfreeze/(.*)', lxcweb.Unfreeze,

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

def main():
    optlist, args = getopt.getopt(sys.argv[1:], 'c:hp:')
    optdict = dict(optlist)
    if '-h' in optdict:
        print main.__doc__
        return
    
    if web.config.rootdir: os.chdir(web.config.rootdir)
    cfg = utils.getcfg(optdict.get('-c', [
        '/etc/lxcweb/lxcweb.conf', 'lxcweb.conf']))
    web.config.users = dict(cfg.items('users'))

    utils.initlog(cfg.get('log', 'loglevel'), cfg.get('log', 'logfile'))

    kw = {}
    port = int(optdict.get('-p') or cfg.getint('main', 'port'))
    if cfg.has_section('ssl'):
        keyfile = cfg.get('ssl', 'key')
        certfile = cfg.get('ssl', 'cert')
        if path.exists(keyfile) and path.exists(certfile):
            kw = {'keyfile': keyfile, 'certfile': certfile}
        app.add_processor(auth_proc)
        
    from gevent.pywsgi import WSGIServer
    print 'service port :%d' % port
    WSGIServer(('', port), app.wsgifunc(), **kw).serve_forever()
    
if __name__ == '__main__': main()
else: application = app.wsgifunc()
