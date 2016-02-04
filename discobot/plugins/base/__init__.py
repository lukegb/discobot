import logging

class DiscobotModule:
    def __init__(self, discobot):
        self.discobot = discobot
        if not hasattr(self, 'name'):
            self.name = self.__class__.__name__
        self.logger = logging.getLogger(self.__class__.__name__)

    def configure(self, environ):
        pass

    def unload(self):
        pass

    @property
    def client(self):
        return self.discobot.client

    async def respond(self, message, content):
        return await self.client.send_message(message.channel, ((message.author.mention + ' ') if not message.channel.is_private else '') + content)


def public_command(f):
    f.public = True
    return f
