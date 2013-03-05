import xbmc, xbmcaddon, os.path

userAgent = 'Mozilla/5.0 (X11; Linux x86_64; rv:17.0) Gecko/20100101 Firefox/17.0'
addonPath = xbmc.translatePath(xbmcaddon.Addon().getAddonInfo('path'))
baseUrl = 'http://uaapsports.studio23.tv'
def getMenu(menuId, userAgent):
    menu = {
        'main' : [{
                    'id' : 'uaaplive',
                    'name' : 'UAAP Live',
                    'url' : 'uaaplive',
                    'icon' : 'http://uaapsports.studio23.tv/images/uaap_uaap-logo.png',
                    'isFolder' : True,
                    'kwargs' : {
                                    'play' : True
                                }
                }]
    }
    return (__name__, menu[menuId])

def play(id, userAgent):
    import CommonFunctions, urlparse, xbmcgui, re
    common = CommonFunctions
    common.plugin = xbmcaddon.Addon().getAddonInfo('name')
    htmlData = openUrl('/livestream.html')
    flashVars = common.parseDOM(htmlData, "embed", attrs = {'base' : 'http://admin.brightcove.com'}, ret = 'flashVars')
    vars = urlparse.parse_qs(flashVars[0])
    from lib.brightcove import BrightCove
    brightCoveServiceName = 'com.brightcove.player.runtime.PlayerMediaFacade'
    brightCoveserviceUrl = 'http://c.brightcove.com/services/messagebroker/amf'
    brightCove = BrightCove('1f101e877a92705f79de79e69685bd57f931cede', vars['playerKey'][0], serviceUrl = brightCoveserviceUrl, serviceName = brightCoveServiceName)
    publisherId = 1878978674001
    brightCoveResponse = brightCove.findMediaById(int(vars['playerID'][0]), int(vars['@videoPlayer'][0]), publisherId, userAgent)
    pattern = re.compile(r'/live/&(.+)')
    m = pattern.search(brightCoveResponse['FLVFullLengthURL'])
    playPath = m.group(1)
    liz=xbmcgui.ListItem(brightCoveResponse['shortDescription'], iconImage = "DefaultVideo.png")
    liz.setInfo( type="Video", infoLabels = { "Title": brightCoveResponse['shortDescription'] } )
    # liz.setProperty('IsLive', '1')
    # liz.setProperty('App', 'live')
    # liz.setProperty('PlayPath', playPath)
    # liz.setProperty('SwfUrl', 'http://admin.brightcove.com/viewer/us20130222.1010/federatedVideoUI/BrightcovePlayer.swf?uid=1362467553994')
    # liz.setProperty('TcUrl', brightCoveResponse['FLVFullLengthURL'])
    # liz.setProperty('PageUrl', 'http://uaapsports.studio23.tv/livestream.html')
    # liz.setProperty('FlashVer', 'WIN 11,1,102,63')
    # xbmc.Player().play(brightCoveResponse['FLVFullLengthURL'], liz)
    videoUrl = brightCoveResponse['FLVFullLengthURL'] + ' live=1 app=live playPath=' + playPath
    # + ' tcUrl=' + brightCoveResponse['FLVFullLengthURL']
    xbmc.Player().play(videoUrl, liz)
    
def openUrl(path, params = {}, headers = []):
    import urllib, urllib2
    # opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookieJar))
    opener = urllib2.build_opener()
    headers.append(('User-Agent', userAgent))
    opener.addheaders = headers
    if params:
        data_encoded = urllib.urlencode(params)
        response = opener.open(baseUrl + path, data_encoded)
    else:
        response = opener.open(baseUrl + path)
    return response.read()