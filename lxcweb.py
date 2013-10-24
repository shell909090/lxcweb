#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
@date: 2013-10-24
@author: shell.xu
'''
import os, sys, json
import web
import lxc

rander = web.config.render

# TODO: authorized

def readable_size(i):
    F = ['B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB', 'NMB']
    if i is None: return 'no size'
    j, i = 0, int(i)
    while i > 1024:
        i >>= 10
        j += 1
    return '%d %s' % (i, F[j])

def network_set(cfg):
    cfg = lxc.sub_config(cfg, 'lxc.network')
    return '%s(%s)' % (cfg['type'][-1], cfg['link'][-1])

def fullinfo():
    for v in lxc.ls():
        info = lxc.info(v)
        if info['state'] == 'RUNNING':
            info.update(lxc.status(v))
        cfg = lxc.container_config(v)
        info['netset'] = network_set(cfg)
        info.update(cfg)
        yield v, info

# info actions

class Home(object):
    def GET(self):
        return rander.home(infos=dict(fullinfo()), rs=readable_size)

class List(object):
    def GET(self):
        return json.dumps(dict(fullinfo()))

class Info(object):
    def GET(self, name):
        ps, info = [], lxc.info(name)
        if info['state'] == 'RUNNING':
            info.update(lxc.status(name))
        return rander.info(nm=name, info=info, rs=readable_size)

class Config(object):
    def GET(self, name):
        cfg = lxc.container_config(name)
        fstab = lxc.container_fstab(name)
        return rander.config(nm=name, cfg=cfg, fstab=fstab)

class Cfg(object):
    def GET(self, name):
        return json.dumps(lxc.container_config(name))

class Ps(object):
    def GET(self, name):
        info = lxc.info(name)
        if info['state'] != 'RUNNING': return 'status not right'
        return rander.ps(nm=name, ps=list(lxc.ps(name)))

class Mount(object):
    def GET(self, name):
        return json.dumps(lxc.container_fstab(name))

# image actions

class Clone(object):
    def GET(self, origin, name):
        lxc.clone(origin, name)
        return web.seeother('/')

class Create(object):
    def GET(self, origin, name):
        lxc.Create(origin, name)
        return web.seeother('/')

class Destory(object):
    def GET(self, name):
        lxc.Destory(name)
        return web.seeother('/')

# container actions

class Start(object):
    def GET(self, name):
        info = dict((v, lxc.info(v)) for v in lxc.ls())
        if name not in info:
            return json.dumps({'msg': 'invaild name %s' % name})
        if info[name]['state'] != "STOPPED":
            return json.dumps({'msg': '%s not stopped' % name})
        lxc.start(name)
        return web.seeother('/')

class Stop(object):
    def GET(self, name):
        info = dict((v, lxc.info(v)) for v in lxc.ls())
        if name not in info:
            return json.dumps({'msg': 'invaild name %s' % name})
        if info[name]['state'] != "RUNNING":
            return json.dumps({'msg': '%s not running' % name})
        lxc.stop(name)
        return web.seeother('/')

class Shutdown(object):
    def GET(self, name):
        info = dict((v, lxc.info(v)) for v in lxc.ls())
        if name not in info:
            return json.dumps({'msg': 'invaild name %s' % name})
        if info[name]['state'] != "RUNNING":
            return json.dumps({'msg': '%s not running' % name})
        lxc.shutdown(name)
        return web.seeother('/')

class Reboot(object):
    def GET(self, name):
        info = dict((v, lxc.info(v)) for v in lxc.ls())
        if name not in info:
            return json.dumps({'msg': 'invaild name %s' % name})
        if info[name]['state'] != "RUNNING":
            return json.dumps({'msg': '%s not running' % name})
        lxc.shutdown(name, reboot=True)
        return web.seeother('/')

# runtime actions

class Attach(object):
    def POST(self, name):
        cmd = web.data()
        web.header('Content-Type', 'text/plain')
        return lxc.check_output(name, cmd)

urls = (
    # info actions
    '/', Home,
    '/info/(.*)', Info,
    '/config/(.*)', Config,
    '/ps/(.*)', Ps,
    '/list', List,
    '/cfg/(.*)', Cfg,
    '/mount/(.*)', Mount,

    # image actions
    '/clone/(.*)/(.*)', Clone,
    '/create/(.*)/(.*)', Create,
    '/destory/(.*)', Destory,
    
    # container actions
    '/start/(.*)', Start,
    '/stop/(.*)', Stop,
    '/shutdown/(.*)', Shutdown,
    '/reboot/(.*)', Reboot,

    # runtime actions
    '/attach/(.*)', Attach,
)
