from urllib2 import Request, urlopen
from urllib import urlencode
import json
import datetime
import numpy as np
from itertools import izip


def dourl(req):
    request = Request(req)
    return json.loads(urlopen(request).read())


def do(url, params):
    req = url + '?' + urlencode(params)
    return dourl(req)


def merge_dicts(d1, d2):
    ret = d1.copy()
    ret.update(d2)
    return ret


def milis2date(millis):
    return datetime.datetime.utcfromtimestamp(millis / 1000.0)


def date2milis(dt):
    return (dt - milis2date(0)).total_seconds()


class EngageLink(object):
    base = 'https://engage.efergy.com/mobile/'
    base_proxy = 'https://engage.efergy.com/mobile_proxy/'

    def __init__(self, token=None, username=None, password=None):
        if token is not None:
            self.token = token
        elif username is not None and password is not None:
            self.token = do(self.base + 'get_token', {'username': username, 'password': password, 'device': 'android'})[
                'token']
        else:
            raise RuntimeError('need to specify either token or username and password')

    def call(self, method, **params):
        return do(self.base_proxy + method, merge_dicts({'token': self.token}, params))

    def getInstant(self):
        result = self.call('getInstant')
        return result['reading'], result['age'], milis2date(result['last_reading_time'])

    def getMontlyBudget(self):
        return self.call('getBudget')['monthly_budget']

    def getCost(self, zoneOffset=+2, period='custom',
                fromTime=datetime.datetime.now() - datetime.timedelta(days=1),
                toTime=datetime.datetime.now()):
        result = self.call('getCost', offset=-zoneOffset * 60,
                           fromTime=date2milis(fromTime),
                           toTime=date2milis(toTime))
        return result['sum'], result['units']

    def getTimeSeries(self, offset=+2,
                      fromTime=datetime.datetime.now() - datetime.timedelta(days=1),
                      toTime=datetime.datetime.now(),
                      aggPeriod='minute', aggFunc='avg'):
        results = self.call('getTimeSeries',
                            offset=-60 * offset,
                            fromTime=date2milis(fromTime),
                            toTime=date2milis(toTime),
                            aggPeriod=aggPeriod,
                            aggFunc=aggFunc)
        return sorted([(milis2date(int(key)), val[0]) for key, val in results['data'].iteritems() if val[0] != 'undef'])

    def mapTimeSeries(self, getter, offset):
        results = self.call(getter, offset=-60 * offset)
        return sorted([(milis2date(int(key)), val[0]) for key, val in results['data'].iteritems() if val[0] != 'undef'])

    def getDay(self, offset=0):
        return self.mapTimeSeries('getDay', offset)

    def getWeek(self, offset=0):
        return self.mapTimeSeries('getWeek', offset)

    def getMonth(self, offset=0):
        return self.mapTimeSeries('getMonth', offset)

    def getYear(self, offset=0):
        return self.mapTimeSeries('getYear', offset)

    def getImageDate(self, imgFilename):
        from PIL import Image
        TSTAG = 36867
        img = Image.open(imgFilename)
        exif = img._getexif()
        return datetime.datetime.strptime(exif[TSTAG][0], '%Y:%m:%d %H:%M:%S')

    def getTimeSeriesBetweenImages(self, img1, img2, offset=2):
        return self.getTimeSeries(offset=offset,
                                  fromTime=self.getImageDate(img1),
                                  toTime=self.getImageDate(img2))

    def integrateTimeSeries(self, timeSeries):
        kwhs = np.array([ts[1] for ts in timeSeries])
        kwhs = kwhs[~np.isnan(kwhs)]
        return kwhs.sum() * (1.0 / 60.0)

    def computeCost(self, timeSeries, timeDependentKwhTariffFunc):
        kwhs = np.array([ts[1] for ts in timeSeries])
        mask = ~np.isnan(kwhs)
        times = np.array([ts[0] for ts in timeSeries])
        costs = np.array([timeDependentKwhTariffFunc(t.time()) for t in times])
        return np.sum([cost * kwh * (1.0 / 60.0) for cost, kwh in izip(costs[mask], kwhs[mask])])
