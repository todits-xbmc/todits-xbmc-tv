    
import sys, urllib
import xbmcgui, xbmcplugin

handle = int(sys.argv[1])

def showMenu():
    addLink('Play', 'rtmp://37.59.35.214/edge/xxooiinjva78v94', 'Play', '', app = 'edge', PlayPath = 'xxooiinjva78v94', SWFPlayer = 'http://cdn.static.ilive.to/jwplayer/player.swf', PageURL = 'http://www.ilive.to', IsLive = '1', TcUrl = 'rtmp://37.59.35.214/edge/xxooiinjva78v94')        
        
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
    showMenu()

xbmcplugin.endOfDirectory(handle)

