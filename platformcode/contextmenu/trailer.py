import xbmc

from core.item import Item
from platformcode import config


def get_menu_items():
    return [(config.get_localized_string(60359), execute)]


def execute():
    tmdbid = xbmc.getInfoLabel('ListItem.Property(tmdb_id)')
    year = xbmc.getInfoLabel('ListItem.Year')
    mediatype = xbmc.getInfoLabel('ListItem.DBTYPE')
    title = xbmc.getInfoLabel('ListItem.Title')
    if mediatype in ('episode', 'season'):
        mediatype = 'tvshow'
        title = xbmc.getInfoLabel('ListItem.TVShowTitle')

    item = Item(channel="trailertools", action="buscartrailer", search_title=title, contentType=mediatype,
                year=year, contentTitle=title, contextual=True)
    item.infoLabels['tmdb_id'] = tmdbid
    xbmc.executebuiltin("RunPlugin(plugin://plugin.video.kod/?" + item.tourl() + ")")
