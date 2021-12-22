# -*- coding: UTF-8 -*-
# coding: utf8

import traceback
import settings
import logging as log

log.basicConfig(filename="wsgi.log", level=log.DEBUG)

def parseUrl(urlStr):
	url = urlStr.split('?')
	pathParts = url[0].split('/')
	pathParts.pop(0)
	log.debug('pathParts='+str(pathParts))
	return pathParts


def handler(environ):
	try:
		result = 'The request could not be processed'
		pathParts = parseUrl(environ['PATH_INFO'])
		subTree = settings.config
		for part in pathParts:
			if part in subTree.keys():
				if isinstance(subTree[part], dict):
					subTree = subTree[part]
				else:
					result = 'No dict for URL'
		if part:
			if 'handler' in subTree.keys():
				handler = subTree['handler']
				parameters = subTree
				result = handler(parameters)
			else:
				result = "Can't find key 'handler' for subpath '{}'".format(part)
	except Exception as e:
		result = 'Error:\n'+ traceback.format_exc()
	log.debug(str(result))
	return result