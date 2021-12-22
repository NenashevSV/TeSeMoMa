# -*- coding: UTF-8 -*-

import handlers
import pymysql

DATABASES = { # Настройки баз данных
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'obj',
        'USER': 'root',
        'PASSWORD': '123456',
        'HOST': '127.0.0.1',
        'PORT': 3306,
    },
	'obj': {  # Алиас БД
		'ENGINE': 'django.db.backends.mysql',
		'NAME': 'obj',
		'USER': 'root',
		'PASSWORD': '123456',
		'HOST': '127.0.0.1',
		'PORT': 3306,
	},
}

# Начало создание подключений к БД (не трогать)
connections = {}
for alias in DATABASES:
	dataBaseSettings = DATABASES[alias]
	user = dataBaseSettings['USER']
	password = dataBaseSettings['PASSWORD']
	host = dataBaseSettings['HOST']
	port = dataBaseSettings['PORT']
	database = dataBaseSettings['NAME']
	connections[alias] = pymysql.connect(user=user, password=password, host=host, db=database, port=port)
# Конец() создание подключений к БД (не трогать)


START_SERVICE = 'start'
STOP_SERVICE = 'stop'
PAUSE_SERVICE = 'pause'
RESUME_SERVICE = 'continue'

SERVICE_ACTIONS = (START_SERVICE, STOP_SERVICE, PAUSE_SERVICE,)

SERVICE_RUNNING = 'running'
SERVICE_PAUSED = 'paused'
SERVICE_START_PENDING = 'start_pending'
SERVICE_PAUSE_PENDING = 'pause_pending'
SERVICE_CONTINUE_PENDING = 'continue_pending'
SERVICE_STOP_PENDING = 'stop_pending'
SERVICE_STOPPED = 'stopped'

SERVICE_STATUS = (
	SERVICE_RUNNING, SERVICE_PAUSED,  SERVICE_START_PENDING, SERVICE_PAUSE_PENDING, SERVICE_CONTINUE_PENDING,
	SERVICE_STOP_PENDING, SERVICE_STOPPED,
)

config = {  # Настройки менеджера
	'obj': {  # Имя настройки
		'dbData': {  # Имя пункта получения информации из БД
			'timeOutInfo': {  # Имя действия
				'query':  # SQL запрос
					"""SELECT concat(min(time_to_sec(timeDIFF(NOW(),o.last_online))), ' секунд прошло с последнего сеанса связи')   
						as 'Кол-во секунд от последней передачи данных' FROM objects o""",
				'connection': connections['obj'],  # Подключение к БД
				'handler': handlers.getOneFieldInfo  # Обработчик запроса
			},
			'timeOutAlarm': {  # Имя действия
				'query':  # SQL запрос
					"""SELECT 
						CASE 
							WHEN minTimeOut<10 then 0 # NORMAL
							WHEN minTimeOut>60 then 2 # ALARM
							ELSE 1 # WARNING
						END AS type,
						CASE 
							WHEN minTimeOut<10 then "Данные от контроллеров приходят стабильно." # NORMAL
							WHEN minTimeOut>60 then "ВНИМАНИЕ!!! Данные от контроллеров не приходят (прошло больше 60 секунд с момента последнего получения данных)." # ALARM 
							ELSE "Задержка получения данных от контроллеров (прошло больше 10 секунд с момента последнего получения данных)." # WARNING
						END AS message
						FROM (SELECT min(time_to_sec(timeDIFF(NOW(),o.last_online))) AS minTimeOut FROM objects o) 
						AS c"""
				,
				'connection': connections['obj'],  # Подключение к БД
				'handler': handlers.alarms,  # Обработчик запроса
			},
			'online': {  # Имя действия
				'query':
					"""
						select 
							case
								when online=0 then concat('Не в сети - ',count(*),' объектов')
								when online=1 then concat('В сети - ', count(*),' объектов')
							end
						from objects
						group by online
					""",
				'connection': connections['obj'],  # Подключение к БД
				'handler': handlers.getMultiRowOneFieldInfo,  # Обработчик запроса
			},
			'status': {  # Имя действия
				'query':
					"""
						select 
						case
							when state=0 then concat('Нормальные показания - ',count(*),' объектов')
							when state=1 then concat('Аварийные показания - ', count(*),' объектов')
							when state=2 then concat('В ремонте - ', count(*),' объектов')
						end
						from objects
						group by state					""",
				'connection': connections['obj'],  # Подключение к БД
				'handler': handlers.getMultiRowOneFieldInfo,  # Обработчик запроса
			},
		},
		'serviceManager': {  # Имя пункта менеджера служб
			'rabbitMQ': {  # Имя подпункта
				'start': {  # Имя действия
					'handler':  handlers.serviceManager,  # Обработчик
					'parameters': [ # В параметрах реальное имя службы и действие
						['RabbitMQ', START_SERVICE],  # Для запуска/остановки служб приложение или web сервер должны обладать соответствующими правами
					],
				},
				'stop': {  # Имя действия
					'handler': handlers.serviceManager,  # Обработчик
					'parameters': [ # В параметрах реальное имя службы и действие
						['RabbitMQ', STOP_SERVICE], # Для запуска/остановки служб приложение или web сервер должны обладать соответствующими правами
					],
				},
				'info': {  # Имя действия
					'handler': handlers.getServicesStatus,  # Обработчик
					'parameters': ['RabbitMQ'], # реальное имя службы
				},
			},
		'services': {  # Имя подпункта
			'info': {  # имя действия
				'handler': handlers.getServicesStatus,  # Обработчик
				'parameters': ['RabbitMQ', 'Apache2.4'],  # реальные имена служб
			}
		}
		},
		'exec': {  # Имя пункта выполнения приложений
			'helloWord': {  # имя действия
				'handler': handlers.execApplication,
				'parameters': [
					# Name                  Path with exec file             parameters      wait result code
					# Человекоудобное       Путь до запускаемого файла      параметры       True - ждать окончания выполенения
					# имя приолжения                                                        False - не ждать окончания выполнения
					#                                                                       число - сколько секунд ждать окончания выполнения
					['ждать окончание 5 секунд', 'c:\\1\\HelloWorld.bat', '',   5],
					# ['ждать окончание выполнения до победного',     'notepad.exe', 'C:\\obj.txt',  True],
					# ['не ждать окончания выполнения (просто запустить)',              'notepad.exe', 'C:\\test1.txt', False],
				]
			},
		},
		'hardware': {  # Имя пункта Информация о "железных ресурсов"
			'cpu': {  # имя действия (процент загрузки ЦП)
				'handler': handlers.getCPUPercent,
			},
			'mem': {  # имя действия (процент свободной памяти)
				'handler': handlers.getMemUsage,
			},
			'cpuAlarm': {  # имя действия (предупреждение о загрузке ЦП)
				'handler': handlers.cpuAlarm,
				'parameters': {
					'min': 0,
					'max': 85,
				},
			},
			'memAlarm': {  # имя действия (предупреждение он загрузке ОЗУ)
				'handler': handlers.memAlarm,
				'parameters': {
					'min': 0,
					'max': 85,
				},
			},
			'diskC': {  # имя действия (свободное место на диске)
				'handler': handlers.freeDiskSpaceAlarm,
				'parameters': {
					'min': 1,
					'disk': 'C:',
				},
			},
			'diskF': {  # имя действия (свободное место на диске)
				'handler': handlers.freeDiskSpaceAlarm,
				'parameters': {
					'min': 1,
					'disk': 'F:',
				},
			},
		},
	},
# ------------------------------------
# Здесь может быть следующая настройка
}
