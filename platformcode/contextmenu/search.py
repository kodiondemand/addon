import xbmc, sys, os
from platformcode import config, logger
import re
# incliuding folder libraries
librerias = xbmc.translatePath(os.path.join(config.get_runtime_path(), 'lib'))
sys.path.insert(0, librerias)


from core import tmdb
from core.item import Item

addon_id = config.get_addon_core().getAddonInfo('id')
global item_is_coming_from_kod


def check_condition():
    global item_is_coming_from_kod
    logger.debug('check item condition')
    mediatype = xbmc.getInfoLabel('ListItem.DBTYPE')

    folderPath = xbmc.getInfoLabel('Container.FolderPath')
    filePath = xbmc.getInfoLabel('ListItem.Path')
    fileNameAndPath = xbmc.getInfoLabel('ListItem.FileNameAndPath')

    logger.debug('Container:',folderPath )
    logger.debug('listitem mediatype:',mediatype )
    logger.debug('filenamepath:', fileNameAndPath )
    logger.info('filepath:', filePath )
    
    item_is_coming_from_kod = addon_id in filePath
    if not item_is_coming_from_kod:
        videolibpath = config.get_setting("videolibrarypath")
        if filePath.startswith(videolibpath):
            pattern = re.compile("\[.*\][\\\/]?$")
            item_is_coming_from_kod = pattern.search(filePath)

    if item_is_coming_from_kod:
        logger.debug("item IS already managed by KOD")

    return mediatype


def get_menu_items():
    logger.debug('get menu item')
    if check_condition():
        return [(config.get_localized_string(90003 if item_is_coming_from_kod else 90005), execute)]
    else:
        return []


def execute():
    """
    Gather the selected ListItem's attributes in order to compute the `Item` parameters
    and perform the KOD's globalsearch.
    Globalsearch will be executed specifing the content-type of the selected ListItem

    NOTE: this method needs the DBTYPE and TMDB_ID specified as ListItem's properties
    """

    # These following lines are commented and keep in the code just as reminder.
    # In future, they could be used to filter the search outcome

    # ADDON: maybe can we know if the current windows is related to a specific addon?
    # we could skip the ContextMenu if we already are in KOD's window

    tmdbid = xbmc.getInfoLabel('ListItem.Property(tmdb_id)')
    mediatype = xbmc.getInfoLabel('ListItem.DBTYPE')
    title = xbmc.getInfoLabel('ListItem.Title')
    year = xbmc.getInfoLabel('ListItem.Year')
    imdb = xbmc.getInfoLabel('ListItem.IMDBNumber')

    if mediatype in ('episode', 'season'):
        mediatype = 'tvshow'
        title = xbmc.getInfoLabel('ListItem.TVShowTitle')

    logstr = "Selected ListItem is: 'IMDB: {}' - TMDB: {}' - 'Title: {}' - 'Year: {}'' - 'Type: {}'".format(imdb, tmdbid, title, year, mediatype)
    logger.info(logstr)

    if not tmdbid and imdb:
        logger.info('No TMDBid found. Try to get by IMDB')
        it = Item(contentType= mediatype, infoLabels={'imdb_id' : imdb})
        try:
            tmdb.set_infoLabels(it)
            tmdbid = it.infoLabels.get('tmdb_id', '')
        except:
            logger.info("Cannot find TMDB via imdb")

    if not tmdbid:
        logger.info('No TMDBid found. Try to get by Title/Year')
        it = Item(contentTitle= title, contentType= mediatype, infoLabels={'year' : year})
        try:
            tmdb.set_infoLabels(it)
            tmdbid = it.infoLabels.get('tmdb_id', '')
        except:
            logger.info("Cannot find TMDB via title/year")

    if not tmdbid:
        # We can continue searching by 'title (year)'
        logger.info( "No TMDB found, proceed with title/year:",  title , "(" , year, ")" )

    # User wants to search on other channels
    logger.info("Search on other channels")

    item = Item(
    action="from_context",
    channel="search",
    contentType= mediatype,
    mode="search",
    contextual= True,
    text=title,
    type= mediatype,
    infoLabels= {
        'tmdb_id': tmdbid,
        'year': year,
        'mediatype': mediatype
    },
    folder= False
    )

    logger.info("Invoking Item: ", item.tostring() )

    itemurl = item.tourl()

    if config.get_setting('new_search'):
        xbmc.executebuiltin("RunPlugin(plugin://plugin.video.kod/?" + itemurl + ")")
    else:
        xbmc.executebuiltin("Container.Update(plugin://plugin.video.kod/?" + itemurl + ")")




