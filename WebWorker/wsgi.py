# -*- coding: UTF-8 -*-
# coding: utf8

import os, sys
import traceback

sys.path.append(r'C:\Users\Art\prj\Timosha\TiWorker3')
sys.path.insert(0, r'C:\Users\Art\prj\Timosha\TiWorker3\venv\Lib\site-packages')
import worker

def application(environ, start_response):

    status = '200 OK'
    try:
        output = worker.handler(environ)
    except Exception as e:
        output = 'Error:\n' + traceback.format_exc()
    output = output.decode('cp1251').encode('utf-8')
    response_headers = [('Content-type', 'text/plain'),
                        ('Content-Length', str(len(output)))]

    start_response(status, response_headers)

    return [str(output)]
