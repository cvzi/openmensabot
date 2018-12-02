#! python3
# Inspired by https://youtu.be/ufaOgM9QYk0

import time
import datetime
import threading
import copy

class PostgresStorage:

    def __init__(self, databaseurl=None, conn=None):
        self.fields = ("username", "firstContact", "language")
        self.userdata = {}
        # TODO Sorry, Postgres queries are not open source :(
        print("Skipping Postgres connection")

    def storeField(self, uid, fields, values):
        # Store data in a specific field

        if not isinstance(fields, tuple) and not isinstance(fields, list):
            fields = (fields, )
        if not isinstance(values, tuple) and not isinstance(values, list):
            values = (values, )

        if len(fields) != len(values):
            raise ValueError(
                "Length of fields (%d) and values (%d) needs to be the same" %
                (len(fields), len(values)))

        for field in fields:
            if field not in self.fields:
                raise ValueError(
                    "'field' must be one of %r. Found %r" %
                    (self.fields, field))

        # TODO Sorry, Postgres queries are not open source :(

        if uid not in self.userdata:
            self.userdata[uid] = {}

        for field, value in zip(fields, values):
            self.userdata[uid][field] = value

    def storeData(self, uid, data):
        # Store data in the arbitrary 'data' field as json data

        # TODO Sorry, Postgres queries are not open source :(
        if uid not in self.userdata:
            self.userdata[uid] = {}
        self.userdata[uid]["data"] = data

    def retrieveUser(self, uid):
        # TODO Sorry, Postgres queries are not open source :(
        if uid not in self.userdata:
            self.userdata[uid] = {}
        return self.userdata[uid]

    def deleteUser(self, uid):
        # TODO Sorry, Postgres queries are not open source :(
        if uid in self.userdata:
            self.userdata.pop(uid)


