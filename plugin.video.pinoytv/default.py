    
import sys, urllib
import xbmcgui, xbmcplugin

handle = int(sys.argv[1])

def showMenu():
    addDir('ABS-CBN', 'abscbnlive', 1, 'abscbn_logo.jpg')
    addLink('PBA Live', 'rtmp://85.12.5.5/vl/_definst_', 'PBA Live', '', app = 'vl/_definst_', PlayPath = 'sportspbalive', SWFPlayer = 'http://www.veemi.com/player/player-licensed.swf', PageURL = 'http://www.veemi.com', TcUrl = 'rtmp://85.12.5.5/vl/_definst_')
    
def showSubMenu(url):
    if url == 'abscbnlive':
        hosts = ['37.59.35.214', '46.105.111.187']
        ctr = 1
        for h in hosts:
            addLink('Play Stream %s' % ctr, 'rtmp://%s/edge/xxooiinjva78v94' % (h), 'Play Stream %s' % ctr, '', app = 'edge', PlayPath = 'xxooiinjva78v94', SWFPlayer = 'http://cdn.static.ilive.to/jwplayer/player.swf', PageURL = 'http://www.ilive.to', IsLive = '1', TcUrl = 'rtmp://%s/edge/xxooiinjva78v94' % (h))
            ctr += 1
        
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
    showMenu()
elif mode == 1:
    showSubMenu(url)

xbmcplugin.endOfDirectory(handle)

