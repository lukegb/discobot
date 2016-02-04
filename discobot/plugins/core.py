from .base import DiscobotModule, registry
import discord
import random


@registry.register_module
class DiscobotCore(DiscobotModule):
    name = 'core'

    def __init__(self, discobot):
        super().__init__(discobot)

        self.logger.info('Readying up!')
        self.first_time = True
        self.discobot.register('ready', self.on_ready, priority=0)
        self.discobot.register('message', self.on_message)
        self.superusers = []
        self.logger.info('DiscobotCore, at your service.')

    async def on_ready(self):
        self.logger.info('Discord reports ready {}'.format('for the first time' if self.first_time else 'again...'))

        self.logger.debug('Setting up command prefixes')
        self.prefixes = ['!', self.client.user.mention, self.client.user.name + ': ']

        self.first_time = False

    def allowable_prefixes(self, channel):
        if channel.is_private:
            return self.prefixes + ['']
        return self.prefixes

    def message_is_command(self, message):
        allowable_prefixes = self.allowable_prefixes(message.channel)
        for prefix in allowable_prefixes:
             if message.content.startswith(prefix):
                 return message.content[len(prefix):]
        return None

    def resolve_command(self, module, command):
        allowable_modules = self.discobot.modules[::-1]
        if module is not None:
            allowable_modules = [m for m in allowable_modules if m.name == module]

        for module in allowable_modules:
            if hasattr(module, 'cmd_' + command):
                return getattr(module, 'cmd_' + command), '{}:{}'.format(module.name, command)

        return None, None

    async def on_message(self, message):
        self.logger.info('[{0.timestamp}] <{0.author}@{0.channel}> {0.content}'.format(message))
        if message.author == self.client.user:
            return

        command = self.message_is_command(message)
        if not command:
            return

        command = command.split(None, 1)
        rest = ''
        if len(command) == 1:
            command = command[0]
        else:
            command, rest = command

        module = None
        if ':' in command:
            module, _, command = command.partition(':')

        cmd_f, command_name = self.resolve_command(module, command)
        if not cmd_f or not command_name:
            return await self.respond(message, "I can't find that command.")

        has_permission = self.discobot.permissions.has_permission(user=message.author, permission=command_name, channel=message.channel)
        if not has_permission:
            return await self.respond(message, "I'm sorry, but you don't have permission to do '{}'.".format(command_name))

        return await cmd_f(message, rest)

    async def cmd_help(self, message, rest):
        parts = ['semver', 'alpha', 'beta', 'gamma', 'delta', 'sigma', 'kappa', 'prerelease', 'rc']
        return await self.respond(message, "Discobot v0.0.1-" + '-'.join([random.choice(parts) for _ in range(4)]))

    async def cmd_reload(self, message, rest):
        self.discobot.reload()
        return await self.respond(message, "Discobot reloaded, maybe?")


