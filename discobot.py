import discobot
import logging

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    import os
    def environ(env_name, default=None):
        sentinel = None
        if default is None:
            sentinel = object()
            default = sentinel
        value = os.environ.get(env_name, default)
        if sentinel and value is sentinel:
            raise KeyError("{} is not set in the environment.".format(env_name))
        return value

    username = environ('DISCOBOT_EMAIL')
    password = environ('DISCOBOT_PASSWORD')

    bot = discobot.Discobot()
    bot.configure(environ)
    bot.run(username, password)
