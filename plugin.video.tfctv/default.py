import sys, urllib, urllib2, json, cookielib, time, os.path, hashlib
import xbmc, xbmcgui, xbmcplugin, xbmcaddon
from lib.SimpleCache import SimpleCache

import CommonFunctions
common = CommonFunctions
thisAddon = xbmcaddon.Addon()
common.plugin = thisAddon.getAddonInfo('name')
cacheExpirySeconds = int(thisAddon.getSetting('cacheHours')) * 60 * 60

# common.dbg = True # Default
# common.dbglevel = 3 # Default

def showCategories():
    accountChanged = checkAccountChange()
    clearCacheOnNextEntry = True if thisAddon.getSetting('clearCacheOnNextEntry') == 'true' else False
    if accountChanged or clearCacheOnNextEntry:
        cleanCache(True)
        if clearCacheOnNextEntry:
            thisAddon.setSetting('clearCacheOnNextEntry', 'false')
    else:
        cleanCache(False)
    categories = [
        { 'name' : 'Subscribed Shows', 'url' : 'SubscribedShows', 'mode' : 10 },
        { 'name' : 'Entertainment', 'url' : '/Menu/BuildMenuGroup/Entertainment', 'mode' : 1 },
        { 'name' : 'News', 'url' : '/Menu/BuildMenuGroup/News', 'mode' : 1 },
        { 'name' : 'Movies', 'url' : '/Menu/BuildMenuGroup/Movies', 'mode' : 1 },
        #{ 'name' : 'Live', 'url' : '/Menu/BuildMenuGroup/Live', 'mode' : 1 },
        { 'name' : 'Free TV', 'url' : '/Show/_ShowEpisodes/929', 'mode' : 3 }
    ]
    for c in categories:
        addDir(c['name'], c['url'], c['mode'], 'icon.png')
    xbmcplugin.endOfDirectory(thisPlugin)

def getFromCache(key, expirySeconds = cacheExpirySeconds):
    try:
        if isCacheEnabled:
            cacheKey = hashlib.sha1(key).hexdigest()
            return SimpleCache(expirySeconds).get(cacheKey)
        else:
            return None
    except:
        return None

def setToCache(key, value, expirySeconds = cacheExpirySeconds):
    try:
        if isCacheEnabled:
            cacheKey = hashlib.sha1(key).hexdigest()
            SimpleCache(expirySeconds).set(cacheKey, value)
    except:
        pass

def cleanCache(force = False):
    try:
        if isCacheEnabled:
            purgeAfterSeconds = int(thisAddon.getSetting('purgeAfterDays')) * 24 * 60 * 60
            if force:
                purgeAfterSeconds = 0
            return SimpleCache(cacheExpirySeconds).cleanCache(purgeAfterSeconds)
        else:
            return None
    except:
        return None

def showSubCategories(url):
    subCatList = getFromCache(url)
    if subCatList == None:
        jsonData = callServiceApi(url)
        subCatList = json.loads(jsonData)
        setToCache(url, subCatList)
    for s in subCatList:
        subCatName = s['name'].encode('utf8')
        addDir(subCatName, '/Category/List/%s' % s['id'], 2, 'menu_logo.png')
    xbmcplugin.endOfDirectory(thisPlugin)
        
def showShows(url):
    htmlData = ''
    latestShowsHtml = []
    cacheKey = url + ':v1'
    for i in range(int(thisAddon.getSetting('loginRetries')) + 1):
        latestShowsHtml = getFromCache(cacheKey)
        if latestShowsHtml == None or len(latestShowsHtml) == 0:
            htmlData = callServiceApi(url)
            latestShowsHtml = common.parseDOM(htmlData, "div", attrs = {'id' : 'latestShows_bodyContainer'})
            setToCache(cacheKey, latestShowsHtml)
        if len(latestShowsHtml) > 0:
            break
        else:
            loginData = login()
    if url == onlinePremierUrl:
        latestShows = common.parseDOM(latestShowsHtml[0], "div", attrs = {'class' : 'floatLeft'})
    else:
        latestShows = common.parseDOM(latestShowsHtml[0], "div", attrs = {'class' : 'showItem_preview ht_265'})
    listSubscribedFirst = True if thisAddon.getSetting('listSubscribedFirst') == 'true' else False
    italiciseUnsubscribed = True if thisAddon.getSetting('italiciseUnsubscribed') == 'true' else False
    subscribedShowIds = []
    if listSubscribedFirst or italiciseUnsubscribed: 
        # make an API call only if we're checking against subscribed shows
        subscribedShowIds = getSubscribedShowIds()
    unsubscribedShows = []
    subscribedShows = []
    for showHtml in latestShows:
        title = ''
        showTitle = []
        showUrl = []
        thumbnail = []
        if url == onlinePremierUrl:
            title = common.parseDOM(showHtml, "img", ret = 'title')
            showTitle = common.replaceHTMLCodes(title[0].encode('utf8'))
            showUrl = common.parseDOM(showHtml, "a", ret = 'href')
            thumbnail = common.parseDOM(showHtml, "img", ret = 'src')
        else:
            spanTitle = common.parseDOM(showHtml, "span", attrs = {'class' : 'showTitle'})
            title = common.parseDOM(spanTitle[0], "a")
            showTitle = common.replaceHTMLCodes(title[0].encode('utf8'))
            showUrl = common.parseDOM(spanTitle[0], "a", ret = 'href')
            thumbnail = common.parseDOM(showHtml, "img", ret = 'src')
        showUrl = showUrl[0].replace('/Show/Details/', '/Show/_ShowEpisodes/')
        showId = int(showUrl.replace('/Show/_ShowEpisodes/', ''))
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
                addDir(showTitle, showUrl, 3, thumbnail)
            else:
                # will add them later
                unsubscribedShows.append((showTitle, showUrl, 3, thumbnail))
        else:
            addDir(showTitle, showUrl, 3, thumbnail)
    # this will not be populated if we're not listing subscribed shows first
    for u in unsubscribedShows:
        addDir(u[0], u[1], u[2], u[3])
    xbmcplugin.endOfDirectory(thisPlugin)
        
