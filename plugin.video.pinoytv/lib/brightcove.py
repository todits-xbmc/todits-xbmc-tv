import pyamf, httplib
from pyamf.remoting.client import RemotingService
from pyamf import remoting, amf3, util

class BrightCove(object):
    def __init__(self, token, playerKey, serviceUrl = 'http://c.brightcove.com/services/messagebroker/amf', serviceName = 'com.brightcove.experience.ExperienceRuntimeFacade'):
        self._token = token
        self._playerKey = playerKey
        self._serviceName = serviceName
        self._amfUrl = serviceUrl + '?playerKey=' + playerKey

    def getBrightCoveData(self, playerId, userAgent, amfVersion = pyamf.AMF3, **kwargs):
        client = RemotingService(self._amfUrl, user_agent = userAgent, amf_version = amfVersion)
        for k, v in kwargs.iteritems():
            if k == 'headers':
                for header in v:
                    client.addHTTPHeader(header[0], header[1])
            if k == 'proxy':
                client.setProxy(v)
        service = client.getService(self._serviceName)
        return service.getProgrammingForExperience(self._token, playerId)
        
    def findMediaById(self, playerId, videoPlayer, publisherId, userAgent, amfVersion = pyamf.AMF3, **kwargs):
        client = RemotingService(self._amfUrl, user_agent = userAgent, amf_version = amfVersion)
        for k, v in kwargs.iteritems():
            if k == 'headers':
                for header in v:
                    client.addHTTPHeader(header[0], header[1])
            if k == 'proxy':
                client.setProxy(v)
        service = client.getService(self._serviceName)
        return service.findMediaById(self._token, playerId, videoPlayer, publisherId)