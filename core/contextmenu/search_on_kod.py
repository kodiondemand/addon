import xbmc, sys, xbmcgui, os
from platformcode import config, logger

# incliuding folder libraries
librerias = xbmc.translatePath(os.path.join(config.get_runtime_path(), 'lib'))
sys.path.insert(0, librerias)


from core import tmdb
from core.item import Item

addon_id = config.get_addon_core().getAddonInfo('id')


def check_condition():
    logger.debug('[SOK] check item condition')
    mediatype = xbmc.getInfoLabel('ListItem.DBTYPE')

    folderPath = xbmc.getInfoLabel('Container.FolderPath')
    filePath = xbmc.getInfoLabel('ListItem.FileNameAndPath')

    logger.debug('Container:',folderPath )
    logger.debug('listitem mediatype:',mediatype )
    logger.debug('filenamepath:',filePath )

    # we_are_in_kod = folderPath.find( addon_id ) > -1
    item_is_coming_from_kod = addon_id in filePath

    # logger.info('[SOK] container is KOD? {}'.format(we_are_in_kod) )

    return mediatype and not item_is_coming_from_kod # and not we_are_in_kod

def get_menu_item():
    logger.debug('get menu item')
    return config.get_localized_string(90005)


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


    logger.info("Search on KOD (gobalsearch)")

    item = Item(
    action="Search",
    channel="globalsearch",
    contentType= mediatype,
    mode="search",
    text= title,
    type= mediatype,
    infoLabels= {
        'tmdb_id': tmdbid,
        'year': year
    },
    folder= False
    )

    logger.info("Invoking Item:", item.tostring() )

    itemurl = item.tourl()
    xbmc.executebuiltin("RunPlugin(plugin://plugin.video.kod/?" + itemurl + ")")




