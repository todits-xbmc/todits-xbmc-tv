    
import sys, urllib, re
import xbmcgui, xbmcplugin
from pyamf.remoting.client import RemotingService

handle = int(sys.argv[1])
userAgent = 'Mozilla/5.0 (X11; Linux x86_64; rv:17.0) Gecko/20100101 Firefox/17.0'

def getMenu(id):
    if id == 'tvpatrol-live':
        return getTvPatrolMenu('live')
    if id == 'tvpatrol-replay':
        return getTvPatrolMenu('ondemand')
    if id == 'bandila':
        return getBandilaMenu('ondemand')
    if id == 'abscbn-live':
        return getAbsCbnLiveMenu()
    menu = {
        'main' : [  { 'id' : 'abscbn', 'name' : 'ABS-CBN', 'icon' : 'abscbn_logo.jpg', 'isFolder' : True},
                    {   'name' : 'PBA Live', 
                        'url' : 'rtmp://85.12.5.5/vl/_definst_', 
                        'title' : 'PBA Live', 
                        'icon' : '', 
                        'isFolder' : False,
                        'extraArgs' : {
                                        'app' : 'vl/_definst_', 
                                        'PlayPath' : 'sportspbalive', 
                                        'SWFPlayer' : 'http://www.veemi.com/player/player-licensed.swf', 
                                        'PageURL' : 'http://www.veemi.com', 
                                        'TcUrl' : 'rtmp://85.12.5.5/vl/_definst_'
                        }
                    }
        ],
        
        'abscbn' : [{ 'id' : 'tvpatrol', 'name' : 'TV Patrol', 'icon' : 'tvpatrol_logo.jpg', 'isFolder' : True},
                    { 'id' : 'bandila', 'name' : 'Bandila', 'icon' : 'bandila_logo.jpg', 'isFolder' : True},
                    { 'id' : 'abscbn-live', 'name' : 'Live', 'icon': 'abscbn_logo.jpg', 'isFolder' : True}
        ],
        
        'tvpatrol' : [  {'id' : 'tvpatrol-live', 'name' : 'Live', 'icon' : 'tvpatrol_logo.jpg', 'isFolder' : True},
                        {'id' : 'tvpatrol-replay', 'name' : 'Replay', 'icon' : 'tvpatrol_logo.jpg', 'isFolder' : True}
        ]
    }
    return menu[id]

def getTvPatrolMenu(streamType):
    serviceData = {
        'live'   : { 
                     'name' : 'Live', 
                     'icon' : 'tvpatrol_logo.jpg',
                     'serviceName' : 'com.brightcove.experience.ExperienceRuntimeFacade',
                     'serviceUrl' : 'http://c.brightcove.com/services/messagebroker/amf?playerKey=AQ~~,AAABtXvbPVE~,ZfNKKkFP3R-R8qlcWfs20DL-8Bvb6UcW',
                     'serviceKey' : 'aa3634a3b4371a1c2f780f830dc2fd1ef4bbb111',
                     'playerId' : 1905932797001,
                     'playPathRegexPattern' : r'/live/&(LS_TVPatrol.+)'
        },
        'ondemand' : { 
                     'name' : 'Replay',
                     'icon' : 'tvpatrol_logo.jpg',
                     'serviceName' : 'com.brightcove.experience.ExperienceRuntimeFacade',
                     'serviceUrl' : 'http://c.brightcove.com/services/messagebroker/amf?playerKey=AQ~~,AAABtXvbPVE~,ZfNKKkFP3R8lv_FZU4AZv5yZg6d3YSFW',
                     'serviceKey' : 'f7d4096475cca62e0afb88633662b4df1f429b98',
                     'playerId' : 1933244636001,
                     'playPathRegexPattern' : r'/ondemand/&(mp4:.+\.mp4)\?'
        }
    }
    response = callBrightCoveService(serviceData, streamType)
    brightCoveData = []
    if streamType == 'live':
        brightCoveData = response['playlistCombo']['lineupListDTO']['playlistDTOs'][0]['videoDTOs']
    elif streamType == 'ondemand':
        brightCoveData = response['playlistTabs']['lineupListDTO']['playlistDTOs'][0]['videoDTOs']
        
    return getBrightCoveMenu(serviceData, streamType, brightCoveData)
    
def getBandilaMenu(streamType):
    serviceData = {
        'ondemand'   : { 
                     'name' : 'Ondemand', 
                     'icon' : 'bandila_logo.jpg',
                     'serviceName' : 'com.brightcove.experience.ExperienceRuntimeFacade',
                     'serviceUrl' : 'http://c.brightcove.com/services/messagebroker/amf?playerKey=AQ~~,AAABtXvbPVE~,ZfNKKkFP3R_F56e3g2DVHn4JP7JQvZsz',
                     'serviceKey' : '1e901d1b97bc4590fa2d3924a8ec642d684afca4',
                     'playerId' : 1927018689001,
                     'playPathRegexPattern' : r'/ondemand/&(mp4:.+\.mp4)\?'
        }
    }
    response = callBrightCoveService(serviceData, streamType)
    brightCoveData = response['videoList']['mediaCollectionDTO']['videoDTOs']
        
    return getBrightCoveMenu(serviceData, streamType, brightCoveData)
    
