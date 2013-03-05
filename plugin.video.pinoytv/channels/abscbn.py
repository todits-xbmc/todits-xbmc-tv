import xbmc, xbmcaddon, os.path
userAgent = 'Mozilla/5.0 (X11; Linux x86_64; rv:17.0) Gecko/20100101 Firefox/17.0'
brightCoveserviceUrl = 'http://c.brightcove.com/services/messagebroker/amf'
brightCoveServiceName = 'com.brightcove.experience.ExperienceRuntimeFacade'
addonPath = xbmc.translatePath(xbmcaddon.Addon().getAddonInfo('path'))

def getMenu(menuId, userAgent = userAgent):
    
    if(menuId == 'tvpatrollive'):
        return (__name__, getTvPatrolLiveMenu(userAgent))
    
    if(menuId == 'tvpatrolreplay'):
        return (__name__, getTvPatrolReplayMenu(userAgent))
    
    if(menuId == 'bandilareplay'):
        return (__name__, getBandilaReplayMenu(userAgent))
    
    menu = {
        'main' :[
                    {
                        'id' : 'abscbn',
                        'name' : 'ABS-CBN',
                        'url' : 'abscbn',
                        'icon' : os.path.join(addonPath, 'abscbn_logo.jpg'),
                        'isFolder' : True
                    }
                ],
        'abscbn' : [
                        {
                            'id' : 'tvpatrol',
                            'name' : 'TV Patrol',
                            'url' : 'tvpatrol',
                            'icon' : os.path.join(addonPath, 'tvpatrol_logo.jpg'),
                            'isFolder' : True
                        },
                        {
                            'id' : 'bandila',
                            'name' : 'Bandila',
                            'url' : 'bandila',
                            'icon' : os.path.join(addonPath, 'bandila_logo.jpg'),
                            'isFolder' : True
                        },
                        {
                            'id' : 'live',
                            'name' : 'Live',
                            'url' : 'rtmp://fms.ilive.to:1935/app/_definst_/xxooiinjva78v94',
                            'icon' : os.path.join(addonPath, 'abscbn_logo.jpg'),
                            'isFolder' : False,
                            'kwargs' : { 'listProperty' : { 'SWFPlayer' : 'http://static.ilive.to/jwplayer/player.swf' } }
                        }
                    ],
        'tvpatrol' : [
                        {
                            'id' : 'tvpatrollive',
                            'name' : 'Live',
                            'url' : 'tvpatrollive',
                            'icon' : os.path.join(addonPath, 'tvpatrol_logo.jpg'),
                            'isFolder' : True
                        },
                        {
                            'id' : 'tvpatrolreplay',
                            'name' : 'Replay',
                            'url' : 'tvpatrolreplay',
                            'icon' : os.path.join(addonPath, 'tvpatrol_logo.jpg'),
                            'isFolder' : True
                        }
                    ],
        'bandila' : [
                        {
                            'id' : 'bandilareplay',
                            'name' : 'Replay',
                            'url' : 'bandilareplay',
                            'icon' : os.path.join(addonPath, 'bandila_logo.jpg'),
                            'isFolder' : True
                        }
                    ]
    }
    
    return (__name__, menu[menuId])
    
def getTvPatrolLiveMenu(userAgent = userAgent):
    from lib.brightcove import BrightCove
    serviceKey = 'aa3634a3b4371a1c2f780f830dc2fd1ef4bbb111'
    playerKey = 'AQ~~,AAABtXvbPVE~,ZfNKKkFP3R-R8qlcWfs20DL-8Bvb6UcW'
    playerId = 1905932797001
    brightCove = BrightCove(serviceKey, playerKey, serviceUrl = brightCoveserviceUrl, serviceName = brightCoveServiceName)
    brightCoveResponse = brightCove.getBrightCoveData(playerId, userAgent)
    videoData = brightCoveResponse['playlistCombo']['lineupListDTO']['playlistDTOs'][0]['videoDTOs']
    return getLiveMenu(videoData, r'/live/&(LS_TVPatrol.+)')
    
def getTvPatrolReplayMenu(userAgent = userAgent):
    from lib.brightcove import BrightCove
    serviceKey = 'f7d4096475cca62e0afb88633662b4df1f429b98'
    playerKey = 'AQ~~,AAABtXvbPVE~,ZfNKKkFP3R8lv_FZU4AZv5yZg6d3YSFW'
    playerId = 1933244636001
    brightCove = BrightCove(serviceKey, playerKey, serviceUrl = brightCoveserviceUrl, serviceName = brightCoveServiceName)
    brightCoveResponse = brightCove.getBrightCoveData(playerId, userAgent)
    videoData = brightCoveResponse['playlistTabs']['lineupListDTO']['playlistDTOs'][0]['videoDTOs']
    return getOndemandMenu(videoData, r'/ondemand/&(mp4:.+\.mp4)\?')
    
def getBandilaReplayMenu(userAgent = userAgent):
    from lib.brightcove import BrightCove
    serviceKey = '1e901d1b97bc4590fa2d3924a8ec642d684afca4'
    playerKey = 'AQ~~,AAABtXvbPVE~,ZfNKKkFP3R_F56e3g2DVHn4JP7JQvZsz'
    playerId = 1927018689001
    brightCove = BrightCove(serviceKey, playerKey, serviceUrl = brightCoveserviceUrl, serviceName = brightCoveServiceName)
    brightCoveResponse = brightCove.getBrightCoveData(playerId, userAgent)
    videoData = brightCoveResponse['videoList']['mediaCollectionDTO']['videoDTOs']
    return getOndemandMenu(videoData, r'/ondemand/&(mp4:.+\.mp4)\?')
    
def getOndemandMenu(videoData, playPathPattern):
    import re
    menu = []
    for video in videoData:
        streamUrl = video['FLVFullLengthURL']
        pattern = re.compile(playPathPattern)
        m = pattern.search(streamUrl)
        playPath = m.group(1)
        streamUrl = streamUrl.replace('/ondemand/&mp4', '/ondemand/mp4')
        menuItem = {
                        'id' : video['displayName'],
                        'name' : video['displayName'],
                        'url' : streamUrl,
                        'icon' : video['thumbnailURL'],
                        'isFolder' : False,
                        'kwargs' : { 'listProperty' : { 'app' : 'ondemand', 'PlayPath' : playPath } }
                    }
        menu.append(menuItem)
    return menu
    
def getLiveMenu(videoData, playPathPattern):
    import re
    menu = []
    for video in videoData:
        print video
        swfUrl = 'http://admin.brightcove.com/viewer/us20130222.1010/federatedVideoUI/BrightcovePlayer.swf?uid=1362392439318'
        if video['FLVFullLengthStreamed']:
            print video['displayName'], playPathPattern, video['FLVFullLengthURL']
            pattern = re.compile(playPathPattern)
            m = pattern.search(video['FLVFullLengthURL'])
            playPath = m.group(1)
            # kwargs = { 'listProperty' : { 'IsLive' : '1', 'app' : 'live', 'PlayPath' : playPath, 'SwfUrl' : swfUrl } }
            videoUrl = video['FLVFullLengthURL'] + ' live=1 app=live playPath=' + playPath
            kwargs = {}
        else:
            kwargs = { 'listProperty' : { 'IsLive' : '1', 'SwfUrl' : swfUrl} }
            videoUrl = video['FLVFullLengthURL']
        menuItem = {
                        'id' : video['displayName'],
                        'name' : video['displayName'],
                        'url' : videoUrl,
                        'icon' : '',
                        'isFolder' : False,
                        'kwargs' : kwargs
                    }
        menu.append(menuItem)
    return menu
    