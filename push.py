import time
import os
import datetime

class LastPush:
    timeformat = "%Y-%m-%d %H:%M:%S.%f%z"
    timeformatNoZ = "%Y-%m-%d %H:%M:%S.%f"

    """ Store last pushTime in file"""
    def __init__(self, nowTime, pushFile='data/lastpush.txt'):
        if not isinstance(nowTime, datetime.datetime):
            raise ValueError("Expected datetime.datetime, received %r" % (nowTime, ))

        self._pushFile = pushFile
        if not os.path.isfile(self._pushFile):
            self.setPushTime(nowTime)
        else:
            try:
                datetimeobj = self.lastPushTime()  # Check if readably not corrupted
                if datetimeobj.date() != nowTime.date():  # Date is not today -> outdated
                    self.setPushTime(nowTime)
            except Exception as e:
                # Try recreating the file
                print("Push file corrupted: %r\nTrying to recreate %s" % (str(e), self._pushFile))
                os.remove(self._pushFile)
                self.setPushTime(nowTime)


    def lastPushTime(self):
        with open(self._pushFile, "r") as fs:
            s = fs.read()
        try:
            return datetime.datetime.strptime(s, LastPush.timeformat)
        except ValueError:
            return datetime.datetime.strptime(s, LastPush.timeformatNoZ)

    def setPushTime(self, nowTime):
        if not isinstance(nowTime, datetime.datetime):
            raise ValueError("Expected datetime.datetime, received %r" % (nowTime, ))

        with open(self._pushFile, "w") as fs:
            fs.write("%s" % nowTime.strftime(LastPush.timeformat))
