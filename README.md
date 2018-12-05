# openmensabot
Telegram bot, shows mensa menus from openmensa.org. Supports daily push messages.  

Live on telegram: [https://telegram.me/OpenMensaRobot](https://telegram.me/OpenMensaRobot)  
This bot runs on Red Hat Openshift 3.

## Run it locally
You need to set the environment variable `TELEGRAM_TOKEN` or hardcode it in [wsgi.py](https://github.com/cvzi/openmensabot/blob/master/wsgi.py#L25-L28) 
to your API Token from [BotFather](https://telegram.me/botfather).  

To test it locally you need a public hostname. This uses [ngrok](https://ngrok.com/), just download it, it's free and provides you
with a public URL for the Webhook.
Move the ngrok executable to you PATH or in this directory.  
Then you can simply run:  
`python3 wsgi.py`

If you run it on a webserver you don't need ngrok, you can just set the environment variable `PUBLIC_URL=https://yourhost.example.com`
