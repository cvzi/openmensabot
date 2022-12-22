import time
import datetime
import os
import threading
import copy

import psycopg2
import json

from push import LastPush

class PostgresStorage:

    def _execute(self, sql, vars=tuple()):
        if not isinstance(vars, dict) and not isinstance(vars, tuple):
            raise ValueError("Parameter 'vars' needs to be a tuple or a dict. Found %r" % type(vars))

        result = False
        try:
            cur = self.conn.cursor()
            cur.execute(sql, vars)
            result = True
        except psycopg2.InterfaceError as error:
            print(error.message)
            if(self._reconnect()):
                try:
                    cur = self.conn.cursor()
                    cur.execute(sql, vars)
                    result = True
                except BaseException:
                    print("_execute:Could not commit after reconnect.")
            else:
                print("_execute:Could not reconnect.")
        except (Exception, psycopg2.DatabaseError) as error:
            print("_execute:Postgres Error: %s\n%r" % (str(error), sql))
        finally:
            if self.conn:
                # Always commit, otherwise all queries after an error will fail
                self.conn.commit()
            if cur is not None:
                cur.close()
        return result

    def _fetchone(self, sql, vars=tuple()):
        if not isinstance(vars, dict) and not isinstance(vars, tuple):
            raise ValueError("Parameter 'vars' needs to be a tuple or a dict. Found %r" % type(vars))

        result = None
        try:
            cur = self.conn.cursor()
            cur.execute(sql, vars)
            result = cur.fetchone()
        except psycopg2.InterfaceError as error:
            print(error.message)
            if(self._reconnect()):
                try:
                    cur = self.conn.cursor()
                    cur.execute(sql, vars)
                    result = cur.fetchone()
                except BaseException:
                    print("_fetchone:Could not fetch after reconnect.")
            else:
                print("_fetchone:Could not reconnect.")
        except (Exception, psycopg2.DatabaseError) as error:
            print("_fetchone:Postgres Error: %s\n%r" % (str(error), sql))
        finally:
            if cur is not None:
                cur.close()
        return result

    def _fetchcursor(self, sql, vars=tuple()):
        if not isinstance(vars, dict) and not isinstance(vars, tuple):
            raise ValueError("Parameter 'vars' needs to be a tuple or a dict. Found %r" % type(vars))

        try:
            cur = self.conn.cursor()
            cur.execute(sql, vars)
            return cur
        except psycopg2.InterfaceError as error:
            print(error.message)
            if(self._reconnect()):
                cur = self.conn.cursor()
                cur.execute(sql, vars)
                return cur
            else:
                print("_fetchcursor:Could not reconnect")
                raise error

    def _reconnect(self):
        """ Try to reconnect after lost connection"""
        if self.__databaseurl is None:
            raise Exception("Cannnot _reconnent, no databaseurl found.")
        try:
            self.conn.commit()
        except BaseException:
            pass
        try:
            self.conn.close()
        except BaseException:
            pass
        try:
            self.conn = psycopg2.connect(self.__databaseurl, sslmode='require')
            return True
        except psycopg2.InterfaceError as error:
            print(error.message)

        return False

    def __init__(self, databaseurl=None, conn=None):
        self.__databaseurl = databaseurl
        if not conn:
            if databaseurl is None:
                raise ValueError("Either parameter 'databaseurl' or 'conn' is required.")
            self.__databaseurl = databaseurl
            self.conn = psycopg2.connect(databaseurl, sslmode='require')
        else:
            self.conn = conn

        self.fields = ("username", "firstContact", "language")
        # e.g. Automatically cast NUMERIC(20,6) or DECIMAL to float
        self.field_types = (str, float, str)

        if len(self.fields) != len(self.field_types):
            raise RuntimeError("self.fields and self.field_types need to match in length")

        self._execute("""
        CREATE TABLE IF NOT EXISTS users (
            uid             BIGINT          PRIMARY KEY     NOT NULL,
            username        TEXT,
            firstContact    NUMERIC(20,6),
            language        VARCHAR(20),
            data            JSONB
        )""")

        self._lastReload = {}

        self.retrieveAll()

    def retrieveAll(self):
        now = time.time()
        fieldsql = ""
        for field in self.fields:
            fieldsql += ", %s" % field
        sql = "SELECT uid, data " + fieldsql + " FROM users"
        try:
            cur = self._fetchcursor(sql)
            self.userdata = {}
            for r in cur:
                uid = r[0]
                self.userdata[uid] = {}

                if r[1]:
                    data = r[1]
                else:
                    data = {}

                self.userdata[uid]["data"] = data

                for i, (field, fieldtype) in enumerate(zip(self.fields, self.field_types)):
                    if r[i + 2] is not None:
                        self.userdata[uid][field] = fieldtype(r[i + 2])
                self._lastReload[uid] = now
            print("Fetched userdata from postgres")

        except psycopg2.InterfaceError as e:
            print("Could not connect")

        finally:
            if cur is not None:
                cur.close()

        return self.userdata

    def storeField(self, uid, fields, values):
        # Store data in a specific field

        if not isinstance(fields, tuple) and not isinstance(fields, list):
            fields = (fields, )
        if not isinstance(values, tuple) and not isinstance(values, list):
            values = (values, )

        if len(fields) != len(values):
            raise ValueError("Length of fields (%d) and values (%d) needs to be the same" % (len(fields), len(values)))

        for field in fields:
            if field not in self.fields:
                raise ValueError("'field' must be one of %r. Found %r" % (self.fields, field))

        if uid not in self.userdata:
            valuessql = ["%s" for value in values]
            vars = [value for value in values]
            vars.insert(0, uid)
            sql = "INSERT INTO users (uid, " + (", ".join(fields)) + ") VALUES (%s, " + (", ".join(valuessql)) + ")"
            self._execute(sql, tuple(vars))
        else:
            fieldsql = []
            for field in fields:
                fieldsql.append(field + "=%s")
            sql = "UPDATE users SET " + (", ".join(fieldsql)) + " WHERE uid=%s"
            vars = [value for value in values]
            vars.append(uid)

            self._execute(sql, tuple(vars))

        if not uid in self.userdata:
            self.userdata[uid] = {}

        for field, value in zip(fields, values):
            self.userdata[uid][field] = value

    def storeData(self, uid, data):
        # Store data in the arbitrary 'data' field as json data

        #jdata = codecs.encode(pickle.dumps(data), "base64").decode()
        jdata = json.dumps(data)

        if uid not in self.userdata or not self.userdata[uid]:
            sql = "INSERT INTO users (uid, data) VALUES (%s, %s)"
            self._execute(sql, (uid, jdata))
        else:
            sql = "UPDATE users SET data=%s WHERE uid=%s"
            self._execute(sql, (jdata, uid))

        if not uid in self.userdata:
            self.userdata[uid] = {}
        self.userdata[uid]["data"] = data

    def retrieveUser(self, uid):

        fieldsql = ""
        for field in self.fields:
            fieldsql += ", %s" % field

        sql = "SELECT data " + fieldsql + " FROM users WHERE uid=%s LIMIT 1"
        r = self._fetchone(sql, (uid, ))

        if r:
            self.userdata[uid] = {}
            jdata = r[0]

            if jdata:
                #data = pickle.loads(codecs.decode(r[0].encode(), "base64"))
                #data = json.loads(r[0])
                data = r[0]
            else:
                data = {}
            self.userdata[uid]["data"] = data

            for i, (field, fieldtype) in enumerate(zip(self.fields, self.field_types)):
                if r[i + 1] is not None:
                    self.userdata[uid][field] = fieldtype(r[i + 1])

            self._lastReload[uid] = time.time()

            return self.userdata[uid]
        else:
            if uid in  self.userdata:
                del self.userdata[uid]
            return {}


    def deleteUser(self, uid):
        sql = "DELETE FROM users WHERE uid=%s"
        self._execute(sql, (uid, ))

        if uid in self.userdata:
            self.userdata.pop(uid)


