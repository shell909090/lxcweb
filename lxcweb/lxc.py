#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
@date: 2013-10-23
@author: shell.xu
'''
import re, os, sys, logging, cStringIO
import subprocess
from os import path

global_configfile = '/etc/lxc/lxc.conf'
default_lxcpath = '/var/lib/lxc'
sudoflag = os.getuid() != 0

def check_call(cmd):
    if sudoflag: cmd.insert(0, 'sudo')
    return subprocess.check_call(cmd)

def check_output(cmd):
    if sudoflag: cmd.insert(0, 'sudo')
    return subprocess.check_output(cmd)

def attach_check_call(name, cmd):
    cmd = ['lxc-attach', '-n', name, '--'] + cmd
    if sudoflag: cmd.insert(0, 'sudo')
    return subprocess.check_call(cmd)

def attach_check_output(name, cmd):
    cmd = ['lxc-attach', '-n', name, '--'] + cmd
    if sudoflag: cmd.insert(0, 'sudo')
    return subprocess.check_output(cmd)

# config methods

def read_config_stream(stream, spliter='='):
    cfg = {}
    for line in stream:
        if line.startswith('#'): continue
        line = line.strip()
        if not line: continue
        v = line.split(spliter, 1)
        k, v = str(v[0]).strip(), str(v[1]).strip()
        cfg.setdefault(k, []).append(v)
    return cfg

def read_config(filepath, spliter='='):
    with open(filepath, 'r') as fi:
        return read_config_stream(fi, spliter)

def sub_config(cfg, prefix):
    return dict((k[len(prefix):].lstrip('.'), v) for k, v in cfg.iteritems()
                if k.startswith(prefix))

def simple_config(cfg):
    return dict((k, v[-1]) for k, v in cfg.iteritems())

def global_config():
    try: return read_config(global_configfile)
    except IOError: return {'lxcpath': [default_lxcpath,]}

def container_path(name, fn=None):
    cfg = global_config()
    if not path.isdir(path.join(cfg['lxcpath'][-1], name)):
        raise Exception('invaild container %s' % name)
    if fn: return path.join(cfg['lxcpath'][-1], name, fn)
    return path.join(cfg['lxcpath'][-1], name)

def container_config(name):
    return read_config(container_path(name, 'config'))

def read_fstab(filepath):
    rslt = []
    with open(filepath, 'r') as fi:
        for line in fi:
            rslt.append(line.split()[:4])
    return rslt

def container_fstab(name):
    cfg, rslt = container_config(name), []
    rootfs = cfg['lxc.rootfs'][-1]
    for line in cfg.get('lxc.mount.entry', []):
        rslt.append(line.split()[:4])
    if 'lxc.mount' in cfg:
        for r in read_fstab(cfg['lxc.mount'][-1]):
            if not r: continue
            if r[1].startswith(rootfs):
                r[1] = r[1][len(rootfs):]
                rslt.append(r)
            else: logging.warning('container %s rule not in rootfs: %s' % (name, str(r)))
    return rslt

def read_comment(name):
    with open(container_path(name, 'comment'), 'r') as fi:
        return fi.read()

# TODO:
def set_comment(name):
    pass

# image methods

def clone(origin, name):
    return check_call(['lxc-clone', '-o', origin, '-n', name])

def create(template, name):
    return check_call(['lxc-create', '-t', template, '-n', name])

def destroy(name):
    return check_call(['lxc-destroy', '-n', name])

# info methods

def ls():
    output = check_output(['lxc-ls',])
    return (i for i in output.split() if i != '.')

def info(name):
    output = check_output(['lxc-info', '-n', name])
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
    output = check_output(['lxc-ps', '-n', name, 'auxf'])
    for line in output.splitlines():
        if line.startswith('CONTAINER'): continue
        i = line.strip().split(None, 10)
        i.extend(i.pop(10).split(' ', 1))
        yield i[1:12]

def df(name):
    cfg = container_config(name)
    p = cfg['lxc.rootfs'][-1]
    if isbtrfs(p): return btrfs_df(p) / 1024
    output = check_output(['du', '-sk', p])
    return int(output.split()[0].strip())

def isbtrfs(rootfs):
    try:
        check_output(['btrfs', 'sub', 'list', rootfs])
        return True
    except subprocess.CalledProcessError:
        return False

def btrfs_info(rootfs):
    buf = cStringIO.StringIO(check_output(['btrfs', 'sub', 'show', rootfs]))
    buf.readline()
    return read_config_stream(buf, spliter=':')

def btrfs_qgroup(rootfs):
    buf = cStringIO.StringIO(check_output(['btrfs', 'qgroup', 'show', rootfs]))
    for line in buf:
        line = line.strip()
        if not line: continue
        v = line.split()
        yield v[0].split('/', 1)[1], int(v[1]), int(v[2])

def btrfs_df(rootfs):
    id = btrfs_info(rootfs)['Object ID'][0]
    for k, v1, v2 in btrfs_qgroup(rootfs):
        if k == id: return v2
    raise Exception('object id not exists in qgroup output')

# container methods

def start(name, daemon=True):
    cmd = ['lxc-start', '-n', name]
    if daemon: cmd.append('-d')
    return check_call(cmd)

def stop(name):
    return check_call(['lxc-stop', '-n', name])

def shutdown(name, wait=True, reboot=False):
    cmd = ['lxc-shutdown', '-n', name]
    if wait: cmd.append('-w')
    if reboot: cmd.append('-r')
    return check_call(cmd)

# lxc-execute

def freeze(name):
    return check_call(['lxc-freeze', '-n', name])

def unfreeze(name):
    return check_call(['lxc-unfreeze', '-n', name])

re_inets = (
    re.compile('inet (\S*).*'),
    re.compile('inet6 (\S*).*'))
def ipaddr(name, dev=''):
    cmd = ['ip', 'addr', 'show']
    if dev: cmd.append(dev)
    for line in attach_check_output(name, cmd).splitlines():
        line = line.strip()
        for r in re_inets:
            m = r.match(line)
            if not m: continue
            i = m.group(1).split('/')
            if i[0] in ('127.0.0.1', '::1'): continue
            yield i[0], int(i[1])
