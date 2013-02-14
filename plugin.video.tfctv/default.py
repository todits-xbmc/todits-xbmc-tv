import sys, urllib, urllib2, json, cookielib, time, os.path
import xbmc, xbmcgui, xbmcplugin, xbmcaddon
import CommonFunctions

common = CommonFunctions
common.plugin = xbmcaddon.Addon().getAddonInfo('name')

# common.dbg = True # Default
# common.dbglevel = 3 # Default

def showCategories():
    categories = [
        { 'name' : 'Subscribed Shows', 'url' : 'SubscribedShows', 'mode' : 10 },
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
    listSubscribedFirst = True if xbmcplugin.getSetting(thisPlugin,'listSubscribedFirst') == 'true' else False
    italiciseUnsubscribed = True if xbmcplugin.getSetting(thisPlugin,'italiciseUnsubscribed') == 'true' else False
    subscribedShowIds = []
    if listSubscribedFirst or italiciseUnsubscribed: 
        # make an API call only if we're checking against subscribed shows
        subscribedShowIds = getSubscribedShowIds()
    unsubscribedShows = []
    subscribedShows = []
    for showHtml in latestShows:
        spanTitle = common.parseDOM(showHtml, "span", attrs = {'class' : 'showTitle'})
        title = common.parseDOM(spanTitle[0], "a")
        showTitle = common.replaceHTMLCodes(title[0].encode('utf8'))
        url = common.parseDOM(spanTitle[0], "a", ret = 'href')
        thumbnail = common.parseDOM(showHtml, "img", ret = 'src')
        url = url[0].replace('/Show/Details/', '/Show/_ShowEpisodes/')
        showId = int(url.replace('/Show/_ShowEpisodes/', ''))
        urlDocName = thumbnail[0][(thumbnail[0].rfind('/') + 1):]
        thumbnail = thumbnail[0].replace(urlDocName, urllib.quote(urlDocName))
        isSubscribed = False
        if showId in subscribedShowIds:
            isSubscribed = True
        else:
            isSubscribed = False
            if italiciseUnsubscribed:
                showTitle = '[I]' + showTitle + '[/I]'
        if listSubscribedFirst:
            if isSubscribed:
                # add them now
                addDir(showTitle, url, 3, thumbnail)
            else:
                # will add them later
                unsubscribedShows.append((showTitle, url, 3, thumbnail))
        else:
            addDir(showTitle, url, 3, thumbnail)
    # this will not be populated if we're not listing subscribed shows first
    for u in unsubscribedShows:
        addDir(u[0], u[1], u[2], u[3])
    return True
        
def showEpisodes(url):
    headers = [('Content-type', 'application/x-www-form-urlencoded'),
        ('X-Requested-With', 'XMLHttpRequest')]
    itemsPerPage = int(xbmcplugin.getSetting(thisPlugin,'itemsPerPage'))
    params = { 'page' : page, 'size' : itemsPerPage }
    jsonData = callServiceApi(url, params, headers)
    episodeList = json.loads(jsonData)
    totalEpisodes = int(episodeList['total'])
    episodeCount = page * itemsPerPage
    if totalEpisodes > episodeCount:
        addDir("Next >>",  url, 3, thumbnail, page + 1)
    for e in episodeList['data']:
        addDir(e['DateAiredStr'].encode('utf8'), str(e['EpisodeId']), 4, thumbnail)
    return True
        
def playEpisode(episodeId):
    quality = int(xbmcplugin.getSetting(thisPlugin,'quality'))
    errorCode = -1
    jsonData = ''
    episodeDetails = {}
    for i in range(int(xbmcplugin.getSetting(thisPlugin,'loginRetries')) + 1):
        jsonData = callServiceApi('/Ajax/GetMedia/%s?p=%s' % (int(episodeId), quality + 1))
        episodeDetails = json.loads(jsonData)
        errorCode = episodeDetails['errorCode']
        if errorCode == 0:
            break
        else:
            login()
    if errorCode == 0:
        liz=xbmcgui.ListItem(name, iconImage = "DefaultVideo.png", thumbnailImage = thumbnail)
        liz.setInfo( type="Video", infoLabels = { "Title": name } )
        url = episodeDetails['data']['Url']
        xbmc.Player().play(url, liz)
    else:
        dialog = xbmcgui.Dialog()
        dialog.ok("Could Not Play Item", "- This item is not part of your subscription", 
"- Or your subscription is already expired", "- Or your email and/or password is incorrect")
    return False

        
def getSubscribedShowIds():
    return getSubscribedShows()[0]
    
def getSubscribedShows():
    params = { 'page' : 1, 'size' : 1000 }
    headers = [('Content-type', 'application/x-www-form-urlencoded'),
        ('X-Requested-With', 'XMLHttpRequest')]
    jsonData = ''
    entitlementsData = {}
    for i in range(int(xbmcplugin.getSetting(thisPlugin,'loginRetries')) + 1):
        jsonData = callServiceApi("/User/_Entitlements", params, headers)
        entitlementsData = json.loads(jsonData)
        if entitlementsData['total'] != 0:
            break
        else:
            login()
    if entitlementsData['total'] > 1000:
        params = { 'page' : 1, 'size' : entitlementsData['total'] }
        jsonData = callServiceApi("/_Entitlements", params, headers)
    subscribedShows = []
    showIds = []
    for e in entitlementsData['data']:
        expiry = int(e['ExpiryDate'].replace('/Date(','').replace(')/', ''))
        if expiry >= (time.time() * 1000):
            jsonData = callServiceApi("/Packages/GetShows?packageId=%s" % (e['PackageId']))
            packagesData = json.loads(jsonData)
            for p in packagesData:
                if p['ShowId'] in showIds:
                    pass
                else:
                    subscribedShows.append(p)
                    showIds.append(p['ShowId'])
    return showIds, subscribedShows
    
def showSubscribedCategories(url):
    subscribedShows = getSubscribedShows()[1]
    categories = []
    for s in subscribedShows:
        if s['MainCategory'] in categories:
            pass
        else:
            categories.append(s['MainCategory'])
            addDir(s['MainCategory'], s['MainCategory'], 11, 'menu_logo.png')
    return True
    
def showSubscribedShows(url):
    subscribedShows = getSubscribedShows()[1]
    for s in subscribedShows:
        if s['MainCategory'] == url:
            showTitle = common.replaceHTMLCodes(s['Show'].encode('utf8'))
            addDir(s['Show'], '/Show/_ShowEpisodes/' + str(s['ShowId']), 3, 'menu_logo.png')
    return True

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
    cookieJar.clear()
    emailAddress = xbmcplugin.getSetting(thisPlugin,'emailAddress')
    password = xbmcplugin.getSetting(thisPlugin,'password')
    formdata = { "EmailAddress" : emailAddress, "Password": password }
    jsonData = callServiceApi("/User/_Login", formdata)
    loginData = json.loads(jsonData)
    
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

thisPlugin = int(sys.argv[1])
userAgent = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:18.0) Gecko/20100101 Firefox/18.0'
baseUrl = 'http://tfc.tv'
cookieFile = os.path.join(xbmc.translatePath(xbmcaddon.Addon().getAddonInfo('profile')), 'tfctv.cookie')
cookieJar = cookielib.LWPCookieJar(cookieFile)
try:
    cookieJar.load()
except:
    login()

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
    thumbnail=urllib.unquote_plus(params["thumbnail"])
except:
    pass
    
#login()

success = False
if mode == None or url == None or len(url) < 1:
    success = showCategories()
elif mode == 1:
    success = showSubCategories(url)
elif mode == 2:
    success = showShows(url)
elif mode == 3:
    success = showEpisodes(url)
elif mode == 4:
    success = playEpisode(url)
elif mode == 10:
    success = showSubscribedCategories(url)
elif mode == 11:
    success = showSubscribedShows(url)

if success == True:
    xbmcplugin.endOfDirectory(thisPlugin)

cookieJar.save()