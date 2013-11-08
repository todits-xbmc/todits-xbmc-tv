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
        { 'name' : 'Free TV', 'url' : '929', 'mode' : 3 },
        { 'name' : 'Subscription Information', 'url' : 'SubscriptionInformation', 'mode' : 12 }
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
        addDir(subCatName, '%s' % s['id'], 2, 'menu_logo.png')
    xbmcplugin.endOfDirectory(thisPlugin)
        
def showShows(categoryId):
    showListData = getShowListData(categoryId)
    if showListData is None:
        xbmcplugin.endOfDirectory(thisPlugin)
        return
    listSubscribedFirst = True if thisAddon.getSetting('listSubscribedFirst') == 'true' else False
    italiciseUnsubscribed = True if thisAddon.getSetting('italiciseUnsubscribed') == 'true' else False
    subscribedShowIds = []
    if listSubscribedFirst or italiciseUnsubscribed: 
        # make an API call only if we're checking against subscribed shows
        subscribedShowIds = getSubscribedShowIds()
    if listSubscribedFirst:
        unsubscribedShows = []
        # try to minimize loops
        for showId, (showName, thumbnail) in showListData.iteritems():
            if showId in subscribedShowIds:
                addDir(showName, str(showId), 3, thumbnail)
            else:
                showTitle = '[I]' + showName + '[/I]' if italiciseUnsubscribed else showName
                # well add these unsubscribed shows later
                unsubscribedShows.append((showId, showTitle, thumbnail))
        for showId, showTitle, thumbnail in unsubscribedShows:
            addDir(showTitle, str(showId), 3, thumbnail)
    else:
        for showId, (showName, thumbnail) in showListData.iteritems():
            showTitle = '[I]' + showName + '[/I]' if italiciseUnsubscribed and showId in subscribedShowIds else showName
            addDir(showTitle, str(showId), 3, thumbnail)
    xbmcplugin.endOfDirectory(thisPlugin)
    
def getShowListData(categoryId, forceRecache = False):
    url = '/Category/List/%s' % categoryId
    cacheKey = 'showListData:v2:%s' % categoryId
    showListData = None
    if forceRecache:
        showListData = None
    else:
        showListData = getFromCache(cacheKey)
    if showListData:
        return showListData
    else:
        htmlData = callServiceApi(url)
        showListData = extractShowListData(htmlData, url)
        setToCache(cacheKey, showListData)
        return showListData
        
def extractShowListData(htmlData, url):
    showListData = {}
    latestShowsHtml = common.parseDOM(htmlData, "div", attrs = {'id' : 'latestShows_bodyContainer'})
    if url == onlinePremierUrl:
        latestShows = common.parseDOM(latestShowsHtml[0], "div", attrs = {'class' : 'floatLeft'})
    else:
        latestShows = common.parseDOM(latestShowsHtml[0], "div", attrs = {'class' : 'showItem_preview ht_265'})
    for showHtml in latestShows:
        title = []
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
        showId = int(showUrl[0].replace('/Show/Details/', ''))
        urlDocName = thumbnail[0][(thumbnail[0].rfind('/') + 1):]
        thumbnail = thumbnail[0].replace(urlDocName, urllib.quote(urlDocName))
        showListData[showId] = (showTitle, thumbnail)
    return showListData
        
def showEpisodes(showId):
    url = '/Show/GetListOfEpisodes/%s' % showId
    itemsPerPage = int(thisAddon.getSetting('itemsPerPage'))
    params = { 'page' : page, 'pageSize' : itemsPerPage }
    jsonData = callServiceApi(url, params)
    episodeList = json.loads(jsonData)
    for e in episodeList['Data']:
        kwargs = { 'listProperties' : { 'IsPlayable' : 'true' } }
        if 'Synopsis' in e:
            kwargs['listInfos'] = { 'video' : { 'plotoutline' : e['Synopsis'] } } 
        addDir(e['DateAiredStr'].encode('utf8'), str(e['EpisodeId']), 4, e['ImgUrl'], isFolder = False, **kwargs)
    totalEpisodes = int(episodeList['Total'])
    episodeCount = page * itemsPerPage
    if totalEpisodes > episodeCount:
        addDir("Next >>",  showId, 3, '', page + 1)
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
    jsonData = ''
    entitlementsData = getEntitlementsData()
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
    shows = [s for s in subscribedShows if s['MainCategory'].startswith(url)]
    thumbnails = {}
    showThumbnails = True if thisAddon.getSetting('showSubscribedShowsThumbnails') == 'true' else False
    showListData = {}
    for s in shows:
        thumbnail = ''
        showId = s['ShowId']
        if showThumbnails:
            categoryId = s['MainCategoryId']
            # get the showListData only once. don't get it if it's already set
            try:
                showListData = showListData if showListData else getShowListData(categoryId, forceRecache = True)
            except:
                pass
            if showId in showListData:
                thumbnail = showListData[showId][1]
            else:
                # the show must be new and the thumbnail is probably not in cache ...
                # ... or the first set of thumbnails might be from a LITE subscription (less shows vs PREMIUM)
                try:
                    showListData = getShowListData(categoryId, forceRecache = True)
                except:
                    pass
                if showId in showListData:
                    thumbnail = showListData[showId][1]
        showTitle = common.replaceHTMLCodes(s['Show'].encode('utf8'))
        addDir(showTitle, str(showId), 3, thumbnail)
    xbmcplugin.endOfDirectory(thisPlugin)
    
def getEntitlementsData():
    entitlementsData = {}
    params = { 'page' : 1, 'size' : 1000 }
    headers = [('Content-type', 'application/x-www-form-urlencoded'),
        ('X-Requested-With', 'XMLHttpRequest')]
    jsonData = ''
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
    return entitlementsData

def showSubcriptionInformation():
    xbmc.executebuiltin("ActivateWindow(%d)" % (10147, ))
    win = xbmcgui.Window(10147)
    entitlementsData = getEntitlementsData()
    message = ''
    for entitlement in entitlementsData['data']:
        expiryUnixTime = (int(entitlement['ExpiryDate'].replace('/Date(','').replace(')/', ''))) / 1000
        entitlementEntry = 'Package Name: %s\n    EID: %s\n    Expiry Date: %s\n\n' % (entitlement['Content'], entitlement['EntitlementId'], time.strftime('%B %d, %Y %X %Z', time.localtime(expiryUnixTime)))
        message += entitlementEntry
    win.getControl(1).setLabel('TFC.tv Subscription Information')
    win.getControl(5).setText(message)

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
        if k == 'listInfos':
            for listInfoKey, listInfoValue in v.iteritems():
                liz.setInfo(listInfoKey, listInfoValue)
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
elif mode == 12:
    showSubcriptionInformation()

if cookieJarType == 'LWPCookieJar':
    cookieJar.save()
