# -*- coding: UTF-8 -*-
# coding: utf8

import os, sys
import traceback

sys.path.append((os.path.dirname(os.path.realpath(__file__))))
sys.path.insert(0, (os.path.dirname(os.path.realpath(__file__)))+r'\env\Lib\site-packages')

import worker

def application(environ, start_response):

    status = '200 OK'
    try:
         output = worker.handler(environ)
    except Exception as e:
         output = 'Error:\n' + traceback.format_exc()
    output = output.decode('cp1251').encode('utf-8')
    # output = (os.path.dirname(os.path.realpath(__file__)))
    response_headers = [('Content-type', 'text/plain'),
                        ('Content-Length', str(len(output)))]

    start_response(status, response_headers)

    return [str(output)]
