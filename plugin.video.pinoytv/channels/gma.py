import xbmc, xbmcaddon, os.path

userAgent = 'Mozilla/5.0 (X11; Linux x86_64; rv:17.0) Gecko/20100101 Firefox/17.0'
addonPath = xbmc.translatePath(xbmcaddon.Addon().getAddonInfo('path'))
resourcesPath = os.path.join(addonPath, 'resources')
imagesPath = os.path.join(resourcesPath, 'images')

def getMenu(menuId, userAgent):
    menu = {
        'main' : [{
                    'id' : 'gma',
                    'name' : 'GMA',
                    'url' : 'gma',
                    'icon' : os.path.join(imagesPath, 'gma_logo.jpg'),
                    'isFolder' : True
                }],
        'gma' : [{
                'id' : 'live',
                'name' : 'Live',
                'url' : 'rtmp://fms.ilive.to:1935/app/_definst_/dfo8ebwnnh37rfv',
                'icon' : os.path.join(imagesPath, 'gma_logo.jpg'),
                'isFolder' : False,
                'kwargs' : {'listProperty' : {'SWFPlayer' : 'http://static.ilive.to/jwplayer/player.swf'}}
            }]
    }
    return (__name__, menu[menuId])
