import xbmc, xbmcaddon, os.path

userAgent = 'Mozilla/5.0 (X11; Linux x86_64; rv:17.0) Gecko/20100101 Firefox/17.0'
addonPath = xbmc.translatePath(xbmcaddon.Addon().getAddonInfo('path'))
resourcesPath = os.path.join(addonPath, 'resources')
imagesPath = os.path.join(resourcesPath, 'images')

def getMenu(menuId, userAgent):
    menu = {
        'main' : [{
                    'id' : 'pbalive',
                    'name' : 'PBA Live',
                    'url' : 'pbalive',
                    'icon' : os.path.join(imagesPath, 'pba_logo.jpg'),
                    'isFolder' : True
                },
                {
                    'id' : 'ncaalive',
                    'name' : 'NCAA Live',
                    'url' : 'http://edge.pldt.swiftserve.com/live/mediascape/amlst:aksyon/playlist.m3u8',
                    'icon' : 'http://season89.ncaa.org.ph/wp-content/uploads/2013/02/logo1-1.png',
                    'isFolder' : False,
                    'kwargs' : { 'play' : True }
                }
                # ,
                # {
                    # 'id' : 'btv',
                    # 'name' : 'BTV Live',
                    # 'url' : 'http://omni.live-s.cdn.bitgravity.com/cdn-live/_definst_/omni/live/balltv_multirate.smil/Manifest',
                    # 'icon' : 'http://season89.ncaa.org.ph/wp-content/uploads/2013/02/logo1-1.png',
                    # 'isFolder' : False,
                    # 'kwargs' : { 'play' : True }
                # }
                ],
        'pbalive' : [
                    {
                        'id' : 'pbalivestream1',
                        'name' : 'Play Stream 1',
                        'url' : 'http://stream3.news5.ph:1935/live/aksyon.stream/playlist.m3u8',
                        'icon' : os.path.join(imagesPath, 'pba_logo.jpg'),
                        'isFolder' : False,
                        'kwargs' : { 'play' : True }
                    },
                    {
                        'id' : 'pbalivestream2',
                        'name' : 'Play Stream 2',
                        'url' : 'livestream2',
                        'icon' : os.path.join(imagesPath, 'pba_logo.jpg'),
                        'isFolder' : True,
                        'kwargs' : { 'play' : True }
                    }
                    # ,
                    # {
                        # 'id' : 'pbalivestream3',
                        # 'name' : 'Play Stream 3',
                        # 'url' : 'rtmp://85.12.5.5/vl/_definst_',
                        # 'icon' : os.path.join(imagesPath, 'pba_logo.jpg'),
                        # 'isFolder' : False,
                        # 'kwargs' : {
                                        # 'listProperty' : {
                                                            # 'app' : 'vl/_definst_', 
                                                            # 'PlayPath' : 'sportspbalive', 
                                                            # 'SWFPlayer' : 'http://www.veemi.com/player/player-licensed.swf', 
                                                            # 'PageURL' : 'http://www.veemi.com', 
                                                            # 'TcUrl' : 'rtmp://85.12.5.5/vl/_definst_'
                                                        # }
                                    # }
                    # },
                    # {
                        # 'id' : 'pbalivestream4',
                        # 'name' : 'Play Stream 3',
                        # 'url' : 'http://edge.pldt.swiftserve.com/live/mediascape/amlst:aksyon/playlist.m3u8',
                        # 'icon' : os.path.join(imagesPath, 'pba_logo.jpg'),
                        # 'isFolder' : False,
                        # 'kwargs' : { 'play' : True }
                    # },
                    # {
                        # 'id' : 'pbalivestream5',
                        # 'name' : 'Play Stream 4',
                        # 'url' : 'http://edge.pldt.swiftserve.com/live/mediascape/amlst:tv5/playlist.m3u8',
                        # 'icon' : os.path.join(imagesPath, 'pba_logo.jpg'),
                        # 'isFolder' : False,
                        # 'kwargs' : { 'play' : True }
                    # }
                ]
                
    }
    return (__name__, menu[menuId])
    
def play(id, userAgent):
    if id == 'pbalivestream2':
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
