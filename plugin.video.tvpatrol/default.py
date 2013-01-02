    
import sys, urllib, re
import xbmcgui, xbmcplugin
from pyamf.remoting.client import RemotingService

handle = int(sys.argv[1])

categoryData = {
    'live'   : { 
                 'name' : 'Live', 
                 'icon' : 'menu_logo.jpg',
                 'serviceName' : 'com.brightcove.experience.ExperienceRuntimeFacade',
                 'serviceUrl' : 'http://c.brightcove.com/services/messagebroker/amf?playerKey=AQ~~,AAABtXvbPVE~,ZfNKKkFP3R-R8qlcWfs20DL-8Bvb6UcW',
                 'serviceKey' : 'aa3634a3b4371a1c2f780f830dc2fd1ef4bbb111',
                 'playerId' : 1905932797001
    },
    'replay' : { 
                 'name' : 'Replay',
                 'icon' : 'menu_logo.jpg',
                 'serviceName' : 'com.brightcove.experience.ExperienceRuntimeFacade',
                 'serviceUrl' : 'http://c.brightcove.com/services/messagebroker/amf?playerKey=AQ~~,AAABtXvbPVE~,ZfNKKkFP3R8lv_FZU4AZv5yZg6d3YSFW',
                 'serviceKey' : 'f7d4096475cca62e0afb88633662b4df1f429b98',
                 'playerId' : 1933244636001
    }
}

def showCategories():
    c = categoryData['live']
    addDir(c['name'], 'live', 1, c['icon'])
    c = categoryData['replay']
    addDir(c['name'], 'replay', 1, c['icon'])        
        
        
def showEpisodes(url):
    c = categoryData[url]
    client = RemotingService(c['serviceUrl'])
    service = client.getService(c['serviceName'])
    data = service.getProgrammingForExperience(c['serviceKey'], c['playerId'])
    if url == 'live':
        for d in data['playlistCombo']['lineupListDTO']['playlistDTOs'][0]['videoDTOs']:
            if d['FLVFullLengthStreamed']:
                pattern = re.compile(r'/live/&(LS_TVPatrol.+)')
                streamUrl = d['FLVFullLengthURL']
                m = pattern.search(streamUrl)
                playPath = m.group(1)
                addLink(d['displayName'], streamUrl, d['displayName'], '', IsLive = '1', app = 'live', PlayPath = playPath)
            else:
                addLink(d['displayName'], d['FLVFullLengthURL'], d['displayName'], '', IsLive = '1')
    elif url == 'replay':
        pattern = re.compile(r'/ondemand/&(mp4:.+\.mp4)\?')
        for d in data['playlistTabs']['lineupListDTO']['playlistDTOs'][0]['videoDTOs']:
            streamUrl = d['FLVFullLengthURL']
            m = pattern.search(streamUrl)
            app = 'ondemand'
            playPath = m.group(1)
            streamUrl = streamUrl.replace('/ondemand/&mp4', '/ondemand/mp4')
            addLink(d['displayName'], streamUrl, d['displayName'], d['thumbnailURL'], app = app, PlayPath = playPath)

        
    
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

def addLink(name, url, title, iconimage, **kwargs):
    liz = xbmcgui.ListItem(name, iconImage = "DefaultVideo.png", thumbnailImage = iconimage)
    liz.setInfo(type = "Video", infoLabels = {"Title" : title})
    for k, v in kwargs.iteritems():
        liz.setProperty(k, v)
    return xbmcplugin.addDirectoryItem(handle = handle, url = url, listitem = liz)
    
def addDir(name,url,mode,iconimage):
    u = sys.argv[0] + "?url=" + urllib.quote_plus(url) + "&mode=" + str(mode) + "&name=" + urllib.quote_plus(name)
    liz = xbmcgui.ListItem(name, iconImage = "DefaultFolder.png", thumbnailImage = iconimage)
    liz.setInfo(type = "Video", infoLabels = {"Title" : name})
    return xbmcplugin.addDirectoryItem(handle = handle, url = u, listitem = liz, isFolder = True)

params=getParams()
url=None
name=None
mode=None

try:
    url=urllib.unquote_plus(params["url"])
except:
    pass
try:
    name=urllib.unquote_plus(params["name"])
except:
    pass
try:
    mode=int(params["mode"])
except:
    pass

if mode == None or url == None or len(url) < 1:
    showCategories()
elif mode == 1:
    showEpisodes(url)

xbmcplugin.endOfDirectory(handle)

