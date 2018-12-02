# openmensabot
Telegram bot, shows mensa menus from openmensa.org. Supports daily push messages.  


Live on telegram: [https://telegram.me/OpenMensaRobot](https://telegram.me/OpenMensaRobot)  
This bot runs on Red Hat Openshift 3.

## Run it locally:
You need to change the file [mensabot/mensatoken.py](https://github.com/cvzi/openmensabot/blob/master/mensabot/mensatoken.py) 
and add you API Token from [BotFather](https://telegram.me/botfather).  

To test it locally you need a public hostname. This uses [ngrok](https://ngrok.com/), just download it, it's free and provides you
with a public URL for the Webhook.
Move the ngrok executable to you PATH or in this directory.  
Then you can simply run:  
`python3 wsgi.py`
