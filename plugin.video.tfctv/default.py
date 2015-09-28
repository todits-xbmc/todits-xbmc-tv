import sys, urllib, urllib2, json, cookielib, time, os.path, hashlib
import xbmc, xbmcgui, xbmcplugin, xbmcaddon
from operator import itemgetter

import CommonFunctions
common = CommonFunctions
thisAddon = xbmcaddon.Addon()
common.plugin = thisAddon.getAddonInfo('name')
baseUrl = 'http://tfc.tv'

# common.dbg = True # Default
# common.dbglevel = 3 # Default

def showCategories():
    checkAccountChange()
    categories = [
        # { 'name' : 'Subscribed Shows', 'url' : 'SubscribedShows', 'mode' : 10 }, #hide subscribed shows while we're having issues with the tfc.tv changes
        { 'name' : 'Shows', 'url' : '/Category/Shows', 'mode' : 1 },
        { 'name' : 'News', 'url' : '/Category/News', 'mode' : 1 },
        { 'name' : 'Movies', 'url' : '/Category/Movies', 'mode' : 1 },
        # { 'name' : 'Live', 'url' : '/Category/Live', 'mode' : 1 },
        # { 'name' : 'Free TV', 'url' : '929', 'mode' : 3 }, # hide free tv while we're having issues with the tfc.tv changes
        # { 'name' : 'Subscription Information', 'url' : 'SubscriptionInformation', 'mode' : 12 } #hide subscription information while we're having issues with the tfc.tv changes
    ]
    for c in categories:
        addDir(c['name'], c['url'], c['mode'], 'icon.png')
    xbmcplugin.endOfDirectory(thisPlugin)

def extractSubCategory(htmlContents):
    sectionHeaders = common.parseDOM(htmlContents, "div", attrs = {'class' : 'sec_header'})
    subCategories = []
    for s in sectionHeaders:
        titleRaw = common.parseDOM(s, "h2", attrs = {'class' : 'section_title clearfix'})
        title = common.replaceHTMLCodes(titleRaw[0]) if len(titleRaw) > 0 else ''
        urlRaw = common.parseDOM(s, "a", ret = 'href')
        url = urlRaw[0] if len(urlRaw) > 0 else ''
        if title and url:
            subCategories.append((title, url))
    return subCategories
        
def showSubCategories(url):
    htmlContents = callServiceApi(url)
    subCatList = extractSubCategory(htmlContents)
    for s in subCatList:
        addDir(s[0].encode('utf8'), '%s' % s[1], 2, 'menu_logo.png')
    xbmcplugin.endOfDirectory(thisPlugin)
        
def showShows(categoryId):
    showListData = getShowListData(categoryId)
    if showListData is None:
        xbmcplugin.endOfDirectory(thisPlugin)
        return
    listSubscribedFirst = True if thisAddon.getSetting('listSubscribedFirst') == 'true' else False
    italiciseUnsubscribed = True if thisAddon.getSetting('italiciseUnsubscribed') == 'true' else False
    listSubscribedFirst = False
    italiciseUnsubscribed = False
    subscribedShowIds = []
    if listSubscribedFirst or italiciseUnsubscribed: 
        # make an API call only if we're checking against subscribed shows
        subscribedShowIds = getSubscribedShowIds()
    if listSubscribedFirst:
        unsubscribedShows = []
        # try to minimize loops
        sortedShowInfos = []
        sortedUnsubscibed = []
        for showId, (showName, thumbnail) in showListData.iteritems():
            if showId in subscribedShowIds:
                sortedShowInfos.append((showName.lower(), showName, str(showId), 3, thumbnail))
                # addDir(showName, str(showId), 3, thumbnail)
            else:
                showTitle = '[I]' + showName + '[/I]' if italiciseUnsubscribed else showName
                # we'll add these unsubscribed shows later
                # unsubscribedShows.append((showId, showTitle, thumbnail))
                sortedUnsubscibed.append((showName.lower(), showTitle, showId, 3, thumbnail))
        sortedShowInfos = sorted(sortedShowInfos, key = itemgetter(0))
        sortedUnsubscibed = sorted(sortedUnsubscibed, key = itemgetter(0))
        for info in sortedShowInfos:
            addDir(info[1], info[2], info[3], info[4])
        # for showId, showTitle, thumbnail in unsubscribedShows:
        for info in sortedUnsubscibed:
            addDir(info[1], info[2], info[3], info[4])
    else:
        sortedShowInfos = []
        for showId, (showName, thumbnail) in showListData.iteritems():
            showTitle = '[I]' + showName + '[/I]' if italiciseUnsubscribed and showId in subscribedShowIds else showName
            sortedShowInfos.append((showName.lower(), showTitle, str(showId), 3, thumbnail))
            # addDir(showTitle, str(showId), 3, thumbnail)
        sortedShowInfos = sorted(sortedShowInfos, key = itemgetter(0))
        for info in sortedShowInfos:
            addDir(info[1], info[2], info[3], info[4])
    xbmcplugin.endOfDirectory(thisPlugin)
    