def showEpisodes(url):
    headers = [('Content-type', 'application/x-www-form-urlencoded'),
        ('X-Requested-With', 'XMLHttpRequest')]
    itemsPerPage = int(thisAddon.getSetting('itemsPerPage'))
    params = { 'page' : page, 'size' : itemsPerPage }
    jsonData = callServiceApi(url, params, headers)
    episodeList = json.loads(jsonData)
    for e in episodeList['data']:
        kwargs = { 'listProperties' : { 'IsPlayable' : 'true' } }
        addDir(e['DateAiredStr'].encode('utf8'), str(e['EpisodeId']), 4, thumbnail, isFolder = False, **kwargs)
    totalEpisodes = int(episodeList['total'])
    episodeCount = page * itemsPerPage
    if totalEpisodes > episodeCount:
        addDir("Next >>",  url, 3, thumbnail, page + 1)
    xbmcplugin.endOfDirectory(thisPlugin)
        
def playEpisode(episodeId):
    quality = int(thisAddon.getSetting('quality'))
    errorCode = -1
    jsonData = ''
    episodeDetails = {}
    notificationCall = ''
    hasError = False
    for i in range(int(thisAddon.getSetting('loginRetries')) + 1):
        jsonData = callServiceApi('/Ajax/GetMedia/%s?p=%s' % (int(episodeId), quality + 1))
        episodeDetails = json.loads(jsonData)
        if type(episodeDetails) is dict and episodeDetails.has_key('errorCode') and episodeDetails['errorCode'] != 0:
            errorHeader = 'Media Error'
            errorMessage = 'Subscription is already expired or the item is not part of your subscription.'
            #if episodeDetails.has_key('errorMessage'):
            #    errorMessage = episodeDetails['errorMessage']
            notificationCall = 'Notification(%s, %s)' % (errorHeader, errorMessage)
            hasError = True
        errorCode = episodeDetails['errorCode']
        if errorCode == 0:
            break
        else:
            loginData = login()
            if type(loginData) is dict and loginData.has_key('errorCode') and loginData['errorCode'] != 0:
                errorHeader = 'Login Error'
                errorMessage = 'Could not login'
                if loginData.has_key('errorMessage'):
                    errorMessage = loginData['errorMessage']
                notificationCall = 'Notification(%s, %s)' % (errorHeader, errorMessage)
                hasError = True
    if errorCode == 0:
        from urlparse import urlparse
        url = episodeDetails['data']['Url']
        urlParsed = urlparse(url)
        url = '%s://%s%s?%s' % (urlParsed.scheme, urlParsed.netloc, urllib.quote(urlParsed.path), urlParsed.query)
        liz=xbmcgui.ListItem(name, iconImage = "DefaultVideo.png", thumbnailImage = thumbnail, path = url)
        liz.setInfo( type="Video", infoLabels = { "Title": name } )
        liz.setProperty('IsPlayable', 'true')
        return xbmcplugin.setResolvedUrl(thisPlugin, True, liz)
        # url = episodeDetails['data']['Url']
        # xbmc.Player().play(url, liz)
    else:
        if hasError:
            xbmc.executebuiltin(notificationCall)
    # else:
    #     dialog = xbmcgui.Dialog()
    #     dialog.ok("Could Not Play Item", "- This item is not part of your subscription", 
