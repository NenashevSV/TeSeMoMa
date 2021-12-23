# -*- coding: UTF-8 -*-
# coding: utf8

import handlers

# Message type
NORMAL = 0
WARNING = 1
ALARM = 2

START_SERVICE = 'start'
STOP_SERVICE = 'stop'
PAUSE_SERVICE = 'pause'
RESUME_SERVICE = 'continue'
REQUEST_PERIOD = 30  # second
TOKEN = '5067445228:AAFtOZay60GVQIfa6-u3GCMtcX7iPyAtNgI' # TeSeMoMa здесь заполнить откен вашего бота

# GROUPS
USERS = 'USERS'
ENGINEER = 'ENGINEER'
SERVER_ADMINS = 'SERVER_ADMINS'
FULL_ADMINS = 'FULL_ADMINS'

GROUP_USERS = {
    USERS: { # Формат ключ ID пользователя, значение MD5 хеш пароля или ""
        -726899003: '',  # id группы наблюдателей (бота нужно сделать админов группы чтобы он мог читать сообщения)
    },
    ENGINEER: {

    },
    SERVER_ADMINS: {

    },
    FULL_ADMINS: {
        0000000:  '098f6bcd4621d373cade4e832627b4f6',  # ID Админа
    },
}

settings = {
    'obj':  # Наименование раздела настроек ( в данном случае используется одна группа )
    {
        'permissions': {USERS, ENGINEER, SERVER_ADMINS, FULL_ADMINS},  # Доступ групп пользователей к разделу настроек
        'config': {
            'host': '127.0.0.1',  # Адрес для проверки пинга
            #'base_url': 'http://127.0.0.1:8000/',  # Базовый HTTP путь до  например (http://domain.ru/{folder/subfoder/})
            'base_url': 'http://localhost/Timosha/TiWorker3/',  # Базовый HTTP путь до  например (http://domain.ru/{folder/subfoder/})
            'ping': True,  # Проверять соединение пингом
            'timeOutWarning': 10,  # Ждать восстановления связи в секундах до отправки предупреждения
            'timeOutError': 60 * 5,  # Ждать  восстановления связи в секундах до отправки ошибки
        },
        'actions': {  # Описание возможных действий
            'dbAlarms': {  # Обязательный пункт, жестко вызывается при мониторинге (внутри можно чистить)
                'permissions': set(),  # Никто не увидит (кроме системы мониторинга)
                'caption': 'Предупреждения от БД',  # Заголовок пункта меню
                'requests': {  # Описание пользовательских запросов
                    'timeout': {  # Имя запроса
                        'permissions': set(),  # Никто не увидит и не выполнит(кроме системы мониторинга)
                        'url': 'obj/dbData/timeOutAlarm',  # Путь после базового пути
                        'caption': 'Tаймаут',  # Заголовок запроса (подпункт меню)
                        'handler': handlers.alarmHandler,  # Обработчик выполнения запроса
                    },
                },
            },
            'serviceAlarms': {  # Обязательный пункт, жестко вызывается при мониторинге (внутри можно чистить)
                'permissions': set(),  # Никто не увидит (кроме системы мониторинга)
                'caption': 'Предупреждения о работе служб', # Заголовок пункта меню
                'requests': {   # Описание пользовательских запросов
                    'infoRabbitMQ': {
                        'permissions': set(),  # Никто не увидит и не выполнит(кроме системы мониторинга)
                        'url': 'obj/serviceManager/services/info',
                        'caption': 'Предупреждения о службах',
                        'handler': handlers.alarmsHandler,
                    },
                },
            },
            'hardwareAlarms': {  # Обязательный пункт, жестко вызывается при мониторинге  (внутри можно чистить)
                'permissions': set(),  # Никто не увидит (кроме системы мониторинга)
                'caption': 'Предупреждения о свободных ресурсах',  # Заголовок пункта меню
                'requests': {  # Описание пользовательских запросов
                    'cpu': {
                        'permissions': set(),  # Никто не увидит и не выполнит(кроме системы мониторинга)
                        'url': 'obj/hardware/cpuAlarm',
                        'caption': 'Загрузка процессора',
                        'handler': handlers.alarmsHandler,
                    },
                    'memory': {
                        'permissions': set(),  # Никто не увидит и не выполнит(кроме системы мониторинга)
                        'url': 'obj/hardware/memAlarm',
                        'caption': 'Свободное ОЗУ',
                        'handler': handlers.alarmsHandler,
                    },
                    'diskC': {
                        'permissions': set(),  # Никто не увидит и не выполнит(кроме системы мониторинга)
                        'url': 'obj/hardware/diskC',
                        'caption': 'Свободное месте на диске С',
                        'handler': handlers.alarmsHandler,
                    },
                    'diskF': {
                        'permissions': set(),  # Никто не увидит и не выполнит(кроме системы мониторинга)
                        'url': 'obj/hardware/diskF',
                        'caption': 'Свободное месте на диске F',
                        'handler': handlers.alarmsHandler,
                    },
                },
            },
            'dbInfo': { # Пользовательский пункт
                'caption': 'БД инфо',  # Заголовок пункта меню
                'permissions': {USERS, ENGINEER, SERVER_ADMINS, FULL_ADMINS},  # Группы которым будет виден данный пункт
                'requests': {  # Описание пользователских запросов
                    'OBJ_TimeOut': {
                        'url': 'obj/dbData/timeOutInfo',
                        'caption': 'Последний таймаут',
                        'handler': handlers.simpleHandler,
                    },
                    'OBJ_online': {
                        'url': 'obj/dbData/online',
                        'caption': 'Кол-во по состоянию сети',
                        'handler': handlers.simpleHandler,
                    },
                    'OBJ_status': {
                        'url': 'obj/dbData/status',
                        'caption': 'Кол-во по статусу',
                        'handler': handlers.simpleHandler,
                    },

                },
            },
            'serviceManager': { # Пользовательский пункт
                'caption': 'Управление службами',
                'permissions': {USERS, ENGINEER, SERVER_ADMINS, FULL_ADMINS},
                'requests': {
                    'infoRabbitMQ': {
                        'url': 'obj/serviceManager/rabbitMQ/info',
                        'caption': 'Инфо RabbitMQ',
                        'handler': handlers.simpleHandler,
                        'permissions': {USERS, ENGINEER, SERVER_ADMINS, FULL_ADMINS}
                    },
                    'startRabbitMQ': {
                        'url': 'obj/serviceManager/rabbitMQ/start',
                        'caption': 'Старт RabbitMQ',
                        'handler': handlers.simpleHandler,
                        'checkAccess': 'True',
                        'permissions': {SERVER_ADMINS, FULL_ADMINS}
                    },
                    'stopRabbitMQ': {
                        'url': 'obj/serviceManager/rabbitMQ/stop',
                        'caption': 'Стоп RabbitMQ',
                        'handler': handlers.simpleHandler,
                        'checkAccess': 'True',
                        'permissions': {SERVER_ADMINS, FULL_ADMINS},
                        'needPassword': True,
                    },
                },
            },
            'exec': { # Пользовательский пункт
                'caption': 'Запуск приложений',
                'permissions': {SERVER_ADMINS, FULL_ADMINS},
                'requests': {
                    'notepad': {
                        'url': 'obj/exec/notepad',
                        'caption': 'Hello World!',
                        'handler': handlers.simpleHandler,
                        'html': False,
                        'permissions': {SERVER_ADMINS, FULL_ADMINS}
                    },
                },
            },
            'hardware': {  # Пользовательский пункт
                'caption': 'Информация о загрузке железа',
                'permissions': {SERVER_ADMINS, FULL_ADMINS},
                'requests': {
                    'CPU': {
                        'url': 'obj/hardware/cpu',
                        'caption': 'Загрузка процессора',
                        'handler': handlers.simpleHandler,
                        'html': False,
                        'permissions': {SERVER_ADMINS, FULL_ADMINS}
                    },
                    'memory': {
                        'url': 'obj/hardware/mem',
                        'caption': 'Свободное ОЗУ',
                        'handler': handlers.simpleHandler,
                        'html': False,
                        'permissions': {SERVER_ADMINS, FULL_ADMINS}
                    },
                    'diskC': {
                        'url': 'obj/hardware/diskC',
                        'caption': 'Свободное место на C',
                        'handler': handlers.simpleHandler,
                        'html': False,
                        'permissions': {SERVER_ADMINS, FULL_ADMINS}
                    },
                    'diskF': {
                        'url': 'obj/hardware/diskF',
                        'caption': 'Свободное место на F',
                        'handler': handlers.simpleHandler,
                        'html': False,
                        'permissions': {SERVER_ADMINS, FULL_ADMINS}
                    },
                },
            },
            # Здесь еще могут быть добавлены пользователские пункты
        },
    },  # End obj config
    # Здесь еще могут быть добавлены разделы настроек
}   # CONFIGS END
