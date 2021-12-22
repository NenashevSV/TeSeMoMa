# -*- coding: UTF-8 -*-
# coding: utf8

import sys

sys.path.insert(0, r'\venv\Lib\site-packages')

import settings
import handlers
import platform
import subprocess
import time
import telebot
import json
import hashlib
from telebot import types
from threading import Thread


def getUserGroups(userId, group_users): # Получение групп в которые входит пользователь
    result = set()
    for groupName in group_users:
        if userId in group_users[groupName]:
            result.add(groupName)
    return result


def getUserMenuItems(message, settings, group_users): # Получение пунктов меню
    items = None
    userID = message.from_user.id
    userGroups = getUserGroups(userID, group_users)
    if len(userGroups) == 0:
        return items
    settingsKeys = settings.keys()
    settingsKeys.sort()
    for settingName in settingsKeys:
        if 'permissions' in settings[settingName]['permissions']:
            permissions = settings[settingName]['permissions']
        else:
            permissions = userGroups
        if len(userGroups & permissions) > 0:
            actions = settings[settingName]['actions']
            items = []
            actionsKeys = actions.keys()
            actionsKeys.sort()
            for actionName in actionsKeys:
                if 'permissions' in settings[settingName]['actions'][actionName]:
                    permissions = settings[settingName]['actions'][actionName]['permissions']
                else:
                    permissions = userGroups
                if len(userGroups & permissions) > 0:
                    item = actions[actionName]
                    item['name'] = actionName
                    item['caption'] = actions[actionName]['caption']
                    item['path'] = '/'.join([settingName, 'actions', actionName, 'requests'])
                    items.append(item)
    return items


def makeMenu(menuItems, user_id=None): # Создание разметки меню
    iButtons = []
    markup = types.InlineKeyboardMarkup()
    for menuItem in menuItems:
        iButton = types.InlineKeyboardButton(menuItem['caption'], callback_data=menuItem['path'])
        markup.add(iButton)
    return markup

