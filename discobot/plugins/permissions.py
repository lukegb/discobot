from collections import defaultdict

from .base import DiscobotModule, registry
import discord


# we need to keep track of a tree of several layers of permissions:
#
# on users:
#   global (e.g. public commands)
#   per-server
#   per-serverchannel
#
# on serverroles:
#   per-server
#   per-serverchannel
#
# each permission can be True, False, or None at each layer
# True means "yes", False means "DEFINITELY no", and None means "continue looking"
# if we encounter a False at any point, we can immediately stop looking and deny the permission

GLOBAL_SERVER = discord.Object(id='global:server')
GLOBAL_CHANNEL = discord.Object(id='global:channel')
GLOBAL_USERROLE = discord.Object(id='global:userrole')


@registry.register_module
class DiscobotPermissions(DiscobotModule):
    name = 'permissions'

    def __init__(self, discobot):
        super().__init__(discobot)

        self.logger.info('Readying up!')
        self.superusers = []
        self.permissions = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: {})))
        self.logger.info('DiscobotPermissions, at your service.')

    def configure(self, environ):
        self.superusers = [discord.Object(id=bid) for bid in environ('DISCOBOT_BOTMASTERS', '').split(';') if bid]
        self.logger.info('Configured superusers: {}'.format(self.superusers))

    def build_permission_layers(self, user, channel=None):
        layers = []

        layers += [self.permissions[GLOBAL_SERVER][GLOBAL_CHANNEL][GLOBAL_USERROLE]]
        layers += [self.permissions[GLOBAL_SERVER][GLOBAL_CHANNEL][user]]

        if hasattr(user, 'server'):
            layers += [self.permissions[user.server][GLOBAL_CHANNEL][GLOBAL_USERROLE]]
            layers += [self.permissions[user.server][GLOBAL_CHANNEL][user]]

        if channel:
            layers += [self.permissions[channel.server][channel][GLOBAL_USERROLE]]
            layers += [self.permissions[channel.server][channel][user]]

        if hasattr(user, 'roles'):
            for role in user.roles:
                layers += [self.permissions[user.server][GLOBAL_CHANNEL][role]]
                if channel:
                    layers += [self.permissions[user.server][channel][role]]

        return layers

    def has_permission(self, user, permission, channel=None):
        self.logger.info('Checking permission {0} for user {1.id}'.format(permission, user))
        for u in self.superusers:
            if u.id == user.id:
                self.logger.debug('Permission {0} granted to {1.id}: is superuser'.format(permission, user))
                return True

        # OK, fine, we need to check each permission layer
        layers = self.build_permission_layers(user)
        state = False
        for layer in layers:
            val = layer.get(permission, None)
            if val == False:
                self.logger.info('Permission {0} denied to {1.id}: False found in layer {2}'.format(permission, user, layer))
                return False
            elif val == True:
                state = True
                self.logger.info('Permission {0} might be granted to {1.id}: True found in layer {2}'.format(permission, user, layer))
            elif val is None:
                pass
            else:
                self.logger.warning('Permission {0} check at layer {2} for {1.id}: found {3}?!?'.format(permission, user, layer, val))

        self.logger.debug('Final verdict: {0} granted to {1.id}? {2}'.format(permission, user, state))
        return state

    def set_permission(self, user_or_role, permission, state, channel=None, server=None):
        server = server or GLOBAL_SERVER
        channel = channel or GLOBAL_CHANNEL

        if channel is not GLOBAL_CHANNEL and not channel.is_private:
            server = channel.server

        self.permissions[server][channel][user_or_role] = state

    def parse_revoke_grant(self, message, rest):
        bits = rest.split(' ')
        if len(bits) != 3:
            return False, None

        wherestr, whostr, whatstr = bits
        server, channel, who, what = None, None, None, None

        if wherestr == 'global':
            server = GLOBAL_SERVER
            channel = GLOBAL_CHANNEL
        elif wherestr == 'server':
            server = message.server
            channel = GLOBAL_CHANNEL
        elif wherestr == 'channel':
            server = message.server
            channel = message.channel
        else:
            return False, '<where> must be "global", "server", or "channel"'

        who = None
        if whostr == 'everyone':
            who = GLOBAL_USERROLE
        if not who and server is not GLOBAL_SERVER:
            who = discord.utils.get(message.server.roles, name=whostr)
        if not who:
            who = discord.utils.get(message.server.members, name=whostr)
        if not who:
            return False, '<who> must be a username or a role - roles cannot be used if <where> is "global"'
        
        what = whatstr 
        return server, channel, who, what


    async def cmd_revoke(self, message, rest):
        if message.channel.is_private:
            return await self.respond(message, 'revoke must be sent in a channel, not via PM')

        res = self.parse_revoke_grant(message, rest)
        if len(res) == 2 and res[0] is False:
            msg = res[1] or 'revoke <where:global/server/channel> <who:everyone/username/rolename> <what>'
            # <where> <who> <what>
            return await self.respond(message, msg)
        elif len(res) != 4:
            self.logger.error("Got {} from parse_revoke_grant for {}".format(res, rest))
            return await self.respond(message, "Something went wrong.")

        server, channel, who, what = res
        self.permissions[server][channel][who][what] = False
        return await self.respond(message, "Revoked {} from {} on {}".format(what, 'everyone' if who is GLOBAL_USERROLE else who.name, 'every server' if server is GLOBAL_SERVER else ('this server' if channel is GLOBAL_CHANNEL else '#{}'.format(channel.name))))

    async def cmd_grant(self, message, rest):
        if message.channel.is_private:
            return await self.respond(message, 'grant must be sent in a channel, not via PM')

        res = self.parse_revoke_grant(message, rest)
        if len(res) == 2 and res[0] is False:
            msg = res[1] or 'grant <where:global/server/channel> <who:everyone/username/rolename> <what>'
            # <where> <who> <what>
            return await self.respond(message, msg)
        elif len(res) != 4:
            self.logger.error("Got {} from parse_revoke_grant for {}".format(res, rest))
            return await self.respond(message, "Something went wrong.")

        server, channel, who, what = res
        self.permissions[server][channel][who][what] = True
        return await self.respond(message, "Granted {} to {} on {}".format(what, 'everyone' if who is GLOBAL_USERROLE else who.name, 'every server' if server is GLOBAL_SERVER else ('this server' if channel is GLOBAL_CHANNEL else '#{}'.format(channel.name))))