def getShowListData(categoryId):
    url = categoryId
    if not url.startswith('/Category/List/'):
        url = '/Category/List/%s' % categoryId
    htmlData = callServiceApi(url)
    showListData = extractShowListData(htmlData, url)
    return showListData
        
def extractShowListData(htmlData, url):
    showListData = {}
    showsHtml = common.parseDOM(htmlData, "div", attrs = {'class' : 'movie col-md-2 col-sm-3 col-xs-6 no_title'})
    for s in showsHtml:
        thumbnail = common.parseDOM(s, "img", ret = 'src')
        titleElement = common.parseDOM(s, "h2")
        showUrl = common.parseDOM(titleElement, "a", ret = 'href')
        title = common.parseDOM(titleElement, "a")
        urlDocName = thumbnail[0][(thumbnail[0].rfind('/') + 1):]
        thumbnail = thumbnail[0].replace(urlDocName, urllib.quote(urlDocName))
        showListData[int(showUrl[0].replace('/Show/Details/', '').split('/')[0])] = (common.replaceHTMLCodes(title[0].encode('utf8')), thumbnail)
    return showListData
        
def showEpisodes(showId):
    itemsPerPage = int(thisAddon.getSetting('itemsPerPage'))
    url = '/Show/GetMoreEpisodes/%s/?page=%s&pageSize=%s' % (showId, page, itemsPerPage)
    episodes_html = callServiceApi(url)
    episode_data = common.parseDOM(episodes_html, "div")
    episodes_returned = 0
    for e in episode_data:
        episodes_returned = episodes_returned + 1
        episode_hrefs = common.parseDOM(e, "a", ret = 'href') # there will be at least 2 hrefs but they are all duplicates
        episode_id = episode_hrefs[0].replace('/Episode/Details/', '').split('|')[0]
        image_url = common.parseDOM(e, "img", ret = 'src')[0]
        title_div = common.parseDOM(e, "div", attrs = { 'class' : 'e-title' })[0]
        title_tag = common.parseDOM(title_div, "a")[0]
        kwargs = { 'listProperties' : { 'IsPlayable' : 'true' } }
        # if 'Synopsis' in e:
            # kwargs['listInfos'] = { 'video' : { 'plot' : e['Synopsis'] } } 
        addDir(title_tag.split('-')[-1].strip().encode('utf8'), episode_id, 4, image_url, isFolder = False, **kwargs)
    if episodes_returned == itemsPerPage:
        addDir("Next >>",  showId, 3, '', page + 1)
    xbmcplugin.endOfDirectory(thisPlugin)
        
def playEpisode(episode):
    errorCode = -1
    jsonData = ''
    episodeDetails = {}
    notificationCall = ''
    hasError = False
    headers = [('X-Requested-With', 'XMLHttpRequest')]
    for i in range(int(thisAddon.getSetting('loginRetries')) + 1):
        episodeDetails = get_media_info(episode)
        if episodeDetails and episodeDetails.has_key('errorCode') and episodeDetails['errorCode'] == 0:
            break
        else:
            login()
    if episodeDetails and episodeDetails.has_key('errorCode') and episodeDetails['errorCode'] == 0:
        url = episodeDetails['data']['Url']
        liz=xbmcgui.ListItem(name, iconImage = "DefaultVideo.png", thumbnailImage = thumbnail, path = url)
        liz.setInfo( type="Video", infoLabels = { "Title": name } )
        liz.setProperty('IsPlayable', 'true')
        return xbmcplugin.setResolvedUrl(thisPlugin, True, liz)
    else:
        if (not episodeDetails) or (episodeDetails and episodeDetails.has_key('errorCode') and episodeDetails['errorCode'] != 0):
            xbmc.executebuiltin('Notification(%s, %s)' % ('Media Error', 'Subscription is already expired or the item is not part of your subscription.'))
    return False
    
def get_media_info(episode):
    import re
    html = callServiceApi('/Episode/Details/%s' % episode)
    body = common.parseDOM(html, "body")
    scripts = common.parseDOM(body, "script")
    episode_id = episode.split('/')[0]
    media_info = None
    api_bare_path = '/Ajax/GetMedia/%s' % (episode_id)
    pattern = re.compile('{0}(\?p=[0-9])?'.format(api_bare_path), re.IGNORECASE)
    for script in scripts:
        line = script.strip();
        match = pattern.search(line)
        if match:
            response = callServiceApi(match.group(0), headers = [('X-Requested-With', 'XMLHttpRequest')])
            media_info = json.loads(response)
            break
    return media_info

def getSubscribedShowIds():
    return getSubscribedShows()[0]
    
