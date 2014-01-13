#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
@date: 2011-05-05
@author: shell.xu
@version: 0.8.1
'''
import os, sys, web, base64, getopt, logging, ConfigParser
from os import path
import utils, lxc, lxcweb

logger = logging.getLogger('main')
DEBUG = not path.isfile('RELEASE')
web.config.debug = DEBUG

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

def Authenticate(username, password):
    def auth(handler):
        auth = web.ctx.env.get('HTTP_AUTHORIZATION')
        if auth and auth.startswith('Basic '):
            user, passwd = base64.decodestring(auth[6:]).split(':', 1)
            if user == username and passwd == password:
                return handler()
        web.header('WWW-Authenticate', 'Basic realm="user login"')
        web.ctx.status = '401 Unauthorized'
        return
    return auth

def main():
    optlist, args = getopt.getopt(sys.argv[1:], 'c:hp:')
    optdict = dict(optlist)
    if '-h' in optdict:
        print main.__doc__
        return
    
    cfg = utils.getcfg(optdict.get('-c', [
        '/etc/lxcweb/lxcweb.conf', 'lxcweb.conf']))
    utils.initlog(cfg.get('log', 'loglevel'), cfg.get('log', 'logfile'))

    if cfg.has_section('lxc'):
        lxc.global_configfile = cfg.get('lxc', 'config')
        lxc.default_lxcpath = cfg.get('lxc', 'lxcpath')
        lxc.sudoflag = cfg.getboolean('lxc', 'sudo')

    # if web.config.rootdir: os.chdir(web.config.rootdir)
    static_path = None
    for p in ['static', '/usr/share/lxcweb/static']:
        if path.isdir(p):
            static_path = p
            break
    assert static_path is not None, "static path not exist."

    app = web.application((
        '/static/(.*)', serve_path(static_path),
        # info actions
        '/', serve_file(path.join(static_path, 'home.html')),
        '/list.json', lxcweb.ListJson,
        '/info/(.*).json', lxcweb.InfoJson,
        '/ps/(.*).json', lxcweb.PsJson,
        '/ps/.*', serve_file(path.join(static_path, 'ps.html')),
        '/config/(.*).json', lxcweb.ConfigJson,
        '/fstab/(.*).json', lxcweb.FstabJson,
        '/config/.*', serve_file(path.join(static_path, 'config.html')),

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
    ))

    kw = {}
    port = int(optdict.get('-p') or cfg.getint('main', 'port'))

    if cfg.has_section('ssl'):
        keyfile = cfg.get('ssl', 'key')
        certfile = cfg.get('ssl', 'cert')
        if path.exists(keyfile) and path.exists(certfile):
            kw = {'keyfile': keyfile, 'certfile': certfile}

    if cfg.has_section('users'):
        app.add_processor(Authenticate(
            cfg.get('users', 'username'), cfg.get('users', 'password')))
        
    from gevent.pywsgi import WSGIServer
    print 'service port :%d' % port
    WSGIServer(('', port), app.wsgifunc(), **kw).serve_forever()

if __name__ == '__main__':
    main()
