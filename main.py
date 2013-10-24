#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
@date: 2011-05-05
@author: shell.xu
'''
import os, sys, web, logging
from os import path
# from web.contrib.template import render_mako

def initlog(lv, logfile=None):
    rootlog = logging.getLogger()
    if logfile: handler = logging.FileHandler(logfile)
    else: handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter(
            '%(asctime)s,%(msecs)03d %(name)s[%(levelname)s]: %(message)s',
            '%H:%M:%S'))
    rootlog.addHandler(handler)
    rootlog.setLevel(lv)

logger = logging.getLogger('main')
DEBUG = not path.isfile('RELEASE')
web.config.debug = DEBUG
web.config.rootdir = path.dirname(__file__)
# web.config.db = web.database(dbn='postgres', db='hosts')
# web.config.render = render_mako(
#     directories = ['templates'],  imports = ['import web'],
#     default_filters = ['decode.utf8'], filesystem_checks = DEBUG,
#     module_directory = None if DEBUG else '/tmp/mako_modules',
#     input_encoding = 'utf-8', output_encoding = 'utf-8')

# urls = (
#     '/openid/', 'actions.webgid.host',
#     '/ticket/', 'actions.ticket.ticket',
#     '/timezone/', 'actions.timezone.timezone',
#     '/segment/', 'actions.segtxt.segtxt',
#     '/txtimg', txtimg.app,
#     '/pycode', pycode.app,
# )
import lxcweb
app = web.application(lxcweb.urls)

# if web.config.get('sesssion') is None:
#     web.config.session = web.session.Session(
#         app, web.session.DBStore(web.config.db, 'sessions'))

if __name__ == '__main__':
    if len(sys.argv) > 1:
        cmd = sys.argv.pop(1)
        if cmd == 'profile':
            app.run(web.profiler)
        elif cmd == 'test':
            from test import tester
            tester.testall(app)
    else: app.run()
else: application = app.wsgifunc()
