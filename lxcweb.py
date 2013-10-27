#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
@date: 2013-10-24
@author: shell.xu
'''
import os, sys, json, urlparse
import web
import lxc

rander = web.config.render

# TODO: authorized

def httperr(msg):
    raise web.InternalError(json.dumps({'msg': msg}))

def state_check(name, st, exist=True):
    if exist and name not in list(lxc.ls()):
        httperr('%s not exist' % name)
    info = lxc.info(name)
    if st and info['state'] != st:
        httperr('%s not %s' % (name, st.lower()))
    return info

def readable_size(i, tgt=None):
    F = ['B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB', 'NMB']
    if i is None: return None
    if tgt: tgt = F.index(tgt)
    if tgt == -1: tgt = None
    j, i = 0, int(i)
    while i > 1024:
        i >>= 10
        j += 1
        if tgt and j == tgt: break
    return '%d %s' % (i, F[j])

def fullinfo():
    for v in lxc.ls():
        info = lxc.info(v)
        if info['state'] == 'RUNNING':
            info.update(lxc.cgroupinfo(v))
            info['ipaddr'] = list(lxc.ipaddr(v))
        yield v, info

# info actions

class ListJson(object):
    def GET(self):
        web.header("Content-Type", "application/json")
        return json.dumps(dict(fullinfo()))

class Home(object):
    def GET(self):
        return rander.home(infos=dict(fullinfo()), rs=readable_size)

class InfoJson(object):
    def GET(self, name):
        ps, info = [], lxc.info(name)
        if info['state'] == 'RUNNING':
            info.update(lxc.cgroupinfo(name))
        info['diskusage'] = lxc.df(name, True) / 1024
        web.header("Content-Type", "application/json")
        return json.dumps(info)

class Info(object):
    def GET(self, name):
        ps, info = [], lxc.info(name)
        if info['state'] == 'RUNNING':
            info.update(lxc.cgroupinfo(name))
        info['diskusage'] = lxc.df(name, True) / 1024
        return rander.info(nm=name, info=info, rs=readable_size)

class PsJson(object):
    def GET(self, name):
        info = state_check(name, 'RUNNING')
        web.header("Content-Type", "application/json")
        return json.dumps(list(lxc.ps(name)))

class Ps(object):
    def GET(self, name):
        info = state_check(name, 'RUNNING')
        return rander.ps(nm=name, ps=list(lxc.ps(name)))

class ConfigJson(object):
    def GET(self, name):
        web.header("Content-Type", "application/json")
        return json.dumps(lxc.container_config(name))

class FstabJson(object):
    def GET(self, name):
        fstab = lxc.container_fstab(name)
        web.header("Content-Type", "application/json")
        return json.dumps({'fstab': fstab, 'aufs': list(lxc.aufs_stack(fstab))})

class Config(object):
    def GET(self, name):
        cfg = lxc.container_config(name)
        fstab = lxc.container_fstab(name)
        aufs = list(lxc.aufs_stack(fstab))
        return rander.config(nm=name, cfg=cfg, fstab=fstab, aufs=aufs)

# image actions

class Clone(object):
    def GET(self, origin, name):
        form = web.input()
        fast = form.get('mode').lower() == 'fast'
        if name in list(lxc.ls()):
            httperr('%s exist' % name)
        if origin not in list(lxc.ls()):
            httperr('%s not exist' % origin)
        lxc.clone(origin, name, fast)
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

class Merge(object):
    def GET(self, name):
        state_check(name, 'RUNNING')
        lxc.merge(name)
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

# runtime actions

class Attach(object):
    def POST(self, name):
        cmd = web.data()
        if cmd.startswith('cmd='):
            cmd = urlparse.parse_qs(cmd)['cmd'][0]
        web.header('Content-Type', 'text/plain')
        return lxc.check_output(name, cmd.split())
