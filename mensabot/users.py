#! python3
# Inspired by https://youtu.be/ufaOgM9QYk0

import time
import datetime
import pickle
import os
import threading


class Users:
    # Store persistent user data. Instead of a databse, this is just single pickle file.
    
    def __init__(self, userFile='data/user.pickle', nowTime=datetime.datetime.now().time()):
        self._userFile = userFile
        self._lastPushFetchTime = nowTime
        self.__lastSafe = time.time()
        self.__saveInterval = 120 # Seconds
        self.__saveFlag = False
        self.__threadLockFile = threading.RLock()
        self.__threadLockDB = threading.RLock()
        
        if os.path.isfile(self._userFile):
            with open(self._userFile, "rb" ) as fs:
                self._db = pickle.load( fs )
        else:
            self._db = {}

        
    def commitChanges(self):
        if self.__saveFlag and time.time() - self.__lastSafe > self.__saveInterval:
            self.__forceSafe()
            
    def forceCommit(self):
        self.__forceSafe()

    def __forceSafe(self):
        # Actually write data to disk
        print("Writing users file: %s" % self._userFile)
        with self.__threadLockFile:
            with open( self._userFile, "wb" ) as fs:
                pickle.dump(self._db, fs )
            self.__lastSafe = time.time()
            self.__saveFlag = False
        
    def __safe(self):
        self.__saveFlag = True

    def _set(self, uid, key, value):
        with self.__threadLockDB:
            if not uid in self._db:
                self._db[uid] = {"firstContact" : time.time()}

            self._db[uid][key] = value
            self.__safe()
            
    def _delete(self, uid, key):
        with self.__threadLockDB:
            if not uid in self._db:
                return

            self._db[uid].pop(key, None)
            self.__safe()
        
    def _get(self, uid, key, fallback="This is a unique fallback value: 123456789123456789123456789"):
        try:
            return self._db[uid][key]
        except KeyError:
            if fallback == "This is a unique fallback value: 123456789123456789123456789":
                raise e
            else:
                return fallback
        
    def _append(self, uid, key, value):
        if not self._appendIfNotExists(uid, key, value):
            with self.__threadLockDB:
                self._db[uid][key].append(value)
                self.__safe()
            
          
    def _appendIfNotExists(self, uid, key, value):
        with self.__threadLockDB:
            if not uid in self._db:
                self._db[uid] = {"firstContact" : time.time()}
        
            if not key in self._db[uid]:
                self._db[uid][key] = []

            if not value in self._db[uid][key]:
                self._db[uid][key].append(value)
                self.__safe()
                return True # Saved
            else:
                return False # Already there
                
    def _remove(self, uid, key, value):
        with self.__threadLockDB:
            if not uid in self._db:
                return
                
        
            if not key in self._db[uid]:
                return

            if not value in self._db[uid][key]:
                return
            else:
                self._db[uid][key].remove(value)
                self.__safe()

        
    def addUser(self, uid, name=None):
        if not uid in self._db:
            self._set(uid, "firstContact", time.time())
        if not "username" in self._db[uid] and name is not None:
            self._set(uid, "username", name)
            
    def deleteUser(self, uid):
        if not uid in self._db:
            return
        self._db.pop(uid, None)
        self.__safe()
            
    def getUsers(self):
        return self._db.keys()
        
    def getStats(self):
        # [(uid, username, timestamp, feedback), ...]
        tmp = []
        for uid in self._db:
            if "username" in self._db[uid] and "firstContact" in self._db[uid]:
                tmp.append((uid, self._db[uid]["username"], self._db[uid]["firstContact"], self.getFeedback(uid)))
            elif "firstContact" in self._db[uid]:
                tmp.append((uid, "<unknown>", self._db[uid]["firstContact"], self.getFeedback(uid)))
            else:
                tmp.append((uid, "<unknown>", 0, self.getFeedback(uid)))
        
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
            raise TypeError("at_time expected datetime.time. Given type was %s" % str(type(at_time)))
        self._set(uid, "push", at_time)
             
    def disablePush(self, uid):
        self._delete(uid, "push")
        
    def getPush(self, uid):
        return self._get(uid, "push", None)
        
    def enablePushSilent(self, uid):
        self._set(uid, "pushsilent", True)
        
    def disablePushSilent(self, uid):
        self._set(uid, "pushsilent", False)

    def isPushSilent(self, uid):
        return self._get(uid, "pushsilent", False)

    def getPendingPushObjects(self, now_time):
        # Return all push objects between _lastPushFetchTime and now_time
        # Set _lastPushFetchTime to now_time
        result = []
        for uid in self._db:
            if "push" in self._db[uid] and self.getFavorites(uid):
                if self._db[uid]["push"] > self._lastPushFetchTime and self._db[uid]["push"] <= now_time:
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
        
        
    
