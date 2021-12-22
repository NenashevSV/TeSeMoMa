import time
import logging

log = logging.getLogger('appl')
FORMAT = '%(asctime)s %(clientip)-15s %(user)-8s %(message)s'


def sleepByNone(iter_timeout, max_iter_count=3):
	def fdecorator(function):
		def wrapper(*args, **kwargs):
			iter_count = 0
			while max_iter_count > iter_count:
				value = function(*args, **kwargs)
				if value is None:
					print('{} - Dream'.format(iter_count))
					time.sleep(iter_timeout)
					iter_count += 1
				else:
					break
		return wrapper
	return fdecorator