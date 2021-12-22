# -*- coding: UTF-8 -*-
# coding: utf8


import json
import psutil
import subprocess
import re
from time import sleep, time
import logging as log


NORMAL = 0
WARNING = 1
ALARM = 2

APP_TIME_OUT = 15

def toLog(dict):
	result = '\n'
	for key in dict:
		result += '"{}":"{}" \n'.format(key, dict[key])
	return result

class timesUpError(RuntimeError):
	pass

def timeoutHandler(signum, frame):
	raise timesUpError

def getServiceStatus(service):
	status_type = {
		'running': 0,
		'paused': 2,
		'start_pending': 1,
		'pause_pending': 2,
		'continue_pending': 1,
		'stop_pending': 2,
		'stopped': 2,
	}
	status = psutil.win_service_get(service).status()
	result = {}
	result['message'] = 'Service "{}" {}'.format(service, status)
	result['type'] = status_type[status]
	log.debug('service status result ->' + toLog(result))
	return json.dumps(result)

def getServicesStatus(data):
	result = []
	if isinstance(data, dict):
		services = data['parameters']
	else:
		services = data
	for service in services:
		res = json.loads(getServiceStatus(service))
		result.append(res)
		#log.debug('services status results ->' + toLog(res))
	return json.dumps(result)

def serviceManager(data):
	try:
		parameters = data['parameters']
		log.debug('Start serviceManager with parameters {}'.format(parameters))
		result = {}
		res = {}
		val = 0
		for parameter in parameters:
			serviceName = parameter[0]
			handler = parameter[1]
			res['state'] = 'Not execute error'
			res['errorCode'] = 1
			data = serviceName
			message = getServiceStatus(data)
			status = json.loads(message)
			log.debug('Before {handler} "{serviceName}" service has status "{status}"'
			             .format(handler=handler, serviceName=serviceName, status=status))
			if re.match(r'pending', status['message']):
				res['state'] = 'Error "{}" service "{}" (service in )'.format(handler, serviceName)
				res['errorCode'] = 3
			else:
				try:
					val = subprocess.call(['sc', handler, serviceName])
					res['state'] = 'For service "{}" execute "{}" with code "{}"'.format(serviceName, handler, val)
					res['errorCode'] = 0
					status = json.loads(getServiceStatus(data))
					res['state'] +='\n'+status['message']
				except:
					res['state'] = 'Exception for "{}" service "{}"'.format(handler, serviceName)
					res['errorCode'] = 2
			sleep(0.2)
			status = json.loads(getServicesStatus([serviceName]))[serviceName]
			log.debug('After {handler} "{serviceName}" service has status "{status}"'
			             .format(handler=handler, serviceName=serviceName, status=status))
			# result[serviceName] = res
			# if res['errorCode']:
			# 	if res['errorCode'] == 2:
			# 		log.error(''.format(res))
			# 	else:
			# 		log.warning(''.format(res))
			# else:
			# 	log.debug(''.format(res))
	except Exception as e:
		print(str(e))
	finally:
		result['message'] = res['state']
		result['type'] = res['errorCode']
		log.debug('service manager result ->' + toLog(result))
	return json.dumps(result)