def getSubscribedShows():
    jsonData = ''
    entitlementsData = getEntitlementsData()
    subscribedShows = []
    showIds = []
    for e in entitlementsData['data']:
        expiry = int(e['ExpiryDate'].replace('/Date(','').replace(')/', ''))
        if expiry >= (time.time() * 1000):
            if e['PackageId']:
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
            else:
                if e['CategoryId'] and e['CategoryId'] not in showIds:
                    e['MainCategory'] = u'A la carte'
                    e['ShowId'] = e['CategoryId']
                    e['Show'] = e['Content']
                    subscribedShows.append(e)
                    showIds.append(e['CategoryId'])
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
    showThumbnails = False # currently broken, disabled for now
    showListData = {}
    for s in shows:
        thumbnail = ''
        showId = s['ShowId']
        if showThumbnails and 'MainCategoryId' in s:
            categoryId = s['MainCategoryId']
            # get the showListData only once. don't get it if it's already set
            try:
                showListData = showListData if showListData else getShowListData(categoryId)
            except:
                pass
            if showId in showListData:
                thumbnail = showListData[showId][1]
            else:
                # the show must be new and the thumbnail is probably not in cache ...
                # ... or the first set of thumbnails might be from a LITE subscription (less shows vs PREMIUM)
                try:
                    showListData = getShowListData(categoryId)
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
    entitlementsData = getEntitlementsData()
    message = ''
    for entitlement in entitlementsData['data']:
        expiryUnixTime = (int(entitlement['ExpiryDate'].replace('/Date(','').replace(')/', ''))) / 1000
        entitlementEntry = 'Package Name: %s\n    EID: %s\n    Expiry Date: %s\n\n' % (entitlement['Content'], entitlement['EntitlementId'], time.strftime('%B %d, %Y %X %Z', time.localtime(expiryUnixTime)))
        message += entitlementEntry
    showMessage(message, xbmcaddon.Addon().getLocalizedString(56001))

def callServiceApi(path, params = {}, headers = [], base_url = baseUrl):
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookieJar))
    headers.append(('User-Agent', userAgent))
    opener.addheaders = headers
    if params:
        data_encoded = urllib.urlencode(params)
        response = opener.open(base_url + path, data_encoded)
    else:
        response = opener.open(base_url + path)
    return response.read()

def login():
    cookieJar.clear()
    login_page = callServiceApi("/User/Login")
    form_login = common.parseDOM(login_page, "form", attrs = {'id' : 'form_login'})
    request_verification_token = common.parseDOM(form_login[0], "input", attrs = {'name' : '__RequestVerificationToken'}, ret = 'value')
    emailAddress = thisAddon.getSetting('emailAddress')
    password = thisAddon.getSetting('password')
    formdata = { "login_email" : emailAddress, "login_pass": password, '__RequestVerificationToken' : request_verification_token[0] }
    callServiceApi("/User/_Login", formdata, headers = [('Referer', 'http://tfc.tv/User/Login')], base_url = 'https://tfc.tv')
    # loginData = json.loads(jsonData)
    # if (not loginData) or (loginData and loginData.has_key('errorCode') and loginData['errorCode'] != 0):
        # xbmc.executebuiltin('Notification(%s, %s)' % ('Login Error', loginData['errorMessage'] if loginData.has_key('errorMessage') else 'Could not login'))
    # return loginData
    
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

def addDir(name, url, mode, thumbnail, page = 0, isFolder = True, **kwargs):
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

def showMessage(message, title = xbmcaddon.Addon().getLocalizedString(50107)):
    if not message:
        return
    xbmc.executebuiltin("ActivateWindow(%d)" % (10147, ))
    win = xbmcgui.Window(10147)
    xbmc.sleep(100)
    win.getControl(1).setLabel(title)
    win.getControl(5).setText(message)

thisPlugin = int(sys.argv[1])
userAgent = 'Mozilla/5.0(iPad; U; CPU OS 4_3 like Mac OS X; en-us) AppleWebKit/533.17.9 (KHTML, like Gecko) Version/5.0.2 Mobile/8F191 Safari/6533.18.5'
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
page=0
thumbnail = ''
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

if thisAddon.getSetting('announcement') != thisAddon.getAddonInfo('version'):
    messages = {
        '0.0.38': 'Your TFC.tv plugin has been updated.\n\nTFC.tv has undergone a lot of changes and the plugin needs to be updated to adjust to those changes.\n\nIf you encounter anything that you think is a bug, please report it to the TFC.tv XBMC Forum thread (http://forum.xbmc.org/showthread.php?tid=155870) or to the plugin website (https://code.google.com/p/todits-xbmc/).'
        }
    if thisAddon.getAddonInfo('version') in messages:
        showMessage(messages[thisAddon.getAddonInfo('version')], xbmcaddon.Addon().getLocalizedString(50106))
        xbmcaddon.Addon().setSetting('announcement', thisAddon.getAddonInfo('version'))
