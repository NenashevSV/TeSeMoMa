# -*- coding: UTF-8 -*-
# coding: utf8

import requests
import json


def prepare(message):
	return message + '\n'

def infoWithCaption(message, caption, html=True):
	caption = '{}'.format(caption.encode('utf-8'))
	if html:
		message = '<i>{}</i>'.format(message.encode('utf-8'))
	else:
		message = '{}'.format(message.encode('utf-8'))
	mes = prepare(caption)+prepare(message)
	return mes


def info(message):
	return prepare('<i>' + message + '</i>')


def warning(message):
	return prepare('<u>' + message + '</u>')


def alarm(message):
	return prepare('<b>' + message + '</b>')


def mess(message, type=0, caption=''):
	mes = [info, warning, alarm]
	handler = mes[type]
	if caption:
		return handler(message)
	else:
		return handler(message)


def request_(base_url, request):
	result = {}
	url = base_url + request['url']
	try:
		resp = requests.get(url)
		if resp.status_code == 200:
			response = json.loads(resp.content)
			result = response
		else:
			message = 'Failed request with url "{}" with status code {}.'.format(url, resp.status_code)
			type = 2 # Alarm
			result = {'message': message, 'type': type}
	except Exception as e:
		message = 'Request error  to url "{}" with message ""'.format(url, e.message)
		type = 2  # Alarm
		result = {'message': message, 'type': type}
	return result

def htmlFromRequest(dict):
	result = True
	if 'html' in dict:
		result = dict['html']
	return result


def alarmHandler(base_url, request):
	alarm = request_(base_url, request)
	message = alarm['message']
	type = alarm['type']
	caption = request['caption']
	return mess(message, type, caption)


def alarmsHandler(base_url, request):
	result = ''
	alarms = request_(base_url, request)
	if isinstance(alarms, list):
		for alarm in alarms:
			message = alarm['message']
			type = alarm['type']
			caption = alarm
			result += mess(message, type, caption)
	else:
		result = alarmHandler(base_url, request)
	return result


def simpleHandler(base_url, request):
	message = ''
	answer = request_(base_url, request)
	html = htmlFromRequest(request)
	caption = unicode(request['caption'], "utf-8")
	if isinstance(answer, list):
		for item in answer:
			message += item['message']+'\n'
	else:
		message = answer['message']
	return infoWithCaption(message, caption, html)
