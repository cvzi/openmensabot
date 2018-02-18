#! python3
# Inspired by https://youtu.be/ufaOgM9QYk0

# Openshift 3 Flask app:

import os
from flask import Flask, request
application = Flask(__name__)

HOSTNAME = r"https://123.starter-us-east-1.openshiftapps.com"  # TODO your host name here
OPENSHIFT_DATA_DIR = os.getenv("OPENSHIFT_DATA_DIR","./data")  # TODO Persistent storage location



print("Starting mensabot.Bot")
import mensabot

mensaCacheFile = os.path.join(OPENSHIFT_DATA_DIR, "mensabot/mensacache.pickle")
userFile = os.path.join(OPENSHIFT_DATA_DIR, "mensabot/users.pickle")

myMensaBot = mensabot.Bot(mensaCacheFile=mensaCacheFile, userFile=userFile)
myMensaBotWebHook = myMensaBot.run(HOSTNAME + "/telegramMensaBot")

myMensaBot.worker()
print("mensabot.Bot is running")


@application.route("/")
def hello():
    return "Hello World!"
    
@application.route("/health")
def health():
    return "OK"
    
@application.route("/probe_readiness")
def probe_readiness():
    if "Running" in myMensaBot.status:
        return "OK", 200
    else:
        return "Bot is not running", 503
    
    
@application.route("/probe_liveness")
def probe_liveness():
    return "OK"
    
      
    
    
@application.route("/telegramMensaBot", methods=['GET', 'POST'])
def myMensaBotIncoming():
    myMensaBotWebHook.feed(request.data)
    return 'OK'


if __name__ == "__main__":
    application.run()
