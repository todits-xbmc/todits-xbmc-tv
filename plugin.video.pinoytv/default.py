import sys, urllib
import xbmcgui, xbmcplugin

handle = int(sys.argv[1])
userAgent = 'Mozilla/5.0 (X11; Linux x86_64; rv:17.0) Gecko/20100101 Firefox/17.0'

def getMenu(channel, id, userAgent):
    entries = []
    if id == 'main':
        from channels import abscbn, gma, ibc, studio23
        entries.append(abscbn.getMenu(id, userAgent))
        entries.append(gma.getMenu(id, userAgent))
        entries.append(ibc.getMenu(id, userAgent))
        entries.append(studio23.getMenu(id, userAgent))
    else:
        channelModule = __import__(channel, fromlist = [''])
        entries.append(channelModule.getMenu(id, userAgent))
    return entries
        
def displayMenu(channel, id, userAgent):
    menuList = getMenu(channel, id, userAgent)
    for channel, menu in menuList:
        for m in menu:
            if m['isFolder']:
                kwargs = m['kwargs'] if m.has_key('kwargs') else {}
                addDir(m['name'], m['id'], channel, m['icon'], **kwargs)
            else:
                kwargs = m['kwargs'] if m.has_key('kwargs') else {}
                addLink(m['name'], m['url'], m['id'], m['icon'], **kwargs)
                
def playItem(channel, id, userAgent):
    channelModule = __import__(channel, fromlist = [''])
    channelModule.play(id, userAgent)
        
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
    for kwargsKey, kwargsValue in kwargs.iteritems():
        if kwargsKey == 'listProperty':
            for propertyKey, propertyValue in kwargsValue.iteritems():
                liz.setProperty(propertyKey, propertyValue)
    return xbmcplugin.addDirectoryItem(handle = handle, url = url, listitem = liz)
    
def addDir(name, id, channel, icon, **kwargs):
    play = 0
    for k, v in kwargs.iteritems():
        if k == 'play' and v:
            play = 1
    u = sys.argv[0] + "?id=" + urllib.quote_plus(id) + "&channel=" + urllib.quote_plus(channel) + "&name=" + urllib.quote_plus(name) + '&play=' + str(play)
    liz = xbmcgui.ListItem(name, iconImage = "DefaultFolder.png", thumbnailImage = icon)
    liz.setInfo(type = "Video", infoLabels = {"Title" : name})
    return xbmcplugin.addDirectoryItem(handle = handle, url = u, listitem = liz, isFolder = True)

params=getParams()
id=None
channel = None
name=None
play = 0

try:
    id=urllib.unquote_plus(params["id"])
except:
    pass
try:
    channel = urllib.unquote_plus(params["channel"])
except:
    pass
try:
    name=urllib.unquote_plus(params["name"])
except:
    pass
try:
    play = int(params["play"])
except:
    pass

callEndOfDirectory = True
if id == None or len(id) < 1:
    displayMenu(channel, 'main', userAgent)
elif play == 1:
    playItem(channel, id, userAgent)
    callEndOfDirectory = False
else:
    displayMenu(channel, id, userAgent)

if callEndOfDirectory:
    xbmcplugin.endOfDirectory(handle)

