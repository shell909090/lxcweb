#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
@date: 2013-10-24
@author: shell.xu
'''
import os, sys, json, urlparse
import web
import lxc

def httperr(msg):
    raise web.InternalError(json.dumps({'msg': msg}))

def state_check(name, st, exist=True):
    if exist and name not in list(lxc.ls()):
        httperr('%s not exist' % name)
    info = lxc.info(name)
    if st and info['state'] != st:
        httperr('%s not %s' % (name, st.lower()))
    return info

def jsondec(func):
    def inner(self, *p):
        obj = func(self, *p)
        web.header("Content-Type", "application/json")
        return json.dumps(obj)
    return inner

# info actions

class ListJson(object):
    @jsondec
    def GET(self):
        infos = {}
        for name in lxc.ls():
            info = lxc.info(name)
            if info['state'] == 'RUNNING':
                info.update(lxc.cgroupinfo(name))
            infos[name] = info
        return infos

class InfoJson(object):
    @jsondec
    def GET(self, name):
        info = lxc.info(name)
        if info['state'] == 'RUNNING':
            info.update(lxc.cgroupinfo(name))
            info['ipaddr'] = list(lxc.ipaddr(name))
        info['diskusage'] = lxc.df(name) / 1024
        try:
            info['comment'] = lxc.read_comment(name)
        except IOError: pass
        return info

class PsJson(object):
    @jsondec
    def GET(self, name):
        info = state_check(name, 'RUNNING')
        return list(lxc.ps(name))

class ConfigJson(object):
    @jsondec
    def GET(self, name):
        return lxc.container_config(name)

class FstabJson(object):
    @jsondec
    def GET(self, name):
        fstab = lxc.container_fstab(name)
        return {'fstab': fstab, 'aufs': list(lxc.aufs_stack(fstab))}

# image actions

class Clone(object):
    def GET(self, origin, name):
        form = web.input()
        if name in list(lxc.ls()):
            httperr('%s exist' % name)
        if origin not in list(lxc.ls()):
            httperr('%s not exist' % origin)
        lxc.clone(origin, name)
        if form.get('run'): lxc.start(name)
        return web.seeother('/')

class Create(object):
    def GET(self, name):
        form = web.input()
        template = form.get('template') or 'debian'
        if name in list(lxc.ls()):
            httperr('%s exist' % name)
        lxc.Create(template, name)
        return web.seeother('/')

class Destroy(object):
    def GET(self, name):
        info = state_check(name, None)
        if info['state'] == 'RUNNING': lxc.stop(name)
        lxc.destroy(name)
        return web.seeother('/')

# container actions

class Start(object):
    def GET(self, name):
        state_check(name, 'STOPPED')
        lxc.start(name)
        return web.seeother('/')

class Stop(object):
    def GET(self, name):
        state_check(name, 'RUNNING')
        lxc.stop(name)
        return web.seeother('/')

class Shutdown(object):
    def GET(self, name):
        state_check(name, 'RUNNING')
        lxc.shutdown(name)
        return web.seeother('/')

class Reboot(object):
    def GET(self, name):
        state_check(name, 'RUNNING')
        lxc.shutdown(name, reboot=True)
        return web.seeother('/')

class Freeze(object):
    def GET(self, name):
        state_check(name, 'RUNNING')
        lxc.freeze(name)
        return web.seeother('/')

# freeze?
class Unfreeze(object):
    def GET(self, name):
        state_check(name, 'RUNNING')
        lxc.unfreeze(name)
        return web.seeother('/')

# runtime actions

class Attach(object):
    def POST(self, name):
        cmd = web.data()
        if cmd.startswith('cmd='):
            cmd = urlparse.parse_qs(cmd)['cmd'][0]
        web.header('Content-Type', 'text/plain')
        return lxc.attach_check_output(name, cmd.split())
