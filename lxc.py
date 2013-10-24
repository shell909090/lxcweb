#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
@date: 2013-10-23
@author: shell.xu
'''
import os, sys, logging
import subprocess
from os import path

global_configfile = '/etc/lxc/lxc.conf'

def readable_size(i):
    F = ['B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB', 'NMB']
    j, i = 0, int(i)
    while i > 1024:
        i >>= 10
        j += 1
    return '%d %s' % (i, F[j])

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
    try: cfg = read_config(global_configfile)
    except IOError: return {'lxcpath': ['/var/lib/lxc',]}

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

def container_net(cfg):
    cfg = sub_config(cfg, 'lxc.network')
    type = cfg.get('type', ['empty',])[-1]
    if type == 'empty':
        return 'no network'
    elif type == 'veth':
        return simple_config(cfg)
    else: raise Exception('not support yet')

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
    return dict([i.strip() for i in line.split(':', 1)]
                for line in output.splitlines())

def status(name):
    rslt = {}
    try:
        with open('/sys/fs/cgroup/lxc/%s/memory.usage_in_bytes' % name, 'r') as fi:
            rslt['memory'] =  int(fi.read().strip())
            rslt['memstr'] = readable_size(rslt['memory'])
        rslt.update(
            simple_config(
                read_config('/sys/fs/cgroup/lxc/%s/cpuacct.stat' % name, spliter=' ')))
        with open('/sys/fs/cgroup/lxc/%s/cpuacct.usage' % name, 'r') as fi:
            rslt['cpu.usage'] = int(fi.read().strip())
            rslt['cpu_usage'] = rslt['cpu.usage'] / 1000000000
        rslt.update(
            simple_config(
                read_config('/sys/fs/cgroup/lxc/%s/memory.stat' % name, spliter=' ')))
    except IOError: pass
    return rslt

def ps(name):
    output = subprocess.check_output(['sudo', 'lxc-ps', '-n', name, 'u'])
    for line in output.splitlines():
        if line.startswith('CONTAINER'): continue
        i = line.strip().split()
        i[11] = ' '.join(i[11:])
        yield i[1:12]

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

def main():
    cfg = container_config(sys.argv[1])
    print 'rootfs:'
    print '\t', cfg['lxc.rootfs'][-1]
    print 'network:'
    print '\t', container_net(cfg)
    print 'fstab:'
    for r in container_fstab(sys.argv[1]):
        print '\t', '\t'.join(r)
    i = info(sys.argv[1])
    print 'info:'
    print '\t', i
    print 'memory:'
    print '\t', readable_size(i['memory'])
    print 'processes:'
    print '\t', len(list(ps(sys.argv[1])))

if __name__ == '__main__': main()
