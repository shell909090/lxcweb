#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
@date: 2013-10-24
@author: shell.xu
'''
import os, sys, json
import lxc

# TODO: authorized
# TODO: wrapper

class ListInfo(object):
    def GET(self):
        info = dict((v, lxc.info(v)) for v in lxc.ls())
        return json.dumps(info)

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
        return web.seeother('/list')

class Create(object):
    def GET(self, origin, name):
        lxc.Create(origin, name)
        return web.seeother('/list')

class Destory(object):
    def GET(self, name):
        lxc.Destory(name)
        return web.seeother('/list')

class Start(object):
    def GET(self, name):
        info = dict((v, lxc.info(v)) for v in lxc.ls())
        if name not in info:
            return json.dumps({'msg': 'invaild name %s' % name})
        if info[name]['state'] != "STOPPED":
            return json.dumps({'msg': '%s not stopped' % name})
        lxc.start(name)
        return web.seeother('/list')

class Stop(object):
    def GET(self, name):
        info = dict((v, lxc.info(v)) for v in lxc.ls())
        if name not in info:
            return json.dumps({'msg': 'invaild name %s' % name})
        if info[name]['state'] != "RUNNING":
            return json.dumps({'msg': '%s not running' % name})
        lxc.stop(name)
        return web.seeother('/list')

class Shutdown(object):
    def GET(self, name):
        info = dict((v, lxc.info(v)) for v in lxc.ls())
        if name not in info:
            return json.dumps({'msg': 'invaild name %s' % name})
        if info[name]['state'] != "RUNNING":
            return json.dumps({'msg': '%s not running' % name})
        lxc.shutdown(name)
        return web.seeother('/list')

class Reboot(object):
    def GET(self, name):
        info = dict((v, lxc.info(v)) for v in lxc.ls())
        if name not in info:
            return json.dumps({'msg': 'invaild name %s' % name})
        if info[name]['state'] != "RUNNING":
            return json.dumps({'msg': '%s not running' % name})
        lxc.shutdown(name, reboot=True)
        return web.seeother('/list')

urls = (
    '/list', ListInfo,
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
