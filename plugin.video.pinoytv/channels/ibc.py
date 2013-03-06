import xbmc, xbmcaddon, os.path

userAgent = 'Mozilla/5.0 (X11; Linux x86_64; rv:17.0) Gecko/20100101 Firefox/17.0'
addonPath = xbmc.translatePath(xbmcaddon.Addon().getAddonInfo('path'))

def getMenu(menuId, userAgent):
    menu = {
        'main' : [{
                    'id' : 'pbalive',
                    'name' : 'PBA Live',
                    'url' : 'pbalive',
                    'icon' : os.path.join(addonPath, 'pba_logo.jpg'),
                    'isFolder' : True
                }],
        'pbalive' : [{
                        'id' : 'livestream1',
                        'name' : 'Play Stream 1',
                        'url' : 'rtmp://85.12.5.5/vl/_definst_',
                        'icon' : os.path.join(addonPath, 'pba_logo.jpg'),
                        'isFolder' : False,
                        'kwargs' : {
                                        'listProperty' : {
                                                            'app' : 'vl/_definst_', 
                                                            'PlayPath' : 'sportspbalive', 
                                                            'SWFPlayer' : 'http://www.veemi.com/player/player-licensed.swf', 
                                                            'PageURL' : 'http://www.veemi.com', 
                                                            'TcUrl' : 'rtmp://85.12.5.5/vl/_definst_'
                                                        }
                                    }
                    },
                    {
                        'id' : 'livestream2',
                        'name' : 'Play Stream 2',
                        'url' : 'livestream2',
                        'icon' : os.path.join(addonPath, 'pba_logo.jpg'),
                        'isFolder' : True,
                        'kwargs' : { 'play' : True }
                    }
                ]
    }
    return (__name__, menu[menuId])
    
def play(id, userAgent):
    if id == 'livestream2':
        import xbmc, xbmcgui
        channelId = '11283017'
        amfUrl = 'http://cdngw.ustream.tv/Viewer/getStream/1/%s.amf' % channelId
        videoInfo = getAmfInfo(amfUrl, userAgent, 'Viewer', 'getStream')
        if videoInfo and videoInfo['status'] == 'online':
            videoUrl = videoInfo['liveHttpUrl']
            liz=xbmcgui.ListItem('PBA Live', iconImage = "DefaultVideo.png")
            liz.setInfo( type="Video", infoLabels = { "Title": 'PBA Live' } )
            xbmc.Player().play(videoUrl, liz)
        else:
            dialog = xbmcgui.Dialog()
            dialog.ok('Offline', 'Stream is offline')
            
        
        
def getAmfInfo(url, userAgent, serviceName, methodName):
    import pyamf
    from pyamf.remoting.client import RemotingService
    from pyamf import remoting, amf3, util
    client = RemotingService(url, user_agent = userAgent)
    service = client.getService(serviceName)
    methodCall = getattr(service, methodName)
    return service.methodCall()
