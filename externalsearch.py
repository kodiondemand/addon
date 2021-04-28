import xbmc, sys, xbmcgui, os
from platformcode import config, logger

# incliuding folder libraries
librerias = xbmc.translatePath(os.path.join(config.get_runtime_path(), 'lib'))
sys.path.insert(0, librerias)


from core import tmdb
from core.item import Item

def execute_search():
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
    # folderPath = xbmc.getInfoLabel('Container.FolderPath')
    # filePath = xbmc.getInfoLabel('ListItem.FileNameAndPath')
    # logger.info("****")
    # logger.info( xbmc.getCondVisibility("String.Contains(Container.FolderPath, 'plugin.video.kod')") )
    # logger.info( xbmc.getCondVisibility("String.Contains(ListItem.FileNameAndPath, 'plugin.video.kod')") )
    # logger.info( xbmc.getCondVisibility("String.IsEqual(ListItem.dbtype,tvshow)") )
    # logger.info( xbmc.getCondVisibility("String.IsEqual(ListItem.dbtype,movie)") )
    # logger.info("****")

    # visible = xbmc.getCondVisibility("!String.StartsWith(ListItem.FileNameAndPath, 'plugin://plugin.video.kod/') + [String.IsEqual(ListItem.dbtype,tvshow) | String.IsEqual(ListItem.dbtype,movie)]")

    logstr = "Selected ListItem is: 'IMDB: {}' - TMDB: {}' - 'Title: {}' - 'Year: {}'' - 'Type: {}'".format(imdb, tmdbid, title, year, mediatype)
    logger.info(logstr)

    if not tmdbid and imdb:
        logger.info('No TMDBid found. Try to get by IMDB')
        it = Item(contentType= mediatype, infoLabels={'imdb_id' : imdb})
        tmdb.set_infoLabels(it)
        tmdbid = it.infoLabels.get('tmdb_id', '')

    if not tmdbid:
        logger.info('No TMDBid found. Try to get by Title/Year')
        it = Item(contentTitle= title, contentType= mediatype, infoLabels={'year' : year})
        tmdb.set_infoLabels(it)
        tmdbid = it.infoLabels.get('tmdb_id', '')


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

    logger.info("Invoking Item: {}".format(item.tostring()))

    itemurl = item.tourl()
    xbmc.executebuiltin("RunPlugin(plugin://plugin.video.kod/?" + itemurl + ")")


if __name__ == '__main__':
    execute_search()
