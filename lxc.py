#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
@date: 2013-10-23
@author: shell.xu
'''
import re, os, sys, logging
import subprocess
from os import path

global_configfile = '/etc/lxc/lxc.conf'
default_lxcpath = '/var/lib/lxc'

def check_call(name, cmd):
    cmd = ['sudo', 'lxc-attach', '-n', name, '--'] + cmd
    return subprocess.check_call(cmd)

def check_output(name, cmd):
    cmd = ['sudo', 'lxc-attach', '-n', name, '--'] + cmd
    return subprocess.check_output(cmd)

# config methods

def read_config(filepath, spliter='='):
    cfg = {}
    with open(filepath, 'r') as fi:
        for line in fi:
            if line.startswith('#'): continue
            line = line.strip()
            if not line: continue
            v = line.split(spliter, 1)
            k, v = str(v[0]).strip(), str(v[1]).strip()
            if k not in cfg: cfg[k] = [v,]
            else: cfg[k].append(v)
    return cfg

def sub_config(cfg, prefix):
    return dict((k[len(prefix):].lstrip('.'), v) for k, v in cfg.iteritems()
                if k.startswith(prefix))

def simple_config(cfg):
    return dict((k, v[-1]) for k, v in cfg.iteritems())

def global_config():
    try: return read_config(global_configfile)
    except IOError: return {'lxcpath': [default_lxcpath,]}

def container_config(name):
    cfg = global_config()
    if not path.isdir(path.join(cfg['lxcpath'][-1], name)):
        raise Exception('invaild container %s' % name)
    return read_config(path.join(cfg['lxcpath'][-1], name, 'config'))

def read_fstab(filepath):
    rslt = []
    with open(filepath, 'r') as fi:
        for line in fi:
            rslt.append(line.split()[:4])
    return rslt

def container_fstab(name):
    cfg, rslt = container_config(name), []
    rootfs = cfg['lxc.rootfs'][-1]
    if 'lxc.mount' in cfg:
        for r in read_fstab(cfg['lxc.mount'][-1]):
            if not r: continue
            if r[1].startswith(rootfs):
                r[1] = r[1][len(rootfs):]
                rslt.append(r)
            else: logging.warning('container %s rule not in rootfs: %s' % (name, str(r)))
    for line in cfg.get('lxc.mount.entry', []):
        rslt.append(line.split()[:4])
    return rslt

def aufs_stack(fstab):
    i = fstab[0]
    if i[1] != '/' or i[2] != 'aufs': return
    for o in i[3].split(','):
        if not o.startswith('br='): continue
        for p in o[3:].split(':'):
            if '=' in p:
                yield p.split('=', 1)
            else: p, 'rw'

# image methods

def clone(origin, name, fast=False):
    cmd = ['sudo', 'lxc-clone' + '-aufs' if aufs else '', '-o', origin, '-n', name]
    return subprocess.check_call(cmd)

def create(template, name):
    cmd = ['sudo', 'lxc-create', '-t', template, '-n', name]
    return subprocess.check_call(cmd)

def destroy(name):
    cmd = ['sudo', 'lxc-destroy', '-n', name]
    return subprocess.check_call(cmd)

def merge(name):
    cfg = container_config(name)
    rootfs = cfg['lxc.rootfs'][-1]
    fstab = container_fstab(name)
    aufs = list(aufs_stack(fstab))
    for i in aufs: subprocess.check_call(['rsync', '-Hax', i[0], rootfs])
    # remove aufs in fstab
    # remove rw?

# info methods

def ls():
    output = subprocess.check_output(['lxc-ls',])
    for m in output.split():
        yield m

def info(name):
    output = subprocess.check_output(['sudo', 'lxc-info', '-n', name])
    return dict([i.strip() for i in line.split(':', 1)]
                for line in output.splitlines())

def cgroupinfo(name):
    rslt, basedir = {}, '/sys/fs/cgroup/lxc/%s/' % name
    try:
        rslt.update(
            simple_config(
                read_config(basedir + 'cpuacct.stat', spliter=' ')))
        with open(basedir + 'cpuacct.usage', 'r') as fi:
            rslt['cpu.usage'] = int(fi.read().strip())
            rslt['cpu_usage'] = rslt['cpu.usage'] / 1000000000
        with open(basedir + 'cgroup.procs', 'r') as fi:
            rslt['pids'] = [int(i.strip()) for i in fi.read().split()]
    except IOError: pass
    try:
        with open(basedir + 'memory.usage_in_bytes', 'r') as fi:
            rslt['memory'] =  int(fi.read().strip())
        rslt.update(
            simple_config(
                read_config(basedir + 'memory.stat', spliter=' ')))
    except IOError: pass
    return rslt

def ps(name):
    output = subprocess.check_output(['sudo', 'lxc-ps', '-n', name, 'auxf'])
    for line in output.splitlines():
        if line.startswith('CONTAINER'): continue
        i = line.strip().split(None, 10)
        i.extend(i.pop(10).split(' ', 1))
        yield i[1:12]

def df(name, all=False):
    if all:
        cfg = global_config()
        if not path.isdir(path.join(cfg['lxcpath'][-1], name)):
            raise Exception('invaild container %s' % name)
        p = path.join(cfg['lxcpath'][-1], name)
    else:
        cfg = container_config(name)
        p = cfg['lxc.rootfs'][-1]
    output = subprocess.check_output(['sudo', 'du', '-sk', p])
    return int(output.split()[0].strip())

# container methods

def start(name, daemon=True):
    cmd = ['sudo', 'lxc-start', '-n', name]
    if daemon: cmd.append('-d')
    return subprocess.check_call(cmd)

def stop(name):
    cmd = ['sudo', 'lxc-stop', '-n', name]
    return subprocess.check_call(cmd)

def shutdown(name, wait=True, reboot=False):
    cmd = ['sudo', 'lxc-shutdown', '-n', name]
    if wait: cmd.append('-w')
    if reboot: cmd.append('-r')
    return subprocess.check_call(cmd)

# lxc-kill
# lxc-execute

# lxc-freeze
# lxc-unfreeze

# lxc-wait

re_inet = re.compile('inet (\S*).*')
def ipaddr(name, dev=''):
    cmd = ['ip', 'addr', 'show']
    if dev: cmd.append(dev)
    for line in check_output(name, cmd).splitlines():
        line = line.strip()
        m = re_inet.match(line)
        if not m: continue
        i = m.group(1).split('/')
        if i[0] in ('127.0.0.1',): continue
        yield i[0], int(i[1])

def main():
    pass

if __name__ == '__main__': main()
