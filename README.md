# openmensabot
Telegram bot, shows canteen/mensa menus from openmensa.org. Supports daily push messages.

This bot ran on Heroku. Python 3.10

## Run it locally
You need to set the environment variable `TELEGRAM_TOKEN` or hard-code it in [wsgi.py](https://github.com/cvzi/openmensabot/blob/master/wsgi.py#L27-L30) 
to your API Token from [BotFather](https://telegram.me/botfather).  

To test it locally you need a public hostname. This uses [ngrok](https://ngrok.com/), just download it, it's free and provides you
with a public URL for the webhook.
Move the ngrok executable to you PATH or in this directory.  
Then you can simply run:  
`python3 wsgi.py`

If you run it on a web server you don't need ngrok, you can just set the environment variable `PUBLIC_URL=https://yourhost.example.com`
