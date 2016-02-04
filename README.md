discobot is a simple Discourse bot written in Python

It uses the excellent discord.py library over at [Rapptz/discord.py](https://github.com/Rapptz/discord.py) and implements a simple plugin system and permissions.

# Installing
To install:

1. `git clone https://github.com/lukegb/discobot.git`
2. `cd discobot`
3. `virtualenv --python=python3 env`
4. `source env/bin/activate`
5. `pip install -r requirements.txt`
6. `$EDITOR env/bin/activate`
7. Refer to [Configuring](#configuring)
8. `source env/bin/activate` (yes, again)
9. `python discobot.py`

# Configuring

discobot.py is set up to read its primary configuration out of the environment. This means you'll need to set a few environment variables to make it work.

If you've got here from step 7 in the guide above, you'll want to add (to the end of the file):

```bash
DISCOBOT_EMAIL=yourdiscordbots.registeredemailaccount@example.com
DISCOBOT_PASSWORD=yourdiscordbots.password
DISCOBOT_BOTMASTERS=your discord user ID
export DISCOBOT_EMAIL DISCOBOT_PASSWORD DISCOBOT_BOTMASTERS
```

## Getting your Discord user ID

Your Discord user ID is a long string of numbers. At some point, I'll add an easy guide on how to find this.

If you're technically minded, you can find it at the moment by running the bot with no `DISCOBOT_BOTMASTERS` specified, and then issuing the "help" command. Your user ID will appear in the logging output e.g.:

```
INFO:DiscobotPermissions:Checking permission permissions:revoke for user 102909905052114944
```

where `102909905052114944` is your user ID.
