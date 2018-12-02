import urllib.request
import urllib.parse
import json
import math
import time
import re
from datetime import datetime
import pickle
import threading
import os

from shortnames import shortnamesId2Name, shortnamesName2Id, shortnamesId2Fullname


class OpenMensa:

    def __init__(self, cacheFile='data/mensacache.pickle'):
        self.userAgentStr = "OpenMensaRobot Python-urllib/%s" % urllib.request.__version__
        self.originHostName = "example.com"  # TODO Set hostname
        self.referer = "https://example.com"  # TODO Set referer

        self.shortnamesId2Name = shortnamesId2Name  # {1: 'MgdbCa',  ...}
        self.shortnamesName2Id = shortnamesName2Id  # {'mgdbca': 1,  ...}
        # {1: 'Magdeburg, Mensa UniCampus',  ...}
        self.shortnamesId2Fullname = shortnamesId2Fullname

        self._cacheFile = cacheFile
        self._cache = {}
        if os.path.isfile(self._cacheFile):
            with open(self._cacheFile, "rb") as fs:
                self._cache = pickle.load(fs)
                print("OpenMensa: cache file loaded: %s" % self._cacheFile)
        else:
            dirname = os.path.dirname(self._cacheFile)
            if not os.path.exists(dirname):
                os.makedirs(dirname, exist_ok=True)

        self.__shortNameCache = {}
        self.__shortNamePattern = re.compile(r"\W")

        self.__threadLock = threading.RLock()

    @staticmethod
    def distance(lat0, lng0, lat1, lng1):
        # https://stackoverflow.com/questions/27928/calculate-distance-between-two-latitude-longitude-points-haversine-formula
        p = 0.017453292519943295  # Pi/180
        a = 0.5 - math.cos((lat1 - lat0) * p) / 2 + math.cos(lat0 * p) * \
            math.cos(lat1 * p) * (1 - math.cos((lng1 - lng0) * p)) / 2
        return 12742 * math.asin(math.sqrt(a))  # 2*R*asin...

    @staticmethod
    def __getCacheKey(url, get_data=None):
        return url + "?" + \
            urllib.parse.urlencode("" if get_data is None else get_data)

    def __isCached(self, cachekey, expire):
        with self.__threadLock:
            if cachekey in self._cache:
                if time.time() - self._cache[cachekey][0] < expire:
                    return True
                else:
                    # Remove expired entry from cache
                    self._cache.pop(cachekey, None)
                    return False
        return False

    def _getJSON(self, url, get_data=None):
        if get_data is not None:
            payload = urllib.parse.urlencode(get_data)
            url_get = "%s?%s" % (url, payload)
        else:
            get_data = {}
            url_get = url

        # Valid URL?
        if not url.startswith("http://") and not url.startswith("https://"):
            raise RuntimeError("URL does not start with http")

        print("OpenMensa: GET: %s" % url_get)
        req = urllib.request.Request(
            url_get,
            headers={
                "User-Agent": self.userAgentStr,
                'Referer': self.referer},
            origin_req_host=self.originHostName)
        with urllib.request.urlopen(req) as r:
            data = json.loads(
                r.read().decode(
                    r.info().get_param('charset') or 'utf-8'))

        while "X-Total-Pages" in r.headers and "X-Current-Page" in r.headers and int(
                r.headers["X-Current-Page"]) < int(r.headers["X-Total-Pages"]):
            get_data['page'] = int(r.headers["X-Current-Page"]) + 1
            payload = urllib.parse.urlencode(get_data)
            url_get = "%s?%s" % (url, payload)
            req = urllib.request.Request(
                url_get,
                headers={
                    "User-Agent": self.userAgentStr},
                origin_req_host=self.originHostName)
            print("OpenMensa: GET: %s" % url_get)
            with urllib.request.urlopen(req) as r:
                nextpage = json.loads(
                    r.read().decode(
                        r.info().get_param('charset') or 'utf-8'))
                data.extend(nextpage)

        return data

    def _getJSONCached(self, url, get_data=None, expire=1800):
        cachekey = self.__getCacheKey(url, get_data)
        with self.__threadLock:
            if self.__isCached(cachekey, expire):
                data = self._cache[cachekey][1]
                # print("OpenMensa: CACHE: %s" % cachekey)
            else:
                data = self._getJSON(url, get_data)
                self._cache[cachekey] = (time.time(), data)
                with open(self._cacheFile, "wb") as fs:
                    pickle.dump(self._cache, fs)
        return data

    def getNextMeal(self, canteen, offsetDays=0, at_day=None):
        days = self._getJSONCached(
            'https://openmensa.org/api/v2/canteens/%d/days' %
            canteen)

        i = -1
        for day in days:
            if at_day is not None:
                if at_day == day['date']:
                    # at_day
                    if day['closed']:
                        return (day['date'], [], False)
                    else:
                        data = self._getJSONCached(
                            'https://openmensa.org/api/v2/canteens/%d/days/%s/meals' %
                            (canteen, day['date']))
                        return (day['date'], data, True)

            elif not day['closed']:
                # offsetDays
                i += 1
                if i == offsetDays:
                    data = self._getJSONCached(
                        'https://openmensa.org/api/v2/canteens/%d/days/%s/meals' %
                        (canteen, day['date']))
                    return (day['date'], data, True)

        try:
            return (day['date'], [], False)  # no open day found
        except BaseException:
            return (None, [], False)  # no days at all found

    def getNextMealIfCached(self, canteen, expire=1800):
        url = 'https://openmensa.org/api/v2/canteens/%d/days' % canteen
        if self.__isCached(self.__getCacheKey(url), expire):
            days = self._getJSONCached(url)
            if datetime.now().time() > datetime.strptime("15:00", '%H:%M').time():
                days = days[1:] if len(days) else []

            day = None
            for day in days:
                if not day['closed']:
                    url = 'https://openmensa.org/api/v2/canteens/%d/days/%s/meals' % (
                        canteen, day['date'])
                    if self.__isCached(self.__getCacheKey(url), expire):
                        data = self._getJSONCached(url)
                        return (day['date'], data, True)
                    else:
                        return None  # Meals not in cache

            if day:
                return (day['date'], [], False)  # no open day found
        return None  # Days not in cache

    def findMensaNear(self, lat=49.405479, lng=8.683767, dist=20):
        url = 'http://openmensa.org/api/v2/canteens'

        return self._getJSONCached(
            url, {"near[lat]": lat, "near[lng]": lng, "near[dist]": dist})

    def findMensaAll(self):
        url = 'http://openmensa.org/api/v2/canteens'

        data = self._getJSONCached(url, get_data={"limit": 9999}, expire=86400)

        if len(data) != len(self.shortnamesId2Name):
            print(
                "len(findMensaAll) = %d  !=  len(shortnames) = %d\nUpdate shortnames?" %
                (len(data), len(
                    self.shortnamesId2Name)))

        return data

    def findMensaByString(self, query):
        data = self.findMensaAll()

        query = query.lower().strip().split()

        result = []
        for mensa in data:
            name = mensa["name"].lower()
            city = mensa["city"].lower() if "city" in mensa else ""
            adress = mensa["adress"].lower() if "adress" in mensa else ""
            shortname = self.getShortName(mensa["id"]).lower()

            if query == shortname:
                result.append(mensa)
                continue

            matches = [False for sub in query]
            for i in range(len(query)):
                if query[i] in name or query[i] in city or query[i] in adress or query[i] in shortname:
                    matches[i] = True
            if all(matches):
                result.append(mensa)
        return result

    def __shortName(self, name):
        if name not in self.__shortNameCache:
            self.__shortNameCache[name] = self.__shortNamePattern.sub("", name)
        return self.__shortNameCache[name]

    def getShortName(self, canteenid):
        mensas = self.findMensaAll()
        mymensa = None
        for mensa in mensas:
            if mensa["id"] == canteenid:
                mymensa = mensa
                break
        if mymensa is None:
            # print("Mensa id=%s not found" % str(canteenid))
            return False

        i = 0
        myname = self.__shortName(mymensa["name"])
        for mensa in mensas:
            if mensa != mymensa and self.__shortName(mensa["name"]) == myname:
                i += 1
            elif mensa == mymensa:
                break

        if i == 0:
            return myname

        return "%s_%d" % (myname, i)

    @staticmethod
    def getHardcodedShortName(canteenid):
        if canteenid in shortnamesId2Name:
            return shortnamesId2Name[canteenid]
        return False

    @staticmethod
    def getIdFromHardcodedShortName(shortname):
        if shortname in shortnamesName2Id:
            return shortnamesName2Id[shortname]
        return False

    def getIdFromShortName(self, shortname):
        if shortname in shortnamesName2Id:
            return shortnamesName2Id[shortname]

        mensas = self.findMensaAll()

        if re.search(r"(\w+?)_(\d+)$", shortname):
            myname, myi = re.search(r"(\w+?)_(\d+)$", shortname).groups()
            myi = int(myi)
        else:
            myname = shortname
            myi = 0

        myname = myname.lower()

        i = 0
        for mensa in mensas:
            if self.__shortName(mensa["name"]).lower() == myname:
                if i != myi:
                    i += 1
                else:
                    return mensa["id"]

        # print("Mensa short=%s not found" % str(shortname))
        return False

    def getMensa(self, canteenid):
        mensas = self.findMensaAll()
        for mensa in mensas:
            if mensa["id"] == canteenid:
                return mensa

        print("Mensa id=%s not found" % str(canteenid))
        return None
