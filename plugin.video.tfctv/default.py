    
import sys, urllib, urllib2, json, cookielib
import xbmc, xbmcgui, xbmcplugin, xbmcaddon

thisPlugin = int(sys.argv[1])

import CommonFunctions
common = CommonFunctions
common.plugin = xbmcaddon.Addon().getAddonInfo('name')

userAgent = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:17.0) Gecko/20100101 Firefox/17.0'
baseUrl = 'http://tfc.tv'
cookieJar = cookielib.CookieJar()

def showCategories():
    categories = [
        { 'name' : 'Entertainment', 'url' : '/Menu/BuildMenuGroup/Entertainment', 'mode' : 1 },
        { 'name' : 'News', 'url' : '/Menu/BuildMenuGroup/News', 'mode' : 1 },
        { 'name' : 'Movies', 'url' : '/Menu/BuildMenuGroup/Movies', 'mode' : 1 },
        { 'name' : 'Live', 'url' : '/Menu/BuildMenuGroup/Live', 'mode' : 1 },
        { 'name' : 'Free TV', 'url' : '/Show/_ShowEpisodes/929', 'mode' : 3 }
    ]
    for c in categories:
        addDir(c['name'], c['url'], c['mode'], 'icon.png')
    return True

def showSubCategories(url):
    jsonData = callServiceApi(url)
    subCatList = json.loads(jsonData)
    for s in subCatList:
        addDir(s['name'], '/Category/List/%s' % s['id'], 2, 'menu_logo.png')
    return True
        
def showShows(url):
    htmlData = callServiceApi(url)
    latestShowsHtml = common.parseDOM(htmlData, "div", attrs = {'id' : 'latestShows_bodyContainer'})
    latestShows = common.parseDOM(latestShowsHtml[0], "div", attrs = {'class' : 'showItem_preview ht_265'})
    for showHtml in latestShows:
        spanTitle = common.parseDOM(showHtml, "span", attrs = {'class' : 'showTitle'})
        title = common.parseDOM(spanTitle[0], "a")
        url = common.parseDOM(spanTitle[0], "a", ret = 'href')
        thumbnail = common.parseDOM(showHtml, "img", ret = 'src')
        url = url[0].replace('/Show/Details/', '/Show/_ShowEpisodes/')
        addDir(common.replaceHTMLCodes(title[0].encode('utf8')), url, 3, thumbnail[0])
    return True
        
def showEpisodes(url):
    print url
    headers = [('Content-type', 'application/x-www-form-urlencoded'),
        ('X-Requested-With', 'XMLHttpRequest')]
    itemsPerPage = int(xbmcplugin.getSetting(thisPlugin,'itemsPerPage'))
    params = { 'page' : page, 'size' : itemsPerPage }
    jsonData = callServiceApi(url, params, headers)
    episodeList = json.loads(jsonData)
    totalEpisodes = int(episodeList['total'])
    episodeCount = page * itemsPerPage
    listedEpisodes = 0
    for e in episodeList['data']:
        quality = int(xbmcplugin.getSetting(thisPlugin,'quality'))
        jsonData = callServiceApi('/Ajax/GetMedia/%s?p=%s' % (e['EpisodeId'], quality + 1))
        episodeDetails = json.loads(jsonData)
        if episodeDetails['errorCode'] == 0:
            listedEpisodes += 1
            if listedEpisodes == 1:
                if totalEpisodes > episodeCount:
                    addDir("Next >>",  url, 3, thumbnail, page + 1)
            itemUrl = episodeDetails['data']['Url']
            addLink(e['DateAiredStr'], itemUrl, '', '')
        else:
            break
    if listedEpisodes == 0:
        dialog = xbmcgui.Dialog()
        dialog.ok("Not Subscribed To This Item", "Could not find this item in your TFC.tv subscription.")
        return False
    else:
        return True
        
def getEntitlements():
    params = { 'page' : 1, 'size' : 1000 }
    headers = [('Content-type', 'application/x-www-form-urlencoded'),
        ('X-Requested-With', 'XMLHttpRequest')]
    jsonData = callServiceApi("/_Entitlements", params, headers)
    

def callServiceApi(path, params = {}, headers = []):
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookieJar))
    headers.append(('User-Agent', userAgent))
    opener.addheaders = headers
    if params:
        data_encoded = urllib.urlencode(params)
        response = opener.open(baseUrl + path, data_encoded)
    else:
        response = opener.open(baseUrl + path)
    return response.read()

def login():
    emailAddress = xbmcplugin.getSetting(thisPlugin,'emailAddress')
    password = xbmcplugin.getSetting(thisPlugin,'password')
    formdata = { "EmailAddress" : emailAddress, "Password": password }
    jsonData = callServiceApi("/User/_Login", formdata)
    loginData = json.loads(jsonData)
    if loginData['errorCode'] != 0:
        dialog = xbmcgui.Dialog()
        dialog.ok("Login failed", loginData['errorMessage'])
    
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

def addLink(name,url,title,iconimage):
    liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
    liz.setInfo( type="Video", infoLabels={ "Title": title } )
    return xbmcplugin.addDirectoryItem(handle=thisPlugin,url=url,listitem=liz)

def addDir(name, url, mode, thumbnail, page = 1):
    u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)+"&page="+str(page)+"&thumbnail="+urllib.quote_plus(thumbnail)
    liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=thumbnail)
    liz.setInfo( type="Video", infoLabels={ "Title": name } )
    return xbmcplugin.addDirectoryItem(handle=thisPlugin,url=u,listitem=liz,isFolder=True)

params=getParams()
url=None
name=None
mode=None
page=1
thumbnail = ''

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
try:
    page=int(params["page"])
except:
    pass
try:
    thumbnail=int(params["thumbnail"])
except:
    pass
    
login()

success = False
if mode == None or url == None or len(url) < 1:
    success = showCategories()
elif mode == 1:
    success = showSubCategories(url)
elif mode == 2:
    success = showShows(url)
elif mode == 3:
    success = showEpisodes(url)

if success == True:
    xbmcplugin.endOfDirectory(thisPlugin)

