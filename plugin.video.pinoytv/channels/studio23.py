import xbmc, xbmcaddon, os.path

userAgent = 'Mozilla/5.0 (X11; Linux x86_64; rv:17.0) Gecko/20100101 Firefox/17.0'
addonPath = xbmc.translatePath(xbmcaddon.Addon().getAddonInfo('path'))
resourcesPath = os.path.join(addonPath, 'resources')
imagesPath = os.path.join(resourcesPath, 'images')
baseUrl = 'http://uaapsports.studio23.tv'
def getMenu(menuId, userAgent):
    menu = {
        'main' : [{
                    'id' : 'uaaplive',
                    'name' : 'UAAP Live',
                    'url' : 'uaaplive',
                    'icon' : os.path.join(imagesPath, 'uaap-logo.png'),
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
    vars = None
    vars = urlparse.parse_qs(flashVars[0])
    from lib.brightcove import BrightCove
    playerKey = ''
    playerId = 0
    videoPlayer = 0
    if vars:
        playerKey = vars['playerKey'][0]
        playerId = int(vars['playerID'][0])
        videoPlayer = int(vars['@videoPlayer'][0])
    else:
        # I hope these are fixed values.
        playerKey = 'AQ~~,AAABtXvbPVE~,ZfNKKkFP3R-Khxw89mTKD3dSRwdPk_kt'
        playerId = 2023948803001
        videoPlayer = 2147444863001
    brightCoveServiceName = 'com.brightcove.player.runtime.PlayerMediaFacade'
    brightCoveserviceUrl = 'http://c.brightcove.com/services/messagebroker/amf'
    brightCove = BrightCove('1f101e877a92705f79de79e69685bd57f931cede', playerKey, serviceUrl = brightCoveserviceUrl, serviceName = brightCoveServiceName)
    publisherId = 1878978674001
    brightCoveResponse = brightCove.findMediaById(playerId, videoPlayer, publisherId, userAgent)
    pattern = re.compile(r'/live/&(.+)')
    m = pattern.search(brightCoveResponse['FLVFullLengthURL'])
    playPath = m.group(1)
    liz=xbmcgui.ListItem(brightCoveResponse['shortDescription'], iconImage = "DefaultVideo.png")
    liz.setInfo( type="Video", infoLabels = { "Title": brightCoveResponse['shortDescription'] } )
    videoUrl = brightCoveResponse['FLVFullLengthURL'] + ' live=1 app=live playPath=' + playPath
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