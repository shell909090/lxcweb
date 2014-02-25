#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
@date: 2013-10-24
@author: shell.xu
'''
import re, os, sys, json, urlparse, subprocess
import web
import lxc

CHUNKSIZE = 8192

def httperr(msg):
    raise web.InternalError(json.dumps({'msg': msg}))

def state_check(name, st, exist=True):
    if exist and name not in lxc.ls():
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

re_name = re.compile('[a-zA-Z0-9_]{1,20}')
def name_validation(name):
    return re.match(name) is not None

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
        if not lxc.name_validation(name):
            return 'invalid name'
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
        if not lxc.name_validation(name):
            return 'invalid name'
        info = state_check(name, 'RUNNING')
        return list(lxc.ps(name))

class ConfigJson(object):
    @jsondec
    def GET(self, name):
        if not lxc.name_validation(name):
            return 'invalid name'
        return lxc.container_config(name)

# image actions

class Clone(object):
    def GET(self, origin, name):
        if not lxc.name_validation(name):
            return 'invalid name'
        form = web.input()
        if name in lxc.ls():
            httperr('%s exist' % name)
        if origin not in lxc.ls():
            httperr('%s not exist' % origin)
        lxc.clone(origin, name)
        if form.get('run'): lxc.start(name)
        return web.seeother('/')

class Create(object):
    def GET(self, name):
        if not lxc.name_validation(name):
            return 'invalid name'
        form = web.input()
        template = form.get('template') or 'debian'
        if name in lxc.ls():
            httperr('%s exist' % name)
        lxc.Create(template, name)
        return web.seeother('/')

class Destroy(object):
    def GET(self, name):
        if not lxc.name_validation(name):
            return 'invalid name'
        info = state_check(name, None)
        if info['state'] == 'RUNNING': lxc.stop(name)
        lxc.destroy(name)
        return web.seeother('/')

class Export(object):
    def GET(self, name):
        if not lxc.name_validation(name):
            yield 'invalid name'
            return
        cfg = lxc.container_config(name)
        rootfs = cfg['lxc.rootfs'][-1]
        p = subprocess.Popen(['sudo', 'tar', 'cz', rootfs],
                             stdout=subprocess.PIPE)
        web.header("Content-Type", "application/octet-stream")
        web.header("Content-Disposition",
                   "attachment; filename=%s.tar.gz" % name)
        d = p.stdout.read(CHUNKSIZE)
        while d:
            yield d
            d = p.stdout.read(CHUNKSIZE)

# TODO:
class Import(object):
    ''' WARN: this operator is dangerous '''
    def POST(self, name):
        if not lxc.name_validation(name):
            return 'invalid name'
        form = web.input(file={})
        cfg = lxc.container_config(name)
        rootfs = cfg['lxc.rootfs'][-1]
        p = subprocess.Popen(['sudo', 'tar', 'cz', rootfs],
                             stdin=subprocess.PIPE)
        d = form['file'].file.read(CHUNKSIZE)
        while d:
            p.stdin.write(d)
            d = form['file'].file.read(CHUNKSIZE)
        return web.seeother('/')

# container actions

class Start(object):
    def GET(self, name):
        if not lxc.name_validation(name):
            return 'invalid name'
        state_check(name, 'STOPPED')
        lxc.start(name)
        return web.seeother('/')

class Stop(object):
    def GET(self, name):
        if not lxc.name_validation(name):
            return 'invalid name'
        state_check(name, 'RUNNING')
        lxc.stop(name)
        return web.seeother('/')

class Shutdown(object):
    def GET(self, name):
        if not lxc.name_validation(name):
            return 'invalid name'
        state_check(name, 'RUNNING')
        lxc.shutdown(name)
        return web.seeother('/')

class Reboot(object):
    def GET(self, name):
        if not lxc.name_validation(name):
            return 'invalid name'
        state_check(name, 'RUNNING')
        lxc.shutdown(name, reboot=True)
        return web.seeother('/')

class Freeze(object):
    def GET(self, name):
        if not lxc.name_validation(name):
            return 'invalid name'
        state_check(name, 'RUNNING')
        lxc.freeze(name)
        return web.seeother('/')

class Unfreeze(object):
    def GET(self, name):
        if not lxc.name_validation(name):
            return 'invalid name'
        state_check(name, 'RUNNING')
        lxc.unfreeze(name)
        return web.seeother('/')

# runtime actions

class Attach(object):
    def POST(self, name):
        if not lxc.name_validation(name):
            return 'invalid name'
        cmd = web.data()
        if cmd.startswith('cmd='):
            cmd = urlparse.parse_qs(cmd)['cmd'][0]
        web.header('Content-Type', 'text/plain')
        return lxc.attach_check_output(name, cmd.split())
