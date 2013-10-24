#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
@date: 2013-10-23
@author: shell.xu
'''
import os, sys
import subprocess
from os import path

global_configfile = '/etc/lxc/lxc.conf'

def read_config(filepath):
    cfg = {}
    with open(filepath, 'r') as fi:
        for line in fi:
            if line.startswith('#'): continue
            line = line.strip()
            if not line: continue
            v = line.split('=', 1)
            k, v = str(v[0]).strip(), str(v[1]).strip()
            if k not in cfg: cfg[k] = [v,]
            else: cfg[k].append(v)
    return cfg

def sub_config(cfg, prefix):
    return dict((k, v) for k, v in cfg.iteritems() if k.startswith(prefix))

def container_config(name):
    cfg = read_config(global_configfile)
    return read_config(path.join(cfg['lxcpath'][-1], name, 'config'))

def read_fstab(filepath):
    rslt = []
    with open(filepath, 'r') as fi:
        for line in fi:
            rslt.append(line.split()[:4])
    return rslt

def container_fstab(name):
    cfg, rslt = container_config(name), []
    if 'lxc.mount' in cfg:
        rslt.extend(read_fstab(cfg['lxc.mount'][-1]))
    for line in cfg.get('lxc.mount.entry', []):
        r = line.split()[:4]
        if not r[1].startswith('/'):
            r[1] = path.join(cfg['lxc.rootfs'][-1], r[1])
        rslt.append(r)
    return rslt

def clone(origin, name):
    cmd = ['sudo', 'lxc-clone', '-o', origin, '-n', name]
    return subprocess.check_call(cmd)

def create(template, name):
    cmd = ['sudo', 'lxc-create', '-t', template, '-n', name]
    return subprocess.check_call(cmd)

def destroy(name):
    cmd = ['sudo', 'lxc-destroy', '-n', name]
    return subprocess.check_call(cmd)

def ls():
    output = subprocess.check_output(['lxc-ls',])
    for m in output.split():
        yield m

def info(name):
    output = subprocess.check_output(['sudo', 'lxc-info', '-n', name])
    # TODO: cgroup count?
    return dict([i.strip() for i in line.split(':', 1)]
                for line in output.splitlines())

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
# lxc-ps
# lxc-wait
    
def main():
    cfg = container_config('mongo')
    print 'rootfs:'
    print cfg['lxc.rootfs']
    print 'network:'
    print sub_config(cfg, 'lxc.network')
    print 'cgroup:'
    print sub_config(cfg, 'lxc.cgroup')
    print 'mount:'
    print sub_config(cfg, 'lxc.mount')
    print
    print container_fstab('mongo')

if __name__ == '__main__': main()