# SQL version
class Users:
    def __init__(
            self,
            nowTime,
            databaseurl=None):
        self.__threadLockDB = threading.RLock()

        self._lastPush = LastPush(nowTime)

        self._db = PostgresStorage(databaseurl=databaseurl)

        if not isinstance(nowTime, datetime.datetime):
            raise ValueError("Expected datetime.datetime, received %r" % (nowTime, ))

    def postgresConnection(self):
        return self._db.conn


    def _reload(self, uid, nocache=False):
        if uid in self._db._lastReload and uid in self._db.userdata and time.time() - self._db._lastReload[uid] < 0.5:
            return  # Cache is good for 0.5 seconds
        self._db.retrieveUser(uid)

    def _reloadAll(self):
        return self._db.retrieveAll()

    def _set(self, uid, key, value):
        self._reload(uid)
        with self.__threadLockDB:
            if key in self._db.fields:
                # Additionaly store firstContact if no record exists
                if (uid not in self._db.userdata or "firstContact" not in self._db.userdata[uid]) and key != "firstContact":
                    self._db.storeField(
                        uid, (key, "firstContact"), (value, time.time()))
                elif uid not in self._db.userdata:
                    self._db.storeField(uid, (key, ), (value, ))
                elif uid in self._db.userdata and (key not in self._db.userdata[uid] or self._db.userdata[uid][key] != value):
                    # Only store if value has changed or does not exist
                    self._db.storeField(uid, (key, ), (value, ))
            else:
                # Additionaly store firstContact if no record exists
                if uid not in self._db.userdata or "firstContact" not in self._db.userdata[uid]:
                    self._db.storeField(
                        uid, (key, "firstContact"), (value, time.time()))
                data = self._db.userdata[uid]["data"] if uid in self._db.userdata and "data" in self._db.userdata[uid] else {}
                # Only store if value has changed
                if key not in data or data[key] != value:
                    data[key] = value
                    self._db.storeData(uid, data)

    def _delete(self, uid, key):
        self._reload(uid)
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
                data = self._db.userdata[uid]["data"] if uid in self._db.userdata and "data" in self._db.userdata[uid] else {}
                data.pop(key, None)
                self._db.storeData(uid, data)

    def _get(
            self,
            uid,
            key,
            fallback="This is a unique fallback value: 123456789123456789123456789"):
        self._reload(uid)
        if uid in self._db.userdata:
            if key in self._db.fields and key in self._db.userdata[uid]:
                return self._db.userdata[uid][key]
            if "data" in self._db.userdata[uid] and key in self._db.userdata[uid]["data"]:
                return self._db.userdata[uid]["data"][key]
        if fallback == "This is a unique fallback value: 123456789123456789123456789":
            raise KeyError("No key %r in userdata for uid=%r" % (key, uid))
        else:
            return fallback

    def _append(self, uid, key, value):
        # This only works on data fields
        self._reload(uid)
        if not self._appendIfNotExists(uid, key, value):
            with self.__threadLockDB:
                self._db.userdata[uid]["data"][key].append(value)
                self._db.storeData(uid, self._db.userdata[uid]["data"])

    def _appendIfNotExists(self, uid, key, value):
        # This only works on data fields
        self._reload(uid)
        with self.__threadLockDB:
            data = self._db.userdata[uid]["data"] if uid in self._db.userdata and "data" in self._db.userdata[uid] else {}

            if key not in data:
                data[key] = []

            if value in data[key]:
                return False  # Already there

            data[key].append(value)
            self._db.storeData(uid, data)
            return True  # Saved

    def _remove(self, uid, key, value):
        # This only works on data fields
        self._reload(uid)
        with self.__threadLockDB:
            data = self._db.userdata[uid]["data"] if uid in self._db.userdata and "data" in self._db.userdata[uid] else {}
            if key not in data:
                return

            if value not in data[key]:
                return

            data[key].remove(value)
            self._db.storeData(uid, data)

    def getDatabaseCopy(self):
        # Integrate "data" field
        self._reloadAll()
        data = {}
        for uid in self._db.userdata:
            data[uid] = {}
            for field in self._db.userdata[uid]:
                if field != "data":
                    data[uid][field] = copy.deepcopy(
                        self._db.userdata[uid][field])
                else:
                    for key in self._db.userdata[uid]["data"]:
                        data[uid][key] = copy.deepcopy(self._db.userdata[uid]["data"][key])

        return data

    def getStats(self):
        # [(uid, username, timestamp, feedback, askedforfeedback), ...]
        self._reloadAll()
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

    def isUser(self, uid):
        return uid in self._db.userdata

    def addUser(self, uid, name=None):
        if uid not in self._db.userdata:
            self._set(uid, "firstContact", time.time())
        if "username" not in self._db.userdata[uid] and name is not None:
            self._set(uid, "username", name)

    def getUser(self, uid):
        if uid in self._db.userdata:
            return self._db.userdata[uid]
        else:
            return {}

    def deleteUser(self, uid):
        self._db.deleteUser(uid)

    def getUsers(self):
        return self._db.userdata.keys()

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
            raise TypeError("at_time expected datetime.time. Given type was %s" % str(type(at_time)))
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

    def getPendingPushObjects(self, now):
        # Return all push objects between lastPushFetchTime and now_time

        lastPushFetchTime = self._lastPush.lastPushTime().time()
        self._lastPush.setPushTime(now)
        now_time = now.time()

        self._reloadAll()
        result = []
        for uid in self._db.userdata:
            if "data" in self._db.userdata[uid] and "push" in self._db.userdata[uid]["data"] and self.getFavorites(uid):
                at_time = self.getPush(uid)
                if at_time > lastPushFetchTime and at_time <= now_time:
                    result.append((uid, self.getFavorites(uid)))

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
            raise ValueError("Argument 'role' must be one of (False, 'all', 'students', 'employees', 'pupils', 'others') in setShowPrices(uid=%s, role='%s')" % (str(uid), str(role)))
        self._set(uid, "showprices", role)

    def disableShowPrices(self, uid):
        self._set(uid, "showprices", False)

    def getShowPrices(self, uid):
        return self._get(uid, "showprices", False)
