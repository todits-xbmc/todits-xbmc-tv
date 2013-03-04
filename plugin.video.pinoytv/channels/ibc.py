import xbmc, xbmcaddon, os.path

userAgent = 'Mozilla/5.0 (X11; Linux x86_64; rv:17.0) Gecko/20100101 Firefox/17.0'
addonPath = xbmc.translatePath(xbmcaddon.Addon().getAddonInfo('path'))

def getMenu(menuId, userAgent):
    menu = {
        'main' : [{
                    'id' : 'pbalive',
                    'name' : 'PBA Live',
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
                }]
    }
    return (__name__, menu[menuId])