# SQL version
class Users:
    def __init__(
            self,
            nowTime=datetime.datetime.now().time(),
            databaseurl=None):
        self._lastPushFetchTime = nowTime
        self.__threadLockDB = threading.RLock()

        self._db = PostgresStorage(databaseurl=databaseurl)

    def _set(self, uid, key, value):
        with self.__threadLockDB:
            if key in self._db.fields:
                # Additionaly store firstContact if no record exists
                if uid not in self._db.userdata and key != "firstContact":
                    self._db.storeField(
                        uid, (key, "firstContact"), (value, time.time()))
                elif uid not in self._db.userdata:
                    self._db.storeField(uid, (key, ), (value, ))
                elif uid in self._db.userdata:
                    # Only store if value has changed
                    if key not in self._db.userdata[uid] or self._db.userdata[uid][key] != value:
                        self._db.storeField(uid, (key, ), (value, ))
            else:
                data = self._db.userdata[uid]["data"] if uid in self._db.userdata and "data" in self._db.userdata[uid] else {
                }
                # Only store if value has changed
                if key not in data or data[key] != value:
                    data[key] = value
                    self._db.storeData(uid, data)

    def _delete(self, uid, key):
        with self.__threadLockDB:
            if uid not in self._db.userdata:
                return

            if key in self._db.fields:
                if key not in self._db.userdata[uid]:
                    return
                self._db.storeField(uid, (key, ), (None, ))
            else:
                if key not in self._db.userdata[uid]["data"]:
                    return
                data = self._db.userdata[uid]["data"] if uid in self._db.userdata and "data" in self._db.userdata[uid] else {
                }
                data.pop(key, None)
                self._db.storeData(uid, data)

    def _get(
            self,
            uid,
            key,
            fallback="This is a unique fallback value"):
        if key in self._db.fields and key in self._db.userdata[uid]:
            return self._db.userdata[uid][key]
        if "data" in self._db.userdata[uid] and key in self._db.userdata[uid]["data"]:
            return self._db.userdata[uid]["data"][key]
        if fallback == "This is a unique fallback value":
            raise KeyError("No key %r in userdata for uid=%r" % (key, uid))
        else:
            return fallback

    def _append(self, uid, key, value):
        # This only works on data fields
        if not self._appendIfNotExists(uid, key, value):
            with self.__threadLockDB:
                self._db.userdata[uid]["data"][key].append(value)
                self._db.storeData(uid, self._db.userdata[uid]["data"])

    def _appendIfNotExists(self, uid, key, value):
        # This only works on data fields
        with self.__threadLockDB:
            data = self._db.userdata[uid]["data"] if uid in self._db.userdata and "data" in self._db.userdata[uid] else {
            }

            if key not in data:
                data[key] = []

            if value in data[key]:
                return False  # Already there

            data[key].append(value)
            self._db.storeData(uid, data)
            return True  # Saved

    def _remove(self, uid, key, value):
        # This only works on data fields
        with self.__threadLockDB:
            data = self._db.userdata[uid]["data"] if uid in self._db.userdata and "data" in self._db.userdata[uid] else {
            }
            if key not in data:
                return

            if value not in data[key]:
                return

            data[key].remove(value)
            self._db.storeData(uid, data)

    def getDatabaseCopy(self):
        # Integrate "data" field
        data = {}
        for uid in self._db.userdata:
            data[uid] = {}
            for field in self._db.userdata[uid]:
                if field != "data":
                    data[uid][field] = copy.deepcopy(
                        self._db.userdata[uid][field])
                else:
                    for key in self._db.userdata[uid]["data"]:
                        data[uid][key] = copy.deepcopy(
                            self._db.userdata[uid]["data"][key])

        return data

    def isUser(self, uid):
        return uid in self._db.userdata

    def addUser(self, uid, name=None):
        if uid not in self._db.userdata:
            self._set(uid, "firstContact", time.time())
        if "username" not in self._db.userdata[uid] and name is not None:
            self._set(uid, "username", name)

    def deleteUser(self, uid):
        self._db.deleteUser(uid)

    def getUsers(self):
        return self._db.userdata.keys()

    def getStats(self):
        # [(uid, username, timestamp, feedback, askedforfeedback), ...]
        tmp = []
        for uid in self._db.userdata:
            if "username" in self._db.userdata[uid] and "firstContact" in self._db.userdata[uid]:
                tmp.append(
                    (uid,
                     self._db.userdata[uid]["username"],
                     self._db.userdata[uid]["firstContact"],
                     self.getFeedback(uid),
                     self.askedForFeedback(uid)))
            elif "firstContact" in self._db.userdata[uid]:
                tmp.append(
                    (uid,
                     "<unknown>",
                     self._db.userdata[uid]["firstContact"],
                     self.getFeedback(uid),
                     self.askedForFeedback(uid)))
            else:
                tmp.append(
                    (uid,
                     "<unknown>",
                     0,
                     self.getFeedback(uid),
                     self.askedForFeedback(uid)))

        tmp.sort(key=lambda item: item[2])

        return tmp

    def getUsername(self, uid):
        return self._get(uid, "username", None)

    def saveFavorite(self, uid, canteenid):
        self._appendIfNotExists(uid, "favorites", canteenid)

    def getFavorites(self, uid):
        return self._get(uid, "favorites", [])

    def isFavorite(self, uid, canteenid):
        return canteenid in self._get(uid, "favorites", [])

    def removeFavorite(self, uid, canteenid):
        self._remove(uid, "favorites", canteenid)

    def enablePush(self, uid, at_time):
        if not isinstance(at_time, datetime.time):
            raise TypeError(
                "at_time expected datetime.time. Given type was %s" % str(
                    type(at_time)))
        self._set(uid, "push", [at_time.hour, at_time.minute, at_time.second])

    def disablePush(self, uid):
        self._delete(uid, "push")

    def getPush(self, uid):
        arr = self._get(uid, "push", None)
        if not arr:
            return None

        return datetime.time(arr[0], arr[1], arr[2])

    def enablePushSilent(self, uid):
        self._set(uid, "pushsilent", True)

    def disablePushSilent(self, uid):
        self._set(uid, "pushsilent", False)

    def isPushSilent(self, uid):
        return self._get(uid, "pushsilent", True)

    def getPendingPushObjects(self, now_time):
        # Return all push objects between _lastPushFetchTime and now_time
        # Set _lastPushFetchTime to now_time
        result = []
        for uid in self._db.userdata:
            if "data" in self._db.userdata[uid] and "push" in self._db.userdata[uid]["data"] and self.getFavorites(
                    uid):
                at_time = self.getPush(uid)
                if at_time > self._lastPushFetchTime and at_time <= now_time:
                    result.append((uid, self.getFavorites(uid)))

        self._lastPushFetchTime = now_time
        return result

    def setLastCanteen(self, uid, canteenid):
        self._set(uid, "last_canteen", canteenid)

    def getLastCanteen(self, uid):
        return self._get(uid, "last_canteen", None)

    def enableEmojis(self, uid):
        self._set(uid, "emojis", True)

    def disableEmojis(self, uid):
        self._set(uid, "emojis", False)

    def showEmojis(self, uid):
        return self._get(uid, "emojis", True)

    def getLanguage(self, uid, fallback):
        return self._get(uid, "language", fallback)

    def setLanguage(self, uid, lang):
        self._set(uid, "language", lang)

    def saveFeedback(self, uid, text):
        self._append(uid, "feedback", text)

    def getFeedback(self, uid):
        return self._get(uid, "feedback", [])

    def askedForFeedback(self, uid):
        return self._get(uid, "askedforfeedback", False)

    def setAskedForFeedback(self, uid):
        self._set(uid, "askedforfeedback", True)

    def enableShowNotes(self, uid):
        self._set(uid, "shownotes", True)

    def disableShowNotes(self, uid):
        self._set(uid, "shownotes", False)

    def showNotes(self, uid):
        return self._get(uid, "shownotes", False)

    def setShowPrices(self, uid, role="all"):
        if role not in (
            False,
            "all",
            "students",
            "employees",
            "pupils",
                "others"):
            raise ValueError(
                "Argument 'role' must be one of (False, 'all', 'students', 'employees', 'pupils', 'others') in setShowPrices(uid=%s, role='%s')" %
                (str(uid), str(role)))
        self._set(uid, "showprices", role)

    def disableShowPrices(self, uid):
        self._set(uid, "showprices", False)

    def getShowPrices(self, uid):
        return self._get(uid, "showprices", False)