def callBrightCoveService(serviceData, streamType):
    c = serviceData[streamType]
    client = RemotingService(c['serviceUrl'], user_agent = userAgent)
    service = client.getService(c['serviceName'])
    return service.getProgrammingForExperience(c['serviceKey'], c['playerId'])
    
def getBrightCoveMenu(serviceData, streamType, data):
    menu = []
    c = serviceData[streamType]
    pattern = re.compile(c['playPathRegexPattern'])
    if streamType == 'live':
        for d in data:
            if d['FLVFullLengthStreamed']:
                streamUrl = d['FLVFullLengthURL']
                m = pattern.search(streamUrl)
                playPath = m.group(1)
                menuItem = {'name' : d['displayName'], 'url' : streamUrl, 'title' : d['displayName'], 'icon' : '', 'isFolder' : False, 'extraArgs' : { 'IsLive' : '1', 'app' : 'live', 'PlayPath' : playPath}};
            else:
                menuItem = {'name' : d['displayName'], 'url' : d['FLVFullLengthURL'], 'title' : d['displayName'], 'icon' : '', 'isFolder' : False, 'extraArgs' : { 'IsLive' : '1'}};
            menu.append(menuItem)
    elif streamType == 'ondemand':
        for d in data:
            streamUrl = d['FLVFullLengthURL']
            m = pattern.search(streamUrl)
            app = 'ondemand'
            playPath = m.group(1)
            streamUrl = streamUrl.replace('/ondemand/&mp4', '/ondemand/mp4')
            menu.append({'name' : d['displayName'], 'url' : streamUrl, 'title' : d['displayName'], 'icon' : d['thumbnailURL'], 'isFolder' : False, 'extraArgs' : { 'app' : app, 'PlayPath' : playPath}})
    return menu

def getAbsCbnLiveMenu():
    hosts = ['37.59.35.214', '46.105.111.187']
    ctr = 1
    menu = []
    for h in hosts:
        menuItem = {'name' : 'Play Stream %s' % ctr, 
                    'url' : 'rtmp://%s/edge/xxooiinjva78v94' % (h), 
                    'title' : 'Play Stream %s' % ctr, 
                    'icon' : '', 
                    'isFolder' : False,
                    'extraArgs' : { 'app' : 'edge', 
                                    'PlayPath' : 'xxooiinjva78v94', 
                                    'SWFPlayer' : 'http://cdn.static.ilive.to/jwplayer/player.swf', 
                                    'PageURL' : 'http://www.ilive.to', 
                                    'IsLive' : '1', 
                                    'TcUrl' : 'rtmp://%s/edge/xxooiinjva78v94' % (h)
                    }
        }
        menu.append(menuItem)
        ctr += 1
    return menu
        
def displayMenu(id):
    for m in getMenu(id):
        if m['isFolder'] == True:
            addDir(m['name'], m['id'], m['icon'])
        else:
            addLink(m['name'], m['url'], m['title'], m['icon'], **m['extraArgs'])
        
def getParams():
    param={}
    paramstring=sys.argv[2]
    if len(paramstring)>=2:
            params=sys.argv[2]
            cleanedparams=params.replace('?','')
            if (params[len(params)-1]=='/'):
                    params=params[0:len(params)-2]
            pairsofparams=cleanedparams.split('&')
            param={}
            for i in range(len(pairsofparams)):
                    splitparams={}
                    splitparams=pairsofparams[i].split('=')
                    if (len(splitparams))==2:
                            param[splitparams[0]]=splitparams[1]
    return param

def addLink(name, url, title, icon, **kwargs):
    liz = xbmcgui.ListItem(name, iconImage = "DefaultVideo.png", thumbnailImage = icon)
    liz.setInfo(type = "Video", infoLabels = {"Title" : title})
    for k, v in kwargs.iteritems():
        liz.setProperty(k, v)
    return xbmcplugin.addDirectoryItem(handle = handle, url = url, listitem = liz)
    
def addDir(name, id, icon):
    u = sys.argv[0] + "?id=" + urllib.quote_plus(id) + "&name=" + urllib.quote_plus(name)
    liz = xbmcgui.ListItem(name, iconImage = "DefaultFolder.png", thumbnailImage = icon)
    liz.setInfo(type = "Video", infoLabels = {"Title" : name})
    return xbmcplugin.addDirectoryItem(handle = handle, url = u, listitem = liz, isFolder = True)

params=getParams()
id=None
name=None

try:
    id=urllib.unquote_plus(params["id"])
except:
    pass
try:
    name=urllib.unquote_plus(params["name"])
except:
    pass
    
if id == None or len(id) < 1:
    displayMenu('main')
else:
    displayMenu(id)

xbmcplugin.endOfDirectory(handle)