class Watcher(object):

    def __init__(self, settings, token, period, group_users):
        # Период регистрации пользователя в системе после ввода пароля в секундах
        self.USER_REGISTRATION_PERIOD = 20 * 60

        self.__registered = {}
        self.repeatSendCountIfError = 5
        self.delayRepeatSendCountIfError = 300
        self.__settings = settings
        self.__group_users = group_users
        for settingName in self.__settings:
            conf = self.__settings[settingName]
            conf['lastPing'] = time.time()
            conf['state'] = 0
        self.prevDBAlarms = ''
        self.prevServiceAlarms = ''
        self.prevHardwareAlarms = ''
        self.prevPing = ''
        self.__bot = telebot.TeleBot(token, threaded=False)
        self.__period = period
        self.__cur_base_url = ''

        self.__all_groups = set()
        for GROUP_NAME in self.__group_users:
            self.__all_groups.add(GROUP_NAME)

        self.__all_users = set()  # all users list
        for GROUP_NAME in self.__all_groups:
            self.__all_users.update(set(self.__group_users[GROUP_NAME].keys()))


        @self.__bot.callback_query_handler(func=lambda call: True)
        def callback_inline(call): # Обработчик нажатия кнопок телеграм
            try:
                print (call.data)
                path = call.data
                caption = self.getMenuItemCaption(path)
                self.send_message(call.message.chat.id, "Выбран пункт '{}'.".format(caption))
                self.__bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id)
                if '/requests/' in path:
                    base_url = self.getBaseURLFromPath(path)
                    item = self.getPathValue(path)
                    userGroups = getUserGroups(call.from_user.id, self.__group_users)
                    execute = True
                    if 'permissions' in item and not len(userGroups & item['permissions']):
                        execute = False
                    if execute:
                        if 'needPassword' not in item:
                             item['needPassword'] = False
                        execute = True
                        if item['needPassword'] and not self.checkRegistration(call.from_user.id):
                             execute = False
                        if execute:
                            txt = item['handler'](base_url, item)
                            html = handlers.htmlFromRequest(item)
                            if html:
                                self.send_message(call.message.chat.id, txt, parse_mode='HTML')
                            else:
                                self.send_message(call.message.chat.id, txt)
                        else:
                            self.send_message(call.message.chat.id, 'Для выполнения команды необходимо зарегистрироваться.')
                            self.send_message(call.message.chat.id,
                                              '<b>Не регистрируйтесь в групповом чате!!!</b>', parse_mode='HTML')
                else:
                    menuItems = self.getPathItems(path, call.from_user.id)
                    if len(menuItems) > 0:
                        markup = makeMenu(menuItems, call.from_user.id)
                        self.send_message(call.message.chat.id, "Подменю:", reply_markup=markup)
                    else:
                        self.send_message(call.message.chat.id, "У вас нет доступных пунктов меню")
            except Exception as e:
                self.send_message(call.message.chat.id, "Произошла непредвиденная ошибка, сообщите программисту. Ошибка ->{}".format(e))


        @self.__bot.message_handler(content_types=['text'])
        def get_text_messages(message): # Обработчик сообщений телеграм
            try:
                print(message.text)
                menuItems = getUserMenuItems(message, self.__settings, self.__group_users)
                if message.text == '?':
                    if len(menuItems) == 0:
                        self.send_message(message.chat.id,
                            "Для вас нет доступных действий. Отправьте ответственному заявку. Ваш ID='{}'.".format(
                            message.from_user.id))
                    else:
                        if menuItems is None:
                            self.send_message(message.chat.id,
                                "У вас нет доступа к меню. Обратитесь к ответственному. Ваш ID='{}'.".format(
                                message.from_user.id))
                        else:
                            markup = makeMenu(menuItems)
                            self.send_message(message.chat.id, "Меню:", reply_markup=markup)
                elif message.text.startswith('pass '):
                    data = message.text.split(' ')
                    md5 = hashlib.md5(data[1]).hexdigest()
                    if md5 in self.getMD5ByUserID(message.from_user.id):
                        self.register(message.from_user.id)
                        self.send_message(message.from_user.id, "Вы зарегистрированны.")
                    else:
                        self.send_message(message.from_user.id, "Ошибка регистрации.")
                elif message.text == 'unlog':
                    self.unregister(message.from_user.id)
            except Exception as e:
                self.send_message(message.chat.id, "Произошла непредвиденная ошибка, сообщите программисту. Входящий текст '{}' Ошибка ->{}".format(message, e))

    def send_message(self, chatID, message, **params):
        result = False
        for i in range(self.repeatSendCountIfError):
            try:
                self.__bot.send_message(chatID, message, **params)
                result = True
                break
            except Exception as e:
                print('Send error' + str(e))
                time.sleep(self.delayRepeatSendCountIfError/1000*i)
        return result


    def checkRegistration(self, userID):
        result = True
        if userID in self.__registered:
            delta = time.time() - self.__registered[userID]
            if delta > self.USER_REGISTRATION_PERIOD:
                self.__registered.pop(userID)
                result = False
        else:
            result = False
        return result


    def unregister(self, userID):
        self.__registered.pop(userID)


    def register(self, userID):
        self.__registered[userID] = time.time()

    def getMD5ByUserID(self, userID):
        mds = []
        for groupName in self.__group_users:
            if userID in self.__group_users[groupName]:
                mds.append(self.__group_users[groupName][userID])
        return mds

    def getMenuItemCaption(self, path): # Получаем заголовок по пути
        caption = ''
        sections = path.split('/')
        data = self.__settings
        for section in sections:
            data = data[section]
            if 'caption' in data:
                caption = data['caption']
        return caption

    def getBaseURLFromPath(self, path): # Получаем базовый URL по пути
        sections = path.split('/')
        data = self.__settings
        section = sections[0]
        baseUrl = data[section]['config']['base_url']
        return baseUrl

    def getPathValue(self, path):  # Получаем значение по пути
        sections = path.split('/')
        data = self.__settings
        for section in sections:
            data = data[section]
        return data

    def getPathItems(self, path, userID):  # Получаем пункты меню по пути
        data = self.getPathValue(path)
        userGroups = getUserGroups(userID, self.__group_users)
        result = []
        keys = data.keys()
        keys.sort()
        for itemName in keys:
            item = data[itemName]
            enable = True
            if 'permissions' in item:
                if len(userGroups & item['permissions']) == 0:
                    enable = False
            if enable:
                res = {}
                res['name'] = itemName
                res['caption'] = item['caption']
                res['path'] = '/'.join([path, itemName])
                if 'permissions' in item:
                    res['permissions'] = item['permissions']
                result.append(res)
        return result


    def sendToSubscribers(self, message, permissions=None):  # Рассылка
        usersID = set()
        if permissions is None:
            permissions = self.__all_groups  # Рассылка всем группам
        for groupName in permissions:
            usersID.update(set(self.__group_users[groupName].keys()))  # Собираем пользователей из разрешенных групп
        for userID in usersID:  # рассылка пользователям
            self.send_message(userID, message, parse_mode='HTML')


    @staticmethod
    def ping(host):
        """
        Returns True if host (str) responds to a ping request.
        Remember that a host may not respond to a ping (ICMP) request even if the host name is valid.
        """

        # Option for the number of packets as a function of
        param = '-n' if platform.system().lower() == 'windows' else '-c'

        # Building the command. Ex: "ping -c 1 google.com"
        command = ['ping', param, '1', host]

        return subprocess.call(command) == 0


    def sendNewLines(self, txt, oldLines, permissions=None):  # Рассылка новых данных мониторинга
        message = ''
        lines = txt.split('\n')
        for line in lines:
            if not line in oldLines:
                message += line + '\n'
        if message:
            self.sendToSubscribers(message, permissions)
        oldLines = lines
        return oldLines

    def Ping(self, setting):    # Обработчик пинга
        result = True
        if setting['ping']:
            now = time.time()
            if not self.ping(setting['host']):
                diff = now - setting['lastPing']
                txt = ''
                if diff >= setting['timeOutError'] and setting['state'] != 1:
                    result = False
                    setting['state'] = 2
                    txt = handlers.alarm('Товарищи админы беда!!! Сервер не пингуется уже {} минут(ы).'.format(diff/60))
                elif diff >= setting['timeOutWarning'] and setting['state'] != 2:
                    result = False
                    setting['state'] = 1
                    txt = handlers.warning('Товарищи админы... Сервер не пингуется уже {} минут(ы).'.format(diff/60))
                self.prevPing = self.sendNewLines(txt, self.prevPing)
        return result


    def delay(self, period):    # Здесь можно добавить какие либо действия во время ожидания
        timeout = 0
        while timeout < period:
            minPeriod = 0.5
            time.sleep(minPeriod)
            timeout += minPeriod


    def pooling(self):  # Прослушка telegram
        self.__bot.polling(none_stop=True, interval=0)

    def getDBAlarms(self, base_url, settingsItem):  # Получение предупреждений из БД
        txt = ''
        requests = settingsItem['actions']['dbAlarms']['requests']
        keys = requests.keys()
        keys.sort()
        for requestName in keys:
            request = requests[requestName]
            txt += request['handler'](base_url, request)
        self.prevDBAlarms = self.sendNewLines(txt, self.prevDBAlarms)


    def getServiceAlarms(self,base_url, settingsItem):
        txt = ''
        requests = settingsItem['actions']['serviceAlarms']['requests']
        keys = requests.keys()
        keys.sort()
        for requestName in keys:

            request = requests[requestName]
            txt += request['handler'](base_url, request)
        self.prevServiceAlarms = self.sendNewLines(txt, self.prevServiceAlarms)


    def getHardwareAlarms(self,base_url, settingsItem):
        txt = ''
        requests = settingsItem['actions']['hardwareAlarms']['requests']
        keys = requests.keys()
        keys.sort()
        for requestName in keys:
            request = requests[requestName]
            txt += request['handler'](base_url, request)
        self.prevHardwareAlarms = self.sendNewLines(txt, self.prevHardwareAlarms)


    def start(self):
        pretime = 0
        th = Thread(target=self.pooling)  # Поток для прослушки сообщений из telegram
        th.start()
        self.sendToSubscribers('Запуск мониторинга')
        while True:
            delta = time.time() - pretime
            if delta > self.__period:
                pretime = time.time()
                for name in self.__settings:
                    settingsItem = self.__settings[name]
                    if self.Ping(settingsItem['config']): # Пингуем
                        # Если сервер пингуется идем дальше
                        base_url = settingsItem['config']['base_url']
                        self.getDBAlarms(base_url, settingsItem)
                        self.getServiceAlarms(base_url, settingsItem)
                        self.getHardwareAlarms(base_url, settingsItem)
            time.sleep(0.5)


if __name__ == '__main__':
    watcher = Watcher(settings.settings, settings.TOKEN, settings.REQUEST_PERIOD, settings.GROUP_USERS)
    watcher.start()