def execApplication(data):
	result = {}
	result['message'] = ''
	try:
		parameters = data['parameters']
		log.debug('execApplication with parameters {}'.format(parameters))
		for parameter in parameters:
			code = -1   # Not start
			out = 'Error in function, application not executed'
			try:
				name = parameter[0]
				path = parameter[1]
				param = parameter[2]
				wait = parameter[3]
				log.debug('Exec appl "{}" "{}" wait={}'.format(path, param, wait))
				appl = subprocess.Popen([path, param], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
				if isinstance(wait, bool):
					if wait:
						wait = APP_TIME_OUT
					else:
						wait = 0
				startTime = time()
				print(startTime)
				poll = appl.poll()
				while poll is None and time() - startTime < wait:
					poll = appl.poll()
					sleep(0.1)
				if poll is None:
					if wait == 0:
						code = 0
						out = 'Application started'
					else:
						code = -2
						out = 'TimeOut for wait end of Application'
				else:
					code = appl.wait()
					out, err = appl.communicate()
					out = out + ' ' + err
					out = out.decode('cp866')
					out = out.encode('utf-8')
			except Exception as e:
				code = -3  # undefined Exception
				out = 'Undefined Exception with message "{}"'.format(e.message)
			if code == 0:
				pass
				log.debug('     return code={}'.format(code))
				log.debug('     return out="{}"'.format(out))
			elif code > 0 or code == -2 or code == -4:
				log.warning('     return code={}'.format(code))
				log.warning('     return out="{}"'.format(out))
			elif code == -1 or code == -3:
				log.error('     return code={}'.format(code))
				log.error('     return out="{}"'.format(out))
			print(out)
			result['message'] += "Application '{}' {} with code '{}' \n".format(name, out, code)
			log.debug('execApllication return -> {}'.format(result))
	except Exception as e:
		if name:
			result['message'] += 'Error exec application "{}" with error {}'.format(name, e)
		else:
			result['message'] += 'Error exec application with error'.format(e)
	log.debug('application result ->' + toLog(result))
	return json.dumps(result)


def execQuery(params):
	connection = params['connection']
	query = params['query']
	with connection.cursor() as cursor:
		cursor.execute(query)
		data = cursor.fetchall()
	return data

def alarms(params):
	data = execQuery(params)
	type = data[0][0]
	message = data[0][1]
	result = {'message': message, 'type': type}
	log.debug('alarms result ->' + toLog(result))
	return json.dumps(result)

def getOneFieldInfo(params):
	data = execQuery(params)
	message = data[0][0]
	result = {'message': message}
	log.debug('getOneFieldInfo result ->' + toLog(result))
	return json.dumps(result)

def getMultiRowOneFieldInfo(params):
	data = execQuery(params)
	message = ''
	for item in data:
		message += item[0]+'\n'
	result = {'message': message}
	log.debug('getMultiRowOneFieldInfo result ->' + toLog(result))
	return json.dumps(result)

def cpuPercent():
	return psutil.cpu_percent()

def getCPUPercent(data):
	result = {'message': str(cpuPercent())+'%'}
	log.debug('getCPUPercent result ->' + toLog(result))
	return json.dumps(result)

def cpuAlarm(data):
	result = {}
	percents = int(cpuPercent())
	parameters = data['parameters']
	min = parameters['min']
	max = parameters['max']
	if percents not in range(min, max):
		result['message'] = 'Внимание!!! Высокая загрузка процессора ({}%)'.format(percents)
		result['type'] = 2
	else:
		result['message'] = 'Загрузка процессора в норме (от {} до {} %)'.format(min, max)
		result['type'] = 0
	return json.dumps(result)

def memUsage():
	info = psutil.virtual_memory()
	return info[2]

def getMemUsage(data):
	result = {'message': str(memUsage())+'%'}
	log.debug('getMemUsage result ->' + toLog(result))
	return json.dumps(result)


def memAlarm(data):
	result = {}
	percents = int(memUsage())
	parameters = data['parameters']
	min = parameters['min']
	max = parameters['max']
	if percents not in range(min, max):
		result['message'] = 'Внимание!!! Мало свободной памяти (занято {}% памяти)'.format(percents)
		result['type'] = 2
	else:
		result['message'] = 'Свободная память в норме (занято от {} до  {} % памяти)'.format(min, max)
		result['type'] = 0
	return json.dumps(result)


def freeDiskSpaceAlarm(data):
	result = {}
	parameters = data['parameters']
	disk = parameters['disk']
	min = parameters['min']
	size = psutil.disk_usage(disk).free/(1024*1024*1024)
	if size < min:
		result['message'] = 'Внимание!!! Мало свободного места на диске "{}" (свободно {} Gb)'.format(disk, size)
		result['type'] = 2
	else:
		result['message'] = 'Свободное место на диске "{}" в норме (свободно {} Gb)'.format(disk, size)
		result['type'] = 0
	return json.dumps(result)