# "- Or your subscription is already expired", "- Or your email and/or password is incorrect")
    return False

        
def getSubscribedShowIds():
    return getSubscribedShows()[0]
    
def getSubscribedShows():
    showIdsKey = 'showIds:v1'
    subscribedShowsKey = 'subscribedShows:v1'
    showIds = getFromCache(showIdsKey)
    subscribedShows = getFromCache(subscribedShowsKey)
    if showIds and subscribedShows:
        return showIds, subscribedShows
    params = { 'page' : 1, 'size' : 1000 }
    headers = [('Content-type', 'application/x-www-form-urlencoded'),
        ('X-Requested-With', 'XMLHttpRequest')]
    jsonData = ''
    entitlementsData = {}
    urlUserEntitlements = "/User/_Entitlements"
    for i in range(int(thisAddon.getSetting('loginRetries')) + 1):
        jsonData = callServiceApi(urlUserEntitlements, params, headers)
        entitlementsData = json.loads(jsonData)
        if entitlementsData['total'] != 0:
            break
        else:
            loginData = login()
    if entitlementsData['total'] > 1000:
        for i in range(int(thisAddon.getSetting('loginRetries')) + 1):
            params = { 'page' : 1, 'size' : entitlementsData['total'] }
            jsonData = callServiceApi(urlUserEntitlements, params, headers)
            entitlementsData = json.loads(jsonData)
            if entitlementsData['total'] != 0:
                break
            else:
                login()
    subscribedShows = []
    showIds = []
    for e in entitlementsData['data']:
        expiry = int(e['ExpiryDate'].replace('/Date(','').replace(')/', ''))
        if expiry >= (time.time() * 1000):
            url = "/Packages/GetShows?packageId=%s" % (e['PackageId'])
            packagesData = []
            for i in range(int(thisAddon.getSetting('loginRetries')) + 1):
                jsonData = callServiceApi(url)
                packagesData = json.loads(jsonData)
                if packagesData:
                    break
                else:
                    login()
            for p in packagesData:
                if p['ShowId'] in showIds:
                    pass
                else:
                    subscribedShows.append(p)
                    showIds.append(p['ShowId'])
    if showIds and subscribedShows:
        setToCache(showIdsKey, showIds)
        setToCache(subscribedShowsKey, subscribedShows)
    return showIds, subscribedShows
    
def normalizeCategoryName(categoryName):
    return categoryName.replace('LITE', '').replace('PREMIUM', '').strip()
    
def showSubscribedCategories(url):
    subscribedShows = getSubscribedShows()[1]
    categories = []
    for s in subscribedShows:
        categoryName = normalizeCategoryName(s['MainCategory'])
        if categoryName in categories:
            pass
        else:
            categories.append(categoryName)
            addDir(categoryName, categoryName, 11, 'menu_logo.png')
    xbmcplugin.endOfDirectory(thisPlugin)
    
def showSubscribedShows(url):
    subscribedShows = getSubscribedShows()[1]
    thumbnails = {}
    showThumbnails = True if thisAddon.getSetting('showSubscribedShowsThumbnails') == 'true' else False
    isThumbnailFetched = False
    for s in subscribedShows:
        if showThumbnails:
            # let's get the thumbnails once only
            if isThumbnailFetched:
                pass
            else:
                isThumbnailFetched = True
                thumbnails = getSubscribedShowsThumbnails(s['MainCategoryId'])
                try:
                    thumbnails = getSubscribedShowsThumbnails(s['MainCategoryId'])
                except:
                    pass
        categoryName = normalizeCategoryName(s['MainCategory'])
        if categoryName == url:
            thumbnail = ''
            if showThumbnails:
                if thumbnails.has_key(s['ShowId']):
                    thumbnail = thumbnails[s['ShowId']]
                else:
                    # the show must be new and the thumbnail is probably not in cache ...
                    # ... or the first set of thumbnails might be from a LITE subscription (less shows vs PREMIUM)
                    try:
                        thumbnails = getSubscribedShowsThumbnails(s['MainCategoryId'], forceRecache = True)
                    except:
                        pass
                    if thumbnails.has_key(s['ShowId']):
                        thumbnail = thumbnails[s['ShowId']]
            showTitle = common.replaceHTMLCodes(s['Show'].encode('utf8'))
            addDir(showTitle, '/Show/_ShowEpisodes/' + str(s['ShowId']), 3, thumbnail)
    xbmcplugin.endOfDirectory(thisPlugin)

