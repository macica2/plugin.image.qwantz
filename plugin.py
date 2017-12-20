import sys
from bs4 import BeautifulSoup
import os
import random
from traceback import format_exc
import urllib
import urllib2
import urlparse
import xbmcaddon
import xbmcgui
import xbmcplugin

# Constants
LATEST_FOLDER_NAME = "Latest Comic"
RANDOM_FOLDER_NAME = "Random Comic"
PREV_FOLDER_NAME = "Previous Comic"
NEXT_FOLDER_NAME = "Next Comic"
BROWSE_FOLDER_NAME = "Browse by ID"
BROWSE_RANGE_FOLDER_NAME = "Browse Range"

def build_url(query):
    """ Builds the URL for Kodi to traverse pages """
    return base_url + '?' + urllib.urlencode(query)

def get_latest_comic_id():
    """ Returns the ID of the most recently published comic """
    try:
        soup = BeautifulSoup(urllib2.urlopen('http://www.qwantz.com/'), "html.parser")
        prevId = soup.find_all('a', { 'title': 'Previous comic' })[0]['href'].split('comic=')[1]
        curId = int(prevId) + 1
        xbmc.log('curId is ' + str(curId))
        return curId
    except Exception:
        xbmc.log(format_exc())
        return 1 # default to first comic if we can't grab latest

def add_comic_item(url, includePrevAndNext):
    """ Parses the HTML at the specified URL to grab the comic's information and add it to the results """
    try:
        xbmc.log('url is ' + url)
        soup = BeautifulSoup(urllib2.urlopen(url), "html.parser")
        title = soup.title.string
        date = title.split(' - ')[1]
        img = soup.find_all('img', { 'class': 'comic' })[0]
        imgSrc = img['src']
        altText = img['title']
        #nextBtns = soup.find_all('a', { 'title' : 'Next comic' })
        
        li = xbmcgui.ListItem(date, iconImage='DefaultPicture.png')
        li.setProperty('description', altText)
        xbmc.log('setting img with addon_handle ' + str(addon_handle))
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=imgSrc, listitem=li)
    except Exception:
        xbmc.log(format_exc())
    
    if includePrevAndNext:
        add_arrow_item(soup, 'Previous comic', PREV_FOLDER_NAME, 'leftarrow.png')
        add_arrow_item(soup, 'Next comic', NEXT_FOLDER_NAME, 'rightarrow.png')
            
def add_arrow_item(soup, titleText, folderName, iconName):
    """ Adds the previous or next arrow button for the comic 
        The first comic won't have a previous arrow,
        and the most recent comic won't have a next arrow.
    """
    try:
        btns = soup.find_all('a', { 'title': titleText })
        if btns:
            href = btns[0]['href'] # contains link to comic, e.g. http://www.qwantz.com/index.php?comic=3184
            #xbmc.log('prev href = ' + prevHref)
            iconPath = os.path.join(xbmcaddon.Addon().getAddonInfo('path'), 'resources', iconName)
            #xbmc.log('iconPath is ' + iconPath)
            item = xbmcgui.ListItem(folderName, iconImage=iconPath, thumbnailImage=iconPath)
            url = build_url({'mode': 'folder', 'foldername': folderName, 'imgUrl': href})
            #.log('setting arrow with addon_handle ' + str(addon_handle))
            xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=item, isFolder=True)
        else:
            xbmc.log('no prev btn found')
    except Exception:
        xbmc.log(format_exc())

def browse_by_id(latestComicId):
    """ Returns a list of folders to view comics sorted by their IDs """
    items = []
    comicsPerPage = 10
    maxIndex = (latestComicId // comicsPerPage) + (latestComicId % comicsPerPage > 0)
    for i in range(0, maxIndex):
        startId = i*comicsPerPage + 1
        endId = i*comicsPerPage + comicsPerPage
        itemTitle = str(startId) + " - " + str(endId)
        li = xbmcgui.ListItem(itemTitle)
        url = build_url({'mode': 'folder', 'foldername': BROWSE_RANGE_FOLDER_NAME, 'latestComicId': latestComicId,
                            'startId': startId, 'endId': endId})
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)
    xbmcplugin.endOfDirectory(addon_handle)
    
def build_initial_folders(latestComicId):
    """ Builds the folders that the user sees when first opening the add-on """
    build_initial_folder(LATEST_FOLDER_NAME, latestComicId, 'latestcomicicon.png')
    build_initial_folder(RANDOM_FOLDER_NAME, latestComicId, 'randomcomicicon.png')
    build_initial_folder(BROWSE_FOLDER_NAME, latestComicId, 'browsecomicsicon.png')
    
def build_initial_folder(folderName, latestComicId, iconName):
    """ Builds a single folder that the user sees when first opening the add-on """
    iconPath = os.path.join(xbmcaddon.Addon().getAddonInfo('path'), 'resources', iconName)
    url = build_url({'mode': 'folder', 'foldername': folderName, 'latestComicId': latestComicId})
    li = xbmcgui.ListItem(folderName, iconImage=iconPath, thumbnailImage=iconPath)
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)

# Main code
base_url = sys.argv[0]
addon_handle = int(sys.argv[1])
args = urlparse.parse_qs(sys.argv[2][1:]) # skip first character since it's always a ?
# This will give us a dict of lists; for example, '?foo=bar&foo=baz&quux=spam' 
# would be converted to {'foo': ['bar', 'baz'], 'quux': ['spam']}.

xbmc.log("add on handle is " + str(addon_handle))
xbmc.log("base url is " + base_url)

xbmcplugin.setContent(addon_handle, 'images')

mode = args.get('mode', None)

if mode is None:
    # The user just opened the add-on, so display initial options.
    latestComicId = get_latest_comic_id()   
    build_initial_folders(latestComicId)
    xbmcplugin.endOfDirectory(addon_handle)
	
elif mode[0] == 'folder':
    foldername = args['foldername'][0]
    #xbmc.log('foldername is ' + foldername)
    if (foldername == BROWSE_FOLDER_NAME):
        browse_by_id(int(args['latestComicId'][0]))
    elif (foldername == BROWSE_RANGE_FOLDER_NAME):
        startId = int(args['startId'][0])
        endId = int(args['endId'][0])
        latestComicId = int(args['latestComicId'][0])
        #xbmc.log('start is ' + str(startId) + ' end is ' + str(endId) + ' latest is ' + str(latestComicId))
        for i in range(startId, endId + 1):
            if (i <= latestComicId):
                add_comic_item("http://www.qwantz.com/index.php?comic=" + str(i), False)
        xbmcplugin.endOfDirectory(addon_handle)
    else:
        if (foldername == LATEST_FOLDER_NAME):
            #xbmc.log('displaying latest comic')
            url = 'http://www.qwantz.com'
        elif (foldername == RANDOM_FOLDER_NAME):
            #xbmc.log('displaying random comic')
            latestComicId = int(args['latestComicId'][0])
            #xbmc.log('latest comic id in rand is ' + str(latestComicId))
            randId = random.randint(1,latestComicId)
            #xbmc.log('rand comic id is ' + str(randId))
            url = 'http://www.qwantz.com/index.php?comic=' + str(randId)
        elif foldername == PREV_FOLDER_NAME or foldername == NEXT_FOLDER_NAME:
            #xbmc.log('displaying prev/next comic')
            url = args['imgUrl'][0]
        add_comic_item(url, True)
        xbmcplugin.endOfDirectory(addon_handle)