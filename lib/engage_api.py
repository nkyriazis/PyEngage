from urllib2 import Request, urlopen
from urllib import urlencode
import json
import datetime


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
    return (dt - milis2date(0)).total_seconds() * 1000.0


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
                      aggPeriod='month', aggFunc='avg'):
        print fromTime
        print toTime
        result = self.call('getTimeSeries', offset=-2 * offset,
                           fromTime=date2milis(fromTime), toTime=date2milis(toTime),
                           aggPeriod=aggPeriod, aggFunc=aggFunc)
        return result

    def mapTimeSeries(self, getter):
        results = self.call(getter)
        return sorted([(milis2date(int(key)), val[0]) for key, val in results['data'].iteritems()])

    def getDay(self):
        return self.mapTimeSeries('getDay')

    def getWeek(self):
        return self.mapTimeSeries('getWeek')

    def getMonth(self):
        return self.mapTimeSeries('getMonth')

    def getYear(self):
        return self.mapTimeSeries('getYear')