def getSubscribedShowsThumbnails(mainCategoryId, forceRecache = False):
    thumbnailKeyTemplate = 'getThumbnail:%s:v2'
    thumbnailKey = thumbnailKeyTemplate  % mainCategoryId
    tumbnailCacheExpirySeconds = int(thisAddon.getSetting('subscribedThumbnailCacheDays')) * 24 * 60 * 60
    thumbnails = {}
    if forceRecache:
        thumbnails = None
    else:
        thumbnails = getFromCache(thumbnailKey, tumbnailCacheExpirySeconds)
    if thumbnails != None:
        return thumbnails
    url = '/Category/List/%s' % mainCategoryId
    htmlData = callServiceApi(url)
    latestShowsHtml = common.parseDOM(htmlData, "div", attrs = {'id' : 'latestShows_bodyContainer'})
    latestShows = common.parseDOM(latestShowsHtml[0], "div", attrs = {'class' : 'showItem_preview ht_265'})
    thumbnails = {}
    for showHtml in latestShows:
        spanTitle = common.parseDOM(showHtml, "span", attrs = {'class' : 'showTitle'})
        showUrl = common.parseDOM(spanTitle[0], "a", ret = 'href')
        latestShowId = int(showUrl[0].rsplit('/', 1)[1])
        latestShowThumbnail = common.parseDOM(showHtml, "img", ret = 'src')
        if latestShowThumbnail and len(latestShowThumbnail) > 0:
            urlDocName = latestShowThumbnail[0][(latestShowThumbnail[0].rfind('/') + 1):]
            latestShowThumbnailEncoded = latestShowThumbnail[0].replace(urlDocName, urllib.quote(common.replaceHTMLCodes(urlDocName)))
            thumbnails[latestShowId] = latestShowThumbnailEncoded
    if thumbnails and len(thumbnails) > 0:
        setToCache(thumbnailKeyTemplate  % mainCategoryId, thumbnails, tumbnailCacheExpirySeconds)
    return thumbnails
            

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
    emailAddress = thisAddon.getSetting('emailAddress')
    password = thisAddon.getSetting('password')
    formdata = { "EmailAddress" : emailAddress, "Password": password }
    jsonData = callServiceApi("/User/_Login", formdata)
    loginData = json.loads(jsonData)
    return loginData
    
def checkAccountChange():
    emailAddress = thisAddon.getSetting('emailAddress')
    password = thisAddon.getSetting('password')
    hash = hashlib.sha1(emailAddress + password).hexdigest()
    hashFile = os.path.join(xbmc.translatePath(xbmcaddon.Addon().getAddonInfo('profile')), 'a.tmp')
    savedHash = ''
    accountChanged = False
    if os.path.exists(hashFile):
        with open(hashFile) as f:
            savedHash = f.read()
    if savedHash != hash:
        login()
        accountChanged = True
    if os.path.exists(xbmc.translatePath(xbmcaddon.Addon().getAddonInfo('profile'))):
        with open(hashFile, 'w') as f:
            f.write(hash)
    return accountChanged
    
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

def addDir(name, url, mode, thumbnail, page = 1, isFolder = True, **kwargs):
    u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)+"&page="+str(page)+"&thumbnail="+urllib.quote_plus(thumbnail)
    liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=thumbnail)
    liz.setInfo( type="Video", infoLabels={ "Title": name } )
    for k, v in kwargs.iteritems():
        if k == 'listProperties':
            for listPropertyKey, listPropertyValue in v.iteritems():
                liz.setProperty(listPropertyKey, listPropertyValue)
    return xbmcplugin.addDirectoryItem(handle=thisPlugin,url=u,listitem=liz,isFolder=isFolder)


thisPlugin = int(sys.argv[1])
userAgent = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:18.0) Gecko/20100101 Firefox/18.0'
baseUrl = 'http://tfc.tv'
cookieJar = cookielib.CookieJar()
cookieFile = ''
cookieJarType = ''
if os.path.exists(xbmc.translatePath(xbmcaddon.Addon().getAddonInfo('profile'))):
    cookieFile = os.path.join(xbmc.translatePath(xbmcaddon.Addon().getAddonInfo('profile')), 'tfctv.cookie')
    cookieJar = cookielib.LWPCookieJar(cookieFile)
    cookieJarType = 'LWPCookieJar'
if cookieJarType == 'LWPCookieJar':
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
isCacheEnabled = True if thisAddon.getSetting('isCacheEnabled') == 'true' else False
onlinePremierUrl = '/Category/List/1962'


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
    
if mode == None or url == None or len(url) < 1:
    showCategories()
elif mode == 1:
    showSubCategories(url)
elif mode == 2:
    showShows(url)
elif mode == 3:
    showEpisodes(url)
elif mode == 4:
    playEpisode(url)
elif mode == 10:
    showSubscribedCategories(url)
elif mode == 11:
    showSubscribedShows(url)

if cookieJarType == 'LWPCookieJar':
    cookieJar.save()
