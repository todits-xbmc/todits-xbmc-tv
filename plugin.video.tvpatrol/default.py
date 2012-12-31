    
import sys, urllib, re
import xbmcgui, xbmcplugin
from pyamf.remoting.client import RemotingService

handle = int(sys.argv[1])

def showCategories():
    categories = [
        # { 'name' : 'Live', 'url' : '/tvpatrollive' },
        { 'name' : 'Replay', 'url' : '/tvpatrolreplay' }
    ]
    for c in categories:
        addDir(c['name'], c['url'], 1, 'menu_logo.png')
        
def showEpisodes(url):
    client = RemotingService('http://c.brightcove.com/services/messagebroker/amf?playerKey=AQ~~,AAABtXvbPVE~,ZfNKKkFP3R8lv_FZU4AZv5yZg6d3YSFW')
    service = client.getService('com.brightcove.experience.ExperienceRuntimeFacade')
    data = service.getProgrammingForExperience('f7d4096475cca62e0afb88633662b4df1f429b98', 1933244636001)
    pattern = re.compile(r'/ondemand/&(mp4:.+\.mp4)\?')
    for d in data['playlistTabs']['lineupListDTO']['playlistDTOs'][0]['videoDTOs']:
        url = d['FLVFullLengthURL']
        m = pattern.search(url)
        app = 'ondemand'
        playPath = m.group(1)
        url = url.replace('/ondemand/&mp4', '/ondemand/mp4')
        addLink(d['displayName'], url, d['displayName'], d['thumbnailURL'], app, playPath)
    
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

def addLink(name, url, title, iconimage, app, playPath):
    liz = xbmcgui.ListItem(name, iconImage = "DefaultVideo.png", thumbnailImage = iconimage)
    liz.setInfo(type = "Video", infoLabels = {"Title" : title})
    liz.setProperty('app', app)
    liz.setProperty('PlayPath',  playPath)
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

