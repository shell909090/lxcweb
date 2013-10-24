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
# TODO: wrapper

class Home(object):
    def GET(self):
        infos = {}
        for v in lxc.ls():
            infos[v] = lxc.info(v)
            if infos[v]['state'] == 'RUNNING':
                infos[v].update(lxc.status(v))
                infos[v]['processes'] = len(list(lxc.ps(v)))
        return rander.home(infos=infos)

class Info(object):
    def GET(self, name):
        info = lxc.info(name)
        ps, config, fstab = [], [], []
        if info['state'] == 'RUNNING':
            info.update(lxc.status(name))
            ps = list(lxc.ps(name))
            info['processes'] = len(ps)
        config = lxc.container_config(name)
        fstab = lxc.container_fstab(name)
        return rander.info(info=info, ps=ps, config=config,
                           fstab=fstab, rs=lxc.readable_size)

class List(object):
    def GET(self):
        infos = {}
        for v in lxc.ls():
            infos[v] = lxc.info(v)
            if infos[v]['state'] == 'RUNNING':
                infos[v].update(lxc.status(v))
                infos[v]['processes'] = len(list(lxc.ps(v)))
        return json.dumps(infos)

class Config(object):
    def GET(self, name):
        config = lxc.container_config(name)
        return json.dumps(config)

class Fstab(object):
    def GET(self, name):
        fstab = lxc.container_fstab(name)
        return json.dumps(fstab)

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

urls = (
    '/', Home,
    '/info/(.*)', Info,
    
    '/list', List,
    '/config/(.*)', Config,
    '/fstab/(.*)', Fstab,

    '/clone/(.*)/(.*)', Clone,
    '/create/(.*)/(.*)', Create,
    '/destory/(.*)', Destory,
    
    '/start/(.*)', Start,
    '/stop/(.*)', Stop,
    '/shutdown/(.*)', Shutdown,
    '/reboot/(.*)', Reboot,
)
