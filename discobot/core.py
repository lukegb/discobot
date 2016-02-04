import asyncio
import logging

l = logging.getLogger("discobot")

import discord

from . import plugins


class DiscobotClient(discord.Client):
    _dc_registrable_events = [
        'ready',
        'message',
        #'error',
        'socket_opened',
        'socket_closed',
        'socket_update',
        'socket_response',
        'socket_raw_receive',
        'socket_raw_send',
        'message_delete',
        'message_edit',
        'channel_delete',
        'channel_create',
        'channel_update',
        'member_join',
        'member_remove',
        'member_update',
        'server_join',
        'server_remove',
        'server_update',
        'server_role_create',
        'server_role_delete',
        'server_role_update',
        'server_available',
        'server_unavailable',
        'voice_state_update',
        'member_ban',
        'member_unban',
        'typing',
    ]

    def __new__(cls):
        o = super().__new__(cls)
        o._dc_event_registrations = dict()
        for event in cls._dc_registrable_events:
            setattr(o, 'on_' + event, o._dc_create_handler(event))
            o._dc_event_registrations[event] = {}
        o._dc_log = logging.getLogger('discobot.DiscobotClient')
        return o

    def _dc_create_handler(self, event_name):
        async def handler(*args, **kwargs):
            log = self._dc_log
            log.debug('Got event {} with args {} and kwargs {}'.format(event_name, args, kwargs))
            event_registrations = self._dc_event_registrations[event_name]
            priorities = sorted(event_registrations.keys())
            for priority in priorities:
                log.debug('Executing handlers for {} at priority {}'.format(event_name, priority))
                await asyncio.wait([self.loop.create_task(f(*args, **kwargs)) for f in event_registrations[priority]])
        return handler

    def _dc_register(self, event, func, priority=100):
        if not event in self._dc_registrable_events:
            raise KeyError("No such event: {}".format(event))
        priority = int(priority)  # no floats or strings, please

        self._dc_log.info('Registering {} with priority {} for event {}'.format(func, priority, event))

        if priority not in self._dc_event_registrations[event]:
            self._dc_event_registrations[event][priority] = []
        self._dc_event_registrations[event][priority].append(func)

    def _dc_unregister_all(self):
        for k in self._dc_event_registrations.keys():
            self._dc_event_registrations[k] = {}


class Discobot:
    _cls_registered_modules = []

    def __init__(self, client=None, *args, **kwargs):
        self.logger = logging.getLogger('discobot.Discobot')
        self.logger.info('Discobot coming online!')
        self.client = client or DiscobotClient()

        self.logger.info('Registering modules...')
        self.modules = plugins.registry.registry.instantiate_all(discobot=self)
        self.logger.info('Done registering modules!')

    def register(self, event, func, priority=100):
        return self.client._dc_register(event, func, priority=priority)

    def reload(self):
        import inspect
        import importlib

        self.logger.info('Reloading: unloading modules')
        for module in self.modules:
            self.logger.debug('Requesting that {} unload'.format(module))
            module.unload()

        self.modules = []
        self.client._dc_unregister_all()

        plugins.registry.registry.reload()
        self.modules = plugins.registry.registry.instantiate_all(discobot=self)
        self.configure(self._environ)
        self.loop.create_task(self.client.on_ready())  # cheat and dispatch a ready event

    def get_module(self, name):
        for f in self.modules:
             if f.name == name:
                 return f
        raise KeyError(name)

    @property
    def permissions(self):
        return self.get_module('permissions')

    @property
    def loop(self):
        return self.client.loop

    def configure(self, environ):
        for module in self.modules:
            module.configure(environ)
        self._environ = environ

    def run(self, *args, **kwargs):
        self.client.run(*args, **kwargs)


