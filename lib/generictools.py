# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# GenericTools
# ------------------------------------------------------------
# Reusable code of different parts of channels that can
# be called from other channels, and thus charify the format
# and result of each channel and reduce the cost of its maintenance
# ------------------------------------------------------------

import re, os, sys, datetime, time, traceback
try: import urlparse
except: import urllib.parse as urlparse

from channelselector import get_thumb
from core import httptools, scrapertools, servertools, channeltools, filetools, tmdb
from core.item import Item
from platformcode import config, logger, platformtools
from lib import jsunpack

channel_py = "newpct1"
intervenido_judicial = 'Domain intervened by the Judicial Authority'
intervenido_policia = 'Judicial_Policia_Nacional'
intervenido_guardia = 'Judicial_Guardia_Civil'
intervenido_sucuri = 'Access Denied - Sucuri Website Firewall'


def update_title(item):
    logger.debug()
    from core import scraper,support


    """
    Utility to disambiguate Titles before adding them to the Video Library. Can be called from Videolibrarytools
    or from Episodes on a Channel. If called from a channel, the call would be like this (included in post_tmdb_episodes (item, itemlist)):

        # Allow the updating of titles, either for immediate use, or to add to the video library
        item.from_action = item.action      # Save action
        item.from_title = item.title        # Save Title
        itemlist.append(item.clone(title="** [COLOR limegreen]Update Titles - video library preview[/COLOR] **", action="actualizar_titulos", extra="episodios", tmdb_stat=False))

    The channel must add a method to be able to receive the call from Kodi / Alfa, and be able to call this method:

    def actualizar_titulos(item):
        logger.debug()
        itemlist = []
        from lib import generictools
        from platformcode import launcher

        item = generictools.update_title(item) # We call the method that updates the title with tmdb.find_and_set_infoLabels

        # We return to the next action on the channel
        return launcher.run(item)

    To disambiguate titles, TMDB is caused to ask for the really desired title, deleting existing IDs
    The user can select the title among those offered on the first screen
    or you can cancel and enter a new title on the second screen
    If you do it in "Enter another name", TMDB will automatically search for the new title
    If you do this under "Complete Information", it changes to the new title, but does not search TMDB. We have to do it again
    If the second screen is canceled, the variable "scraper_return" will be False. The user does not want to continue
    """
    # logger.debug(item)

    # We restore and delete intermediate labels (if called from the channel)
    if item.from_action:
        item.action = item.from_action
        del item.from_action
    if item.from_update:
        if item.from_title_tmdb:            # If the title of the content returned by TMDB was saved, it is restored.
            item.title = item.from_title_tmdb
    else:
        item.add_videolibrary = True        # We are Adding to the Video Library. Indicator to control the use of Channels
    if item.add_videolibrary:
        if item.season_colapse: del item.season_colapse
        if item.from_num_season_colapse: del item.from_num_season_colapse
        if item.from_title_season_colapse: del item.from_title_season_colapse
        if item.contentType == "movie":
            if item.from_title_tmdb:        # If the title of the content returned by TMDB was saved, it is restored.
                item.title = item.from_title_tmdb
            del item.add_videolibrary
        if item.channel_host:               # We already delete the indicator so that it is not stored in the Video Library
            del item.channel_host
        if item.contentTitle:
            item.contentTitle = re.sub(r' -%s-' % item.category, '', item.contentTitle)
            item.title = re.sub(r' -%s-' % item.category, '', item.title)
    if item.contentType == 'movie':
        from_title_tmdb = item.contentTitle
    else:
        from_title_tmdb = item.contentSerieName

    # We only execute this code if it has not been done before in the Channel. For example, if you have called from Episodes or Findvideos,
    # The Add to Video Library will no longer be executed, although from the channel you can call as many times as you want,
    # or until you find an unambiguous title
    if item.tmdb_stat:
        if item.from_title_tmdb: del item.from_title_tmdb
        if item.from_title: del item.from_title
        item.from_update = True
        del item.from_update
        if item.contentType == "movie":
            if item.channel == channel_py:  # If it is a NewPct1 movie, we put the name of the clone
                item.channel = scrapertools.find_single_match(item.url, r'http.?\:\/\/(?:www.)?(\w+)\.\w+\/')
    else:
        new_item = item.clone()             # We save the initial Item to restore it if the user cancels
        if item.contentType == "movie":
            if item.channel == channel_py:  # If it is a NewPct1 movie, we put the name of the clone
                item.channel = scrapertools.find_single_match(item.url, r'http.?\:\/\/(?:www.)?(\w+)\.\w+\/')
        # We delete the IDs and the year to force TMDB to ask us
        if item.infoLabels['tmdb_id'] or item.infoLabels['tmdb_id'] == None: item.infoLabels['tmdb_id'] = ''
        if item.infoLabels['tvdb_id'] or item.infoLabels['tvdb_id'] == None: item.infoLabels['tvdb_id'] = ''
        if item.infoLabels['imdb_id'] or item.infoLabels['imdb_id'] == None: item.infoLabels['imdb_id'] = ''
        if item.infoLabels['season']: del item.infoLabels['season'] # It works wrong with num. seasonal. Then we restore it
        item.infoLabels['year'] = '-'

        if item.from_title:
            if item.from_title_tmdb:
                if scrapertools.find_single_match(item.from_title_tmdb, r'^(?:\[COLOR \w+\])?(.*?)(?:\[)'):
                    from_title_tmdb = scrapertools.find_single_match(item.from_title_tmdb, r'^(?:\[COLOR \w+\])?(.*?)(?:\[)').strip()
            item.title = item.title.replace(from_title_tmdb, item.from_title)
            item.infoLabels['title'] = item.from_title

            if item.from_title_tmdb: del item.from_title_tmdb
        if not item.from_update and item.from_title: del item.from_title

        if item.contentSerieName and item.contentType == 'tvshow':           # We copy the title to serve as a reference in the "Complete Information" menu
            item.infoLabels['originaltitle'] = item.contentSerieName
            item.contentTitle = item.contentSerieName
        else:
            item.infoLabels['originaltitle'] = item.contentTitle

        scraper_return = scraper.find_and_set_infoLabels(item)

        if not scraper_return:  # If the user has canceled, we restore the data to the initial situation and leave
            return
            # item = new_item.clone()
        else:
            # If the user has changed the data in "Complete Information" you must see the final title in TMDB
            if not item.infoLabels['tmdb_id']:
                if item.contentSerieName:
                    item.contentSerieName = item.contentTitle                       # New title is put
                item.infoLabels['noscrap_id'] = ''                                  # It resets, just in case
                item.infoLabels['year'] = '-'                                       # It resets, just in case
                scraper_return = scraper.find_and_set_infoLabels(item)              # Try again

                # It seems the user has canceled again. We restore the data to the initial situation
                if not scraper_return or not item.infoLabels['tmdb_id']:
                    item = new_item.clone()
                else:
                    item.tmdb_stat = True           # We mark Item as processed correctly by TMDB (pass 2)
            else:
                item.tmdb_stat = True               # We mark Item as successfully processed by TMDB (pass 1)

            # If the user has selected a different option or changed something, we adjust the titles
            if item.contentType != 'movie' or item.from_update:
                item.channel = new_item.channel     # Restoring the name of the channel, in case we had changed it
            if item.tmdb_stat == True:
                if new_item.contentSerieName:       # If it's serial ...
                    filter_languages =  config.get_setting("filter_languages", item.channel)
                    if filter_languages and filter_languages >= 0:
                        item.title_from_channel = new_item.contentSerieName         # I keep the initial title for Filtertools
                        item.contentSerieName = new_item.contentSerieName           # I keep the initial title for Filtertools
                    else:
                        item.title = item.title.replace(new_item.contentSerieName, item.contentTitle).replace(from_title_tmdb, item.contentTitle)
                        item.contentSerieName = item.contentTitle
                    if new_item.contentSeason: item.contentSeason = new_item.contentSeason      # We restore Season
                    if item.infoLabels['title']: del item.infoLabels['title']       # We delete movie title (it is series)
                else:                                                               # If it's a movie ...
                    item.title = item.title.replace(new_item.contentTitle, item.contentTitle).replace(from_title_tmdb, item.contentTitle)
                if new_item.infoLabels['year']:                                     # We update the Year in the title
                    item.title = item.title.replace(str(new_item.infoLabels['year']), str(item.infoLabels['year']))
                if new_item.infoLabels['rating']:                                   # We update in Rating in the title
                    try:
                        rating_old = ''
                        if new_item.infoLabels['rating'] and new_item.infoLabels['rating'] != 0.0:
                            rating_old = float(new_item.infoLabels['rating'])
                            rating_old = round(rating_old, 1)
                        rating_new = ''
                        if item.infoLabels['rating'] and item.infoLabels['rating'] != 0.0:
                            rating_new = float(item.infoLabels['rating'])
                            rating_new = round(rating_new, 1)
                        item.title = item.title.replace("[" + str(rating_old) + "]", "[" + str(rating_new) + "]")
                    except:
                        logger.error(traceback.format_exc())
                if item.wanted:                                         # We update Wanted, if it exists
                    item.wanted = item.contentTitle
                if new_item.contentSeason:                              # We restore the no. Season after TMDB
                    item.contentSeason = new_item.contentSeason

                if item.from_update:                                    # If the call is from the channel menu ...
                    item.from_update = True
                    del item.from_update
                    xlistitem = refresh_screen(item)                    # We refresh the screens with the new Item

        # To avoid TMDB "memory effect", it is called with a dummy title to reset buffers
        # if item.contentSerieName:
        #     new_item.infoLabels['tmdb_id'] = '289'                      # an unambiguous series
        # else:
        #     new_item.infoLabels['tmdb_id'] = '111'                      # an unambiguous movie
        # new_item.infoLabels['year'] = '-'
        # if new_item.contentSeason:
        #     del new_item.infoLabels['season']                           # It works wrong with num. seasonal
        # support.dbg()
        # scraper_return = scraper.find_and_set_infoLabels(new_item)

    #logger.debug(item)

    return item


def refresh_screen(item):
    logger.debug()

    """
    #### Kodi 18 compatibility ####

    Refreshes the screen with the new Item after having established a dialog that has caused the change of Item
    Create an xlistitem to trick Kodi with the xbmcplugin.setResolvedUrl function FALSE

    Entry: item:    The updated Item
    Output: xlistitem   The xlistitem created, in case it is of any later use
    """

    try:
        import xbmcplugin
        import xbmcgui

        xlistitem = xbmcgui.ListItem(path=item.url)                     # We create xlistitem for compatibility with Kodi 18
        if config.get_platform(True)['num_version'] >= 16.0:
            xlistitem.setArt({"thumb": item.contentThumbnail})          # We load the thumb
        else:
            xlistitem.setThumbnailImage(item.contentThumbnail)
        xlistitem.setInfo("video", item.infoLabels)                     # We copy infoLabel

        xbmcplugin.setResolvedUrl(int(sys.argv[1]), False, xlistitem)   # We prepare the environment to avoid Kod1 error 18
        time.sleep(1)                                                   # We leave time for it to run
    except:
        logger.error(traceback.format_exc())

    platformtools.itemlist_update(item)                                 # we refresh the screen with the new Item

    return xlistitem


def post_tmdb_listado(item, itemlist):
    logger.debug()
    itemlist_fo = []

    """

   Last for makeup of the titles obtained from TMDB in List and List_Search.

    InfoLabel takes all the data of interest and places them in different variables, mainly title
    so that it is compatible with Unify, and if there are no Smart Titles, so that the format is the most
    similar to Unify.

    It also restores various saved data from the title before passing it through TMDB, as keeping them would not have found the title (title_subs)

    The method call from Listing or Listing_Search, after passing Itemlist pot TMDB, is:

        from lib import generictools
        item, itemlist = generictools.post_tmdb_listado (item, itemlist)
    """
    # logger.debug(item)

    # We delete values ​​if there has been a fail-over
    channel_alt = ''
    if item.channel_alt:
        channel_alt = item.channel_alt
        del item.channel_alt
    if item.url_alt:
        del item.url_alt

    # We adjust the category name
    if not item.category_new:
        item.category_new = ''

    for item_local in itemlist:                                 # We go through the Itemlist generated by the channel
        item_local.title = re.sub(r'(?i)online|descarga|downloads|trailer|videoteca|gb|autoplay', '', item_local.title).strip()
        # item_local.title = re.sub(r'online|descarga|downloads|trailer|videoteca|gb|autoplay', '', item_local.title, flags=re.IGNORECASE).strip()
        title = item_local.title
        # logger.debug(item_local)

        item_local.last_page = 0
        del item_local.last_page                                # We delete traces of pagination

        if item_local.contentSeason_save:                       # We restore the num. seasonal
            item_local.contentSeason = item_local.contentSeason_save

        # We delete values ​​for each Content if there has been a fail-over
        if item_local.channel_alt:
            del item_local.channel_alt
        if item_local.url_alt:
            del item_local.url_alt
        if item_local.extra2:
            del item_local.extra2
        if item_local.library_filter_show:
            del item_local.library_filter_show
        if item_local.channel_host:
            del item_local.channel_host

        # We adjust the category name
        if item_local.channel == channel_py:
            item_local.category = scrapertools.find_single_match(item_local.url, r'http.?\:\/\/(?:www.)?(\w+)\.\w+\/').capitalize()

        # We restore the additional info saved in the title_subs list, and delete it from Item
        title_add = ' '
        if item_local.title_subs:
            for title_subs in item_local.title_subs:
                if "audio" in title_subs.lower():                               # restores Audio info
                    title_add += scrapertools.find_single_match(title_subs, r'[a|A]udio (.*?)')
                    continue
                if scrapertools.find_single_match(title_subs, r'(\d{4})'):      # The year is restored, if it has not been given by TMDB
                    if not item_local.infoLabels['year'] or item_local.infoLabels['year'] == "-":
                        item_local.infoLabels['year'] = scrapertools.find_single_match(title_subs, r'(\d{4})')
                    continue

                title_add = title_add.rstrip()
                title_add = '%s -%s-' % (title_add, title_subs)                 # all other saved tags are added
        item_local.title_subs = []
        del item_local.title_subs

        # We prepare the video Rating
        rating = ''
        try:
            if item_local.infoLabels['rating'] and item_local.infoLabels['rating'] != 0.0:
                rating = float(item_local.infoLabels['rating'])
                rating = round(rating, 1)
                if rating == 0.0:
                    rating = ''
        except:
            logger.error(traceback.format_exc())

        __modo_grafico__ = config.get_setting('modo_grafico', item.channel)

        # If TMDB has not found the video we clean the year
        if item_local.infoLabels['year'] == "-":
            item_local.infoLabels['year'] = ''
            item_local.infoLabels['aired'] = ''

        # If it brought the TMDB-ID, but it did not work, we reset it and tried again
        if item_local.infoLabels['tmdb_id'] and not item_local.infoLabels['originaltitle']:
            logger.error("*** Wrong TMDB-ID, reset and retry ***")
            logger.error(item_local)
            del item_local.infoLabels['tmdb_id']                # you can bring a wrong TMDB-ID
            try:
                tmdb.set_infoLabels(item_local, __modo_grafico__)       # we go through TMDB again
            except:
                logger.error(traceback.format_exc())
            logger.error(item_local)

        # If TMDB has not found anything and we have used the year of the web, we try without year
        if not item_local.infoLabels['tmdb_id']:
            if item_local.infoLabels['year']:                   # We try again only if there was a year, I may be wrong
                year = item_local.infoLabels['year']            # we save the year in case the new search is not successful
                item_local.infoLabels['year'] = "-"             # reset the year
                try:
                    tmdb.set_infoLabels(item_local, __modo_grafico__)   # we go through TMDB again
                except:
                    logger.error(traceback.format_exc())
                if not item_local.infoLabels['tmdb_id']:        # it has been successful?
                    item_local.infoLabels['year'] = year        # no, we restore the year and leave it now

        # For Episodes, I take the year of exposure and not the year of beginning of the series
        if item_local.infoLabels['aired']:
            item_local.infoLabels['year'] = scrapertools.find_single_match(str(item_local.infoLabels['aired']), r'\/(\d{4})')

        if item_local.from_title:
            if item_local.contentType == 'movie':
                item_local.contentTitle = item_local.from_title
                item_local.title = item_local.from_title
            else:
                item_local.contentSerieName = item_local.from_title
            if item_local.contentType == 'season':
                item_local.title = item_local.from_title
            item_local.title = re.sub(r'(?i)online|descarga|downloads|trailer|videoteca|gb|autoplay', '', item_local.title).strip()
            title = item_local.title

        # We clean quality of original titles that may have been cast
        if item_local.infoLabels['originaltitle'].lower() in item_local.quality.lower():
            item_local.quality = re.sub(item_local.infoLabels['originaltitle'], '', item_local.quality)
            #item_local.quality = re.sub(item_local.infoLabels['originaltitle'], '', item_local.quality, flags=re.IGNORECASE)

        # We prepare the title for series, with no. of seasons, if any
        if item_local.contentType in ['season', 'tvshow', 'episode']:
            if item_local.contentType == "episode":

                # If the title of the episode is not there, but it is in "title", we rescue it
                if not item_local.infoLabels['episodio_titulo'] and item_local.infoLabels['title'].lower() != item_local.infoLabels['tvshowtitle'].lower():
                    item_local.infoLabels['episodio_titulo'] = item_local.infoLabels['title']

                if "Temporada" in title:                    # We make "Season" compatible with Unify
                    title = '%sx%s al 99 -' % (str(item_local.contentSeason), str(item_local.contentEpisodeNumber))
                if " al " in title:                         # If they are multiple episodes, we put a series name
                    if " al 99" in title.lower():           # Full season. We are looking for total number of episodes
                        title = title.replace("99", str(item_local.infoLabels['temporada_num_episodios']))
                    title = '%s %s' % (title, item_local.contentSerieName)
                    item_local.infoLabels['episodio_titulo'] = '%s - %s [%s] [%s]' % (scrapertools.find_single_match(title, r'(al \d+)'), item_local.contentSerieName, item_local.infoLabels['year'], rating)

                elif item_local.infoLabels['episodio_titulo']:
                    title = '%s %s, %s' % (title, item_local.infoLabels['episodio_titulo'], item_local.contentSerieName)
                    item_local.infoLabels['episodio_titulo'] = '%s, %s [%s] [%s]' % (item_local.infoLabels['episodio_titulo'], item_local.contentSerieName, item_local.infoLabels['year'], rating)

                else:                                       # If there is no episode title, we will put the name of the series
                    if item_local.contentSerieName not in title:
                        title = '%s %s' % (title, item_local.contentSerieName)
                    item_local.infoLabels['episodio_titulo'] = '%s [%s] [%s]' % (item_local.contentSerieName, item_local.infoLabels['year'], rating)

                if not item_local.contentSeason or not item_local.contentEpisodeNumber:
                    if "Episodio" in title_add:
                        item_local.contentSeason, item_local.contentEpisodeNumber = scrapertools.find_single_match(title_add, r'Episodio (\d+)x(\d+)')
                        title = '%s [%s] [%s]' % (title, item_local.infoLabels['year'], rating)

            elif item_local.contentType == "season":
                if not item_local.contentSeason:
                    item_local.contentSeason = scrapertools.find_single_match(item_local.url, r'-(\d+)x')
                if not item_local.contentSeason:
                    item_local.contentSeason = scrapertools.find_single_match(item_local.url, r'-temporadas?-(\d+)')
                if item_local.contentSeason:
                    title = '%s -Temporada %s' % (title, str(item_local.contentSeason))
                    if not item_local.contentSeason_save:                           # We restore the num. seasonal
                        item_local.contentSeason_save = item_local.contentSeason    # And we save him again
                    del item_local.infoLabels['season']         # It works wrong with num. seasonal. Then we restore it
                else:
                    title = '%s -Temporada !!!' % (title)

            elif item.action == "search" or item.extra == "search":
                title += " -Serie-"

        if (item_local.extra == "varios" or item_local.extra == "documentales") and (item.action == "search" or item.extra == "search" or item.action == "listado_busqueda"):
            title += " -Varios-"
            item_local.contentTitle += " -Varios-"

        title += title_add                          # Additional tags are added, if any

        # Now we make up the titles a bit depending on whether smart titles have been selected or not
        if not config.get_setting("unify"):         # If Smart Titles NOT selected:
            title = '%s [COLOR yellow][%s][/COLOR] [%s] [COLOR limegreen][%s][/COLOR] [COLOR red]%s[/COLOR]' % (title, str(item_local.infoLabels['year']), rating, item_local.quality, str(item_local.language))

        else:                                       # If Smart Titles YES selected:
            title = title.replace("[", "-").replace("]", "-").replace(".", ",").replace("GB", "G B").replace("Gb", "G b").replace("gb", "g b").replace("MB", "M B").replace("Mb", "M b").replace("mb", "m b")

        # We clean the empty labels
        if item_local.infoLabels['episodio_titulo']:
            item_local.infoLabels['episodio_titulo'] = item_local.infoLabels['episodio_titulo'].replace(" []", "").strip()
        title = title.replace("--", "").replace(" []", "").replace("()", "").replace("(/)", "").replace("[/]", "").strip()
        title = re.sub(r'\s?\[COLOR \w+\]\[\[?\s?\]?\]\[\/COLOR\]', '', title).strip()
        title = re.sub(r'\s?\[COLOR \w+\]\s?\[\/COLOR\]', '', title).strip()

        if item.category_new == "newest":           # It comes from News. We mark the title with the name of the channel
            if scrapertools.find_single_match(item_local.url, r'http.?\:\/\/(?:www.)?(\w+)\.\w+\/'):
                title += ' -%s-' % scrapertools.find_single_match(item_local.url, r'http.?\:\/\/(?:www.)?(\w+)\.\w+\/').capitalize()
            else:
                title += ' -%s-' % item_local.channel.capitalize()
            if item_local.contentType == "movie":
                if scrapertools.find_single_match(item_local.url, r'http.?\:\/\/(?:www.)?(\w+)\.\w+\/'):
                    item_local.contentTitle += ' -%s-' % scrapertools.find_single_match(item_local.url, r'http.?\:\/\/(?:www.)?(\w+)\.\w+\/').capitalize()
                else:
                    item_local.contentTitle += ' -%s-' % item_local.channel.capitalize()
            elif "Episodio " in title:
                if not item_local.contentSeason or not item_local.contentEpisodeNumber:
                    item_local.contentSeason, item_local.contentEpisodeNumber = scrapertools.find_single_match(title_add, r'Episodio (\d+)x(\d+)')

        item_local.title = title

        #logger.debug("url: " + item_local.url + " / title: " + item_local.title + " / content title: " + item_local.contentTitle + "/" + item_local.contentSerieName + " / calidad: " + item_local.quality + "[" + str(item_local.language) + "]" + " / year: " + str(item_local.infoLabels['year']))

        #logger.debug(item_local)

    # If judicial intervention, I warn !!!
    if item.intervencion:
        for clone_inter, autoridad in item.intervencion:
            thumb_intervenido = get_thumb(autoridad)
            itemlist_fo.append(item.clone(action='', title="[COLOR yellow]" + clone_inter.capitalize() + ': [/COLOR]' + intervenido_judicial + '. Reportar el problema en el foro', thumbnail=thumb_intervenido))
        del item.intervencion

    # If there has been a fail-over, I will comment
    if channel_alt and item.category_new != "newest":
        itemlist_fo.append(item.clone(action='', title="[COLOR yellow]" + item.category + '[/COLOR] [ALT ] en uso'))
        itemlist_fo.append(item.clone(action='', title="[COLOR yellow]" + channel_alt.capitalize() + '[/COLOR] inaccesible'))

    if len(itemlist_fo) > 0:
        itemlist = itemlist_fo + itemlist

    del item.category_new

    return (item, itemlist)


def post_tmdb_seasons(item, itemlist):
    logger.debug()

    """

    Past to manage the Seasons menu of a Series

    The activation key for this method is the variable item.season_colapse that puts the channel in the Listing Item.
    This variable will have to disappear when it is added to the Video Library so that episodes are analyzed in the traditional way.

    Review all the episodes produced in itemlist by "episodes" of the channel to extract the seasons. Puts a title for All Temps.
    Create a menu with the different seasons, as well as the titles of Title Update and Add to Video Library
    If there has been a Fail-over or a Judicial Intervention, it also announces it

    The method call from Episodes, before passing Itemlist pot TMDB, is:

        from lib import generictools
        item, itemlist = generictools.post_tmdb_seasons (item, itemlist)

    If there is only one season, please return the original itemlist so that the episodes are painted the traditional way

    """
    # logger.debug(item)

    season = 0
    itemlist_temporadas = []
    itemlist_fo = []

    if config.get_setting("no_pile_on_seasons", 'videolibrary') == 2:           # If you do not want to show seasonally, we are leaving ...
        if item.season_colapse:                                                 # We remove the indicator from the list by Seasons
            del item.season_colapse
        return (item, itemlist)

    # We restore values ​​if there has been a fail-over
    channel_alt = ''
    if item.channel == channel_py:
        if item.channel_alt:
            channel_alt = item.category
            item.category = item.channel_alt.capitalize()
            del item.channel_alt
    else:
        if item.channel_alt:
            channel_alt = item.channel
            item.channel = item.channel_alt
            item.category = item.channel_alt.capitalize()
            del item.channel_alt
    if item.url_alt:
        item.url = item.url_alt
        del item.url_alt

    # First we create a title for ALL Seasons
    # Passed by TMDB to Serial, for additional data
    try:
        tmdb.set_infoLabels(item, True)                     # TMDB of each Temp
    except:
        logger.error(traceback.format_exc())

    item_season = item.clone()
    if item_season.season_colapse:                          # We remove the indicator from the list by Seasons
        del item_season.season_colapse
    title = '** Todas las Temporadas'                       # We add title of ALL Seasons (traditional way)
    if item_season.infoLabels['number_of_episodes']:        # We put the number of episodes of the Series
        title += ' [%sx%s epi]' % (str(item_season.infoLabels['number_of_seasons']), str(item_season.infoLabels['number_of_episodes']))

    rating = ''                                             # We put the rating, if it is different from that of the Series
    if item_season.infoLabels['rating'] and item_season.infoLabels['rating'] != 0.0:
        try:
            rating = float(item_season.infoLabels['rating'])
            rating = round(rating, 1)
        except:
            logger.error(traceback.format_exc())
    if rating and rating == 0.0:
        rating = ''

    if not config.get_setting("unify"):                     # If Smart Titles NOT selected:
        title = '%s [COLOR yellow][%s][/COLOR] [%s] [COLOR limegreen][%s][/COLOR] [COLOR red]%s[/COLOR]' % (title, str(item_season.infoLabels['year']), rating, item_season.quality, str(item_season.language))
    else:                                                   # We fixed it a bit for Unify
        title = title.replace('[', '-').replace(']', '-').replace('.', ',').strip()
    title = title.replace("--", "").replace("[]", "").replace("()", "").replace("(/)", "").replace("[/]", "").strip()

    if config.get_setting("show_all_seasons", 'videolibrary'):
        itemlist_temporadas.append(item_season.clone(title=title, from_title_season_colapse=item.title))

    # We review all the episodes to detect the different seasons
    for item_local in itemlist:
        if item_local.contentSeason != season:
            season = item_local.contentSeason                       # If a different season is detected a title is prepared
            item_season = item.clone()
            item_season.contentSeason = item_local.contentSeason    # Season number is set to get better TMDB data
            item_season.title = 'Temporada %s' % item_season.contentSeason
            itemlist_temporadas.append(item_season.clone(from_title_season_colapse=item.title))

    # If there is more than one season it is followed, or it has been forced to list by seasons, if the original Itemlist is not returned
    if len(itemlist_temporadas) > 2 or config.get_setting("no_pile_on_seasons", 'videolibrary') == 0:
        for item_local in itemlist_temporadas:
            if "** Todas las Temporadas" in item_local.title:       # If it's the title of ALL Seasons, we ignore it
                continue

            # Passed by TMDB to the Seasons
            try:
                tmdb.set_infoLabels(item_local, True)               # TMDB of each Temp
            except:
                logger.error(traceback.format_exc())

            if item_local.infoLabels['temporada_air_date']:         # Temp issue date
                item_local.title += ' [%s]' % str(scrapertools.find_single_match(str(item_local.infoLabels['temporada_air_date']), r'\/(\d{4})'))

            #rating = ''                                            # We put the rating, if it is different from that of the Series
            #if item_local.infoLabels['rating'] and item_local.infoLabels['rating'] != 0.0:
            #    try:
            #        rating = float(item_local.infoLabels['rating'])
            #        rating = round(rating, 1)
            #    except:
            #        logger.error(traceback.format_exc())
            #if rating and rating > 0.0:
            #    item_local.title += ' [%s]' % str(rating)

            if item_local.infoLabels['temporada_num_episodios']:    # No. of Temp Episodes
                item_local.title += ' [%s epi]' % str(item_local.infoLabels['temporada_num_episodios'])

            if not config.get_setting("unify"):                     # If Smart Titles NOT selected:
                item_local.title = '%s [COLOR limegreen][%s][/COLOR] [COLOR red]%s[/COLOR]' % (item_local.title, item_local.quality, str(item_local.language))
            else:                                                   # We fixed it a bit for Unify
                item_local.title = item_local.title.replace("[", "-").replace("]", "-").replace(".", ",").replace("GB", "G B").replace("Gb", "G b").replace("gb", "g b").replace("MB", "M B").replace("Mb", "M b").replace("mb", "m b")
            item_local.title = item_local.title.replace("--", "").replace("[]", "").replace("()", "").replace("(/)", "").replace("[/]", "").strip()

            #logger.debug(item_local)

    else:                                   # If there is more than one season it is followed, if the original Itemlist is not returned
        if item.season_colapse:
            del item.season_colapse
        return (item, itemlist)

    # We allow the updating of titles, either for immediate use, or to add to the video library
    itemlist_temporadas.append(item.clone(title="** [COLOR yelow]Actualizar Títulos - vista previa videoteca[/COLOR] **", action="actualizar_titulos", tmdb_stat=False, from_action=item.action, from_title_tmdb=item.title, from_update=True))

    # It is a standard channel, just a line of Add to Video Library
    title = ''
    if item.infoLabels['status'] and item.infoLabels['status'].lower() == "ended":
        title += ' [TERMINADA]'
    itemlist_temporadas.append(item_season.clone(title="[COLOR yellow]Añadir esta serie a videoteca-[/COLOR]" + title, action="add_serie_to_library", extra="episodios", add_menu=True))

    # If judicial intervention, I warn !!!
    if item.intervencion:
        for clone_inter, autoridad in item.intervencion:
            thumb_intervenido = get_thumb(autoridad)
            itemlist_fo.append(item.clone(action='', title="[COLOR yellow]" + clone_inter.capitalize() + ': [/COLOR]' + intervenido_judicial + '. Reportar el problema en el foro', thumbnail=thumb_intervenido))
        del item.intervencion

    # If there has been a fail-over, I will comment
    if channel_alt:
        itemlist_fo.append(item.clone(action='', title="[COLOR yellow]" + channel_alt.capitalize() + '[/COLOR] [ALT ] en uso'))
        itemlist_fo.append(item.clone(action='', title="[COLOR yellow]" + item.category.capitalize() + '[/COLOR] inaccesible'))

    if len(itemlist_fo) > 0:
        itemlist_temporadas = itemlist_fo + itemlist_temporadas

    return (item, itemlist_temporadas)


def post_tmdb_episodios(item, itemlist):
    logger.debug()
    itemlist_fo = []

    """

   Last for makeup of the titles obtained from TMDB in Episodes.

    InfoLabel takes all the data of interest and places them in different variables, mainly title
    so that it is compatible with Unify, and if there are no Smart Titles, so that the format is the most
    similar to Unify.

    Keep track of the num. of episodes per season, trying to fix Web and TMDB errors

    The method call from Episodes, after passing Itemlist pot TMDB, is:

        from lib import generictools
        item, itemlist = generictools.post_tmdb_episodes (item, itemlist)

    """
    # logger.debug(item)

    modo_serie_temp = ''
    if config.get_setting('seleccionar_serie_temporada', item.channel) >= 0:
        modo_serie_temp = config.get_setting('seleccionar_serie_temporada', item.channel)
    modo_ultima_temp = ''
    if config.get_setting('seleccionar_ult_temporadda_activa', item.channel) is True or config.get_setting('seleccionar_ult_temporadda_activa', item.channel) is False:
        modo_ultima_temp = config.get_setting('seleccionar_ult_temporadda_activa', item.channel)

    # Initiates variables to control the number of episodes per season
    num_episodios = 1
    num_episodios_lista = []
    for i in range(0, 50):  num_episodios_lista += [0]
    num_temporada = 1
    num_temporada_max = 99
    num_episodios_flag = True

    # We restore the Season number to make the choice of Video Library more flexible
    contentSeason = item.contentSeason
    if item.contentSeason_save:
        contentSeason = item.contentSeason_save
        item.contentSeason = item.contentSeason_save
        del item.contentSeason_save

    # We adjust the category name
    if item.channel == channel_py:
        item.category = scrapertools.find_single_match(item.url, r'http.?\:\/\/(?:www.)?(\w+)\.\w+\/').capitalize()

    # We restore values ​​if there has been a fail-over
    channel_alt = ''
    if item.channel == channel_py:
        if item.channel_alt:
            channel_alt = item.category
            item.category = item.channel_alt.capitalize()
            del item.channel_alt
    else:
        if item.channel_alt:
            channel_alt = item.channel
            item.channel = item.channel_alt
            item.category = item.channel_alt.capitalize()
            del item.channel_alt
    if item.url_alt:
        item.url = item.url_alt
        del item.url_alt
    if item.title_from_channel:
        del item.title_from_channel
    if item.ow_force:
        del item.ow_force
    if item.season_colapse:
        del item.season_colapse
    if item.from_action:
        del item.from_action
    if item.from_channel:
        del item.from_channel
    if item.library_filter_show:
        del item.library_filter_show
    if item.channel_host:
        del item.channel_host

    for item_local in itemlist:                             # We go through the Itemlist generated by the channel
        if item_local.add_videolibrary:
            del item_local.add_videolibrary
        if item_local.add_menu:
            del item_local.add_menu
        if item_local.contentSeason_save:
            del item_local.contentSeason_save
        if item_local.title_from_channel:
            del item_local.title_from_channel
        if item_local.library_playcounts:
            del item_local.library_playcounts
        if item_local.library_urls:
            del item_local.library_urls
        if item_local.path:
            del item_local.path
        if item_local.nfo:
            del item_local.nfo
        if item_local.update_last:
            del item_local.update_last
        if item_local.update_next:
            del item_local.update_next
        if item_local.channel_host:
            del item_local.channel_host
        if item_local.intervencion:
            del item_local.intervencion
        if item_local.ow_force:
            del item_local.ow_force
        if item_local.season_colapse:
            del item_local.season_colapse
        if item_local.from_action:
            del item_local.from_action
        if item_local.from_channel:
            del item_local.from_channel
        if item_local.emergency_urls and isinstance(item_local.emergency_urls, dict):
            del item_local.emergency_urls
        if item_local.library_filter_show:
            del item_local.library_filter_show
        if item_local.extra2:
            del item_local.extra2
        item_local.wanted = 'xyz'
        del item_local.wanted
        item_local.text_color = 'xyz'
        del item_local.text_color
        item_local.tmdb_stat = 'xyz'
        del item_local.tmdb_stat
        item_local.totalItems = 'xyz'
        del item_local.totalItems
        item_local.unify = 'xyz'
        del item_local.unify
        item_local.title = re.sub(r'(?i)online|descarga|downloads|trailer|videoteca|gb|autoplay', '', item_local.title).strip()

        # logger.debug(item_local)

        # We adjust the category name if it is a clone of NewPct1
        if item_local.channel == channel_py:
            item_local.category = scrapertools.find_single_match(item_local.url, r'http.?\:\/\/(?:www.)?(\w+)\.\w+\/').capitalize()

        # We restore values ​​for each Episode if there has been a fail-over of a NewPct1 clone
        if item_local.channel == channel_py:
            if item_local.channel_alt:
                item_local.category = item_local.channel_alt
                del item_local.channel_alt
        else:
            if item_local.channel_alt:
                item_local.channel = item_local.channel_alt
                del item_local.channel_alt
        if item_local.url_alt:
            host_act = scrapertools.find_single_match(item_local.url, r':\/\/(.*?)\/')
            host_org = scrapertools.find_single_match(item_local.url_alt, r':\/\/(.*?)\/')
            item_local.url = item_local.url.replace(host_act, host_org)
            del item_local.url_alt

        # If you are updating video library of a NewPct1 series, we restore the channel with the name of the clone
        if item_local.channel == channel_py and (item.library_playcounts or item.add_videolibrary):
            item_local.channel = scrapertools.find_single_match(item_local.url, r'http.?\:\/\/(?:www.)?(\w+)\.\w+\/')

        # If the series title is verified in TMDB, it tries to discover the out of range episodes,
        # which are probable errors of the Web
        if item.tmdb_stat:
            if item_local.infoLabels['number_of_seasons']:
                # If the season num is out of control, it gets 0, and itemlist is reclassified
                if item_local.contentSeason > item_local.infoLabels['number_of_seasons'] + 1:
                    logger.error("ERROR 07: EPISODES: Season number out of range " + " / SEASON: " + str(item_local.contentSeason) + " / " + str(item_local.contentEpisodeNumber) + " / MAX_SEASONS: " + str(item_local.infoLabels['number_of_seasons']) + " / SEASON_LIST: " + str(num_episodios_lista))
                    item_local.contentSeason = 0
                    itemlist = sorted(itemlist, key=lambda it: (int(it.contentSeason), int(it.contentEpisodeNumber)))
                else:
                    num_temporada_max = item_local.infoLabels['number_of_seasons']
            else:
                if item_local.contentSeason > num_temporada_max + 1:
                    logger.error("ERROR 07: EPISODES: Season number out of range " + " / SEASON: " + str(item_local.contentSeason) + " / " + str(item_local.contentEpisodeNumber) + " / MAX_SEASONS: " + str(num_temporada_max) + " / SEASON_LIST: " + str(num_episodios_lista))
                    item_local.contentSeason = 0
                    itemlist = sorted(itemlist, key=lambda it: (int(it.contentSeason), int(it.contentEpisodeNumber)))

        # We save in number of episodes of the season
        try:
            if num_temporada != item_local.contentSeason:
                num_temporada = item_local.contentSeason
                num_episodios = 0
            if item_local.infoLabels['temporada_num_episodios'] and int(item_local.infoLabels['temporada_num_episodios']) > int(num_episodios):
                num_episodios = item_local.infoLabels['temporada_num_episodios']
        except:
            num_episodios = 0
            logger.error(traceback.format_exc())

        # We prepare the video Rating
        rating = ''
        try:
            if item_local.infoLabels['rating'] and item_local.infoLabels['rating'] != 0.0:
                rating = float(item_local.infoLabels['rating'])
                rating = round(rating, 1)
                if rating == 0.0:
                    rating = ''
        except:
            logger.error(traceback.format_exc())

        # If TMDB has not found the video we clean the year
        if item_local.infoLabels['year'] == "-":
            item_local.infoLabels['year'] = ''
            item_local.infoLabels['aired'] = ''
        # For Episodes, I take the year of exposure and not the year of beginning of the series
        elif item_local.infoLabels['aired']:
            item_local.infoLabels['year'] = scrapertools.find_single_match(str(item_local.infoLabels['aired']), r'\/(\d{4})')

        # We clean quality of original titles that may have been cast
        if item_local.infoLabels['originaltitle'].lower() in item_local.quality.lower():
            item_local.quality = re.sub(item_local.infoLabels['originaltitle'], '', item_local.quality)
            # item_local.quality = re.sub(item_local.infoLabels['originaltitle'], '', item_local.quality, flags=re.IGNORECASE)

        # If the title of the episode is not there, but it is in "title", we rescue it
        if not item_local.infoLabels['episodio_titulo'] and item_local.infoLabels['title'].lower() != item_local.infoLabels['tvshowtitle'].lower():
            item_local.infoLabels['episodio_titulo'] = item_local.infoLabels['title']
        item_local.infoLabels['episodio_titulo'] = item_local.infoLabels['episodio_titulo'].replace('GB', 'G B').replace('MB', 'M B')

        # We prepare the title to be compatible with Add Series to Video Library
        if "Temporada" in item_local.title:             # We make "Season" compatible with Unify
            item_local.title = '%sx%s al 99 -' % (str(item_local.contentSeason), str(item_local.contentEpisodeNumber))
        if " al " in item_local.title:                  # If they are multiple episodes, we put a series name
            if " al 99" in item_local.title.lower():    # Full season. We are looking for the total number of episodes of the season
                item_local.title = item_local.title.replace("99", str(num_episodios))
            item_local.title = '%s %s' % (item_local.title, item_local.contentSerieName)
            item_local.infoLabels['episodio_titulo'] = '%s - %s [%s] [%s]' % (scrapertools.find_single_match(item_local.title, r'(al \d+)'), item_local.contentSerieName, item_local.infoLabels['year'], rating)

        elif item_local.infoLabels['episodio_titulo']:
            item_local.title = '%s %s' % (item_local.title, item_local.infoLabels['episodio_titulo'])
            item_local.infoLabels['episodio_titulo'] = '%s [%s] [%s]' % (item_local.infoLabels['episodio_titulo'], item_local.infoLabels['year'], rating)

        else:                                           # If there is no episode title, we will put the name of the series
            item_local.title = '%s %s' % (item_local.title, item_local.contentSerieName)
            item_local.infoLabels['episodio_titulo'] = '%s [%s] [%s]' % (item_local.contentSerieName, item_local.infoLabels['year'], rating)

        # We compose the final title, although with Unify you will use infoLabels ['episode_title']
        item_local.infoLabels['title'] = item_local.infoLabels['episodio_titulo']
        item_local.title = item_local.title.replace("[", "-").replace("]", "-")
        item_local.title = '%s [%s] [%s] [COLOR limegreen][%s][/COLOR] [COLOR red]%s[/COLOR]' % (item_local.title, item_local.infoLabels['year'], rating, item_local.quality, str(item_local.language))

        # We remove empty fields
        item_local.infoLabels['episodio_titulo'] = item_local.infoLabels['episodio_titulo'].replace("[]", "").strip()
        item_local.infoLabels['title'] = item_local.infoLabels['title'].replace("[]", "").strip()
        item_local.title = item_local.title.replace("[]", "").strip()
        item_local.title = re.sub(r'\s?\[COLOR \w+\]\[\[?-?\s?\]?\]\[\/COLOR\]', '', item_local.title).strip()
        item_local.title = re.sub(r'\s?\[COLOR \w+\]-?\s?\[\/COLOR\]', '', item_local.title).strip()
        item_local.title = item_local.title.replace(".", ",").replace("GB", "G B").replace("Gb", "G b").replace("gb", "g b").replace("MB", "M B").replace("Mb", "M b").replace("mb", "m b")

        # If the information of num. total episodes of TMDB is not correct, we try to calculate it
        if num_episodios < item_local.contentEpisodeNumber:
            num_episodios = item_local.contentEpisodeNumber
        if num_episodios > item_local.contentEpisodeNumber:
            item_local.infoLabels['temporada_num_episodios'] = num_episodios
            num_episodios_flag = False
        if num_episodios and not item_local.infoLabels['temporada_num_episodios']:
            item_local.infoLabels['temporada_num_episodios'] = num_episodios
            num_episodios_flag = False
        try:
            num_episodios_lista[item_local.contentSeason] = num_episodios
        except:
            logger.error(traceback.format_exc())

        #logger.debug("title: " + item_local.title + " / url: " + item_local.url + " / calidad: " + item_local.quality + " / Season: " + str(item_local.contentSeason) + " / EpisodeNumber: " + str(item_local.contentEpisodeNumber) + " / num_episodios_lista: " + str(num_episodios_lista) + str(num_episodios_flag))
        #logger.debug(item_local)

    # If you are updating video library of a NewPct1 series, we restore the channel with the name of the clone
    if item.channel == channel_py and (item.library_playcounts or item.add_videolibrary):
        item.channel = scrapertools.find_single_match(item.url, r'http.?\:\/\/(?:www.)?(\w+)\.\w+\/')

    # After reviewing each episode, we close with the footer
    # First we update all episodes with their maximum number of episodes per season
    try:
        if not num_episodios_flag:  # If the number of episodes is not reported, we update episodes of the entire series
            for item_local in itemlist:
                item_local.infoLabels['temporada_num_episodios'] = int(num_episodios_lista[item_local.contentSeason])
    except:
        logger.error("ERROR 07: EPISODES: Season number out of range" + " / SEASON: " + str(item_local.contentSeason) + " / " + str(item_local.contentEpisodeNumber) + " / MAX_SEASONS: " + str(num_temporada_max) + " / SEASON_LIST: " + str(num_episodios_lista))
        logger.error(traceback.format_exc())

    # We allow the updating of titles, either for immediate use, or to add to the video library
    itemlist.append(item.clone(title="** Update Titles - video library preview **", action="actualizar_titulos", tmdb_stat=False, from_action=item.action, from_title_tmdb=item.title, from_update=True))

    # Delete num. Season if you do not come from the Add to Video Library menu and you are not updating the Video Library
    if not item.library_playcounts:                         # if you are not updating the Video Library
        if modo_serie_temp != '':                           # and can change to series-season
            if item.contentSeason and not item.add_menu:
                del item.infoLabels['season']               # The decision to put it or not is made in the menu area

    # We put the title of Add to the Video Library, with the no. of episodes from the last season and the status of the Series
    if config.get_videolibrary_support() and len(itemlist) > 1:
        item_local = itemlist[-2]
        title = ''

        if item_local.infoLabels['temporada_num_episodios']:
            title += ' [Temp. de %s ep.]' % item_local.infoLabels['temporada_num_episodios']

        if item_local.infoLabels['status'] and item_local.infoLabels['status'].lower() == "ended":
            title += ' [TERMINADA]'

        if item_local.quality:      #L The Video Library does not take the quality of the episode, but of the series. I put of the episode
            item.quality = item_local.quality

        if modo_serie_temp != '':
            # We are in a channel that can select between managing complete Series or by Season
            # It will have a line to Add the complete Series and another to Add only the current Season

            if item.action == 'get_seasons':                    # if it is update from video library, standard title
                # If there is a new Season, it is activated as the current one
                if item.library_urls[item.channel] != item.url and (item.contentType == "season" or modo_ultima_temp):
                    item.library_urls[item.channel] = item.url  # The url is updated pointing to the last Season
                    try:
                        from core import videolibrarytools      # Update url in .nfo is forced
                        itemlist_fake = []                      # An empty Itemlist is created to update only the .nfo
                        videolibrarytools.save_tvshow(item, itemlist_fake)      # The .nfo is updated
                    except:
                        logger.error("ERROR 08: EPISODES: Unable to update the URL to the new Season")
                        logger.error(traceback.format_exc())
                itemlist.append(item.clone(title="[COLOR yellow]Add this Series to Video Library-[/COLOR]" + title, action="add_serie_to_library"))

            elif modo_serie_temp == 1:      # if it is Series we give the option to save the last season or the complete series
                itemlist.append(item.clone(title="[COLOR yellow]Add last Temp. to Video Library-[/COLOR]" + title, action="add_serie_to_library", contentType="season", contentSeason=contentSeason, url=item_local.url, add_menu=True))
                itemlist.append(item.clone(title="[COLOR yellow]Add this Series to Video Library-[/COLOR]" + title, action="add_serie_to_library", contentType="tvshow", add_menu=True))

            else:                           # if not, we give the option to save the current season or the complete series
                itemlist.append(item.clone(title="[COLOR yellow]Add this Series to Video Library-[/COLOR]" + title, action="add_serie_to_library", contentType="tvshow", add_menu=True))
                if item.add_videolibrary and not item.add_menu:
                    item.contentSeason = contentSeason
                itemlist.append(item.clone(title="[COLOR yellow]Aadd this Temp. to Video Library-[/COLOR]" + title, action="add_serie_to_library", contentType="season", contentSeason=contentSeason, add_menu=True))

        else:   # It is a standard channel, just a line of Add to Video Library
            itemlist.append(item.clone(title="[COLOR yellow]Add this series to video library-[/COLOR]" + title, action="add_serie_to_library", extra="episodios", add_menu=True))

    # If judicial intervention, I warn !!!
    if item.intervencion:
        for clone_inter, autoridad in item.intervencion:
            thumb_intervenido = get_thumb(autoridad)
            itemlist_fo.append(item.clone(action='', title="[COLOR yellow]" + clone_inter.capitalize() + ': [/COLOR]' + intervenido_judicial + '. Report the problem in the forum', thumbnail=thumb_intervenido))
        del item.intervencion

    # If there has been a fail-over, I will comment
    if channel_alt:
        itemlist_fo.append(item.clone(action='', title="[COLOR yellow]" + channel_alt.capitalize() + '[/COLOR] [ALT ] In use'))
        itemlist_fo.append(item.clone(action='', title="[COLOR yellow]" + item.category.capitalize() + '[/COLOR] Inaccessible'))

    if len(itemlist_fo) > 0:
        itemlist = itemlist_fo + itemlist

    if item.add_videolibrary:                               # We are Adding to the Video Library.
        del item.add_videolibrary                           # We already delete the indicator
        if item.add_menu:                                   # Option that warns if it has been added to the Video Library
            del item.add_menu                               # from the Episodes page or from the Contextual Menu

    # logger.debug(item)

    return (item, itemlist)


def post_tmdb_findvideos(item, itemlist):
    logger.debug()

    """

    Call to create a pseudo title with all the relevant data from the video.

    InfoLabel takes all the data of interest and places them in different variables, mainly the title. Keep track of the num. of episodes per season

    The call to the method from Findvideos, at the beginning, is:

        from lib import generictools
        item, itemlist = generictools.post_tmdb_findvideos (item, itemlist)

    In Itemlist it returns an Item with the pseudo title. There the channel will add the rest.

    """
    # logger.debug(item)

    # Know if we are in a popup window launched from a bullet in the main menu,
    # with the function "play_from_library"
    item.unify = False
    Window_IsMedia = False
    try:
        import xbmc
        if xbmc.getCondVisibility('Window.IsMedia') == 1:
            Window_IsMedia = True
            item.unify = config.get_setting("unify")
    except:
        item.unify = config.get_setting("unify")
        logger.error(traceback.format_exc())

    if item.contentSeason_save:                                 # We restore the num. seasonal
        item.contentSeason = item.contentSeason_save
        del item.contentSeason_save

    if item.library_filter_show:
        del item.library_filter_show

    # We save the information of max num. of episodes per season after TMDB
    num_episodios = item.contentEpisodeNumber
    if item.infoLabels['temporada_num_episodios'] and item.contentEpisodeNumber <= item.infoLabels['temporada_num_episodios']:
        num_episodios = item.infoLabels['temporada_num_episodios']

    # Get updated video information. In a second TMDB reading it gives more information than in the first
    #if not item.infoLabels['tmdb_id'] or (not item.infoLabels['episodio_titulo'] and item.contentType == 'episode'):
    #    tmdb.set_infoLabels(item, True)
    #elif (not item.infoLabels['tvdb_id'] and item.contentType == 'episode') or item.contentChannel == "videolibrary":
    #    tmdb.set_infoLabels(item, True)
    try:
        tmdb.set_infoLabels(item, True)                         # TMDB of each Temp
    except:
        logger.error(traceback.format_exc())
    # We restore the information of max num. of episodes per season after TMDB
    try:
        if item.infoLabels['temporada_num_episodios']:
            if int(num_episodios) > int(item.infoLabels['temporada_num_episodios']):
                item.infoLabels['temporada_num_episodios'] = num_episodios
        else:
            item.infoLabels['temporada_num_episodios'] = num_episodios
    except:
        logger.error(traceback.format_exc())

    # We adjust the category name
    if item.channel == channel_py:
        category = scrapertools.find_single_match(item.url, r'http.?\:\/\/(?:www.)?(\w+)\.\w+\/').capitalize()
        if category:
            item.category = category

    if item.armagedon:                                          #Es una situación catastrófica?
        itemlist.append(item.clone(action='', title=item.category + ': [COLOR hotpink]Using emergency links[/COLOR]'))

    # We remove the category or title name, if you have it
    if item.contentTitle:
        item.contentTitle = re.sub(r' -%s-' % item.category, '', item.contentTitle)
        item.title = re.sub(r' -%s-' % item.category, '', item.title)

    # We clean up the year and episode ratings
    if item.infoLabels['episodio_titulo']:
        item.infoLabels['episodio_titulo'] = re.sub(r'\s?\[.*?\]', '', item.infoLabels['episodio_titulo'])
        item.infoLabels['episodio_titulo'] = re.sub(r'\s?\(.*?\)', '', item.infoLabels['episodio_titulo'])
        item.infoLabels['episodio_titulo'] = item.infoLabels['episodio_titulo'].replace(item.contentSerieName, '')
    if item.infoLabels['aired'] and item.contentType == "episode":
        item.infoLabels['year'] = scrapertools.find_single_match(str(item.infoLabels['aired']), r'\/(\d{4})')

    rating = ''     # We put the rating
    try:
        if item.infoLabels['rating'] and item.infoLabels['rating'] != 0.0:
            rating = float(item.infoLabels['rating'])
            rating = round(rating, 1)
            if rating == 0.0:
                    rating = ''
    except:
        logger.error(traceback.format_exc())

    if item.quality.lower() in ['gb', 'mb']:
        item.quality = item.quality.replace('GB', 'G B').replace('Gb', 'G b').replace('MB', 'M B').replace('Mb', 'M b')

    # I'm looking for "duration" in infoLabels
    tiempo = 0
    if item.infoLabels['duration']:
        try:
            if config.get_platform(True)['num_version'] < 18 or not Window_IsMedia:
                tiempo = item.infoLabels['duration']
            elif xbmc.getCondVisibility('Window.IsMedia') == 1:
                item.quality = re.sub(r'\s?\[\d+:\d+\ h]', '', item.quality)
            else:
                tiempo = item.infoLabels['duration']
        except:
            tiempo = item.infoLabels['duration']
            logger.error(traceback.format_exc())

    elif item.contentChannel == 'videolibrary':                         # No, does it come from the Video Library? we look in the DB
    # I read from the Kodi BD the length of the movie or episode. In "from_fields" you can put the columns you want
        nun_records = 0
        try:
            if item.contentType == 'movie':
                nun_records, records = get_field_from_kodi_DB(item, from_fields='c11')  # Leo from BD Kodi movie length
            else:
                nun_records, records = get_field_from_kodi_DB(item, from_fields='c09')  # Leo from BD Kodi episode length
        except:
            logger.error(traceback.format_exc())
        if nun_records > 0:                                                         # Are there records?
            # It is an array, I look for the record field: add in the FOR a fieldX for a new column
            for strFileName, field1 in records:
                tiempo = field1

    try:                                                                            # we calculate the time in hh: mm
        tiempo_final = int(tiempo)                                                  # I convert it to int, but it can be null
        if tiempo_final > 0:                                                        # If the time is 0, we pass
            if tiempo_final > 700:                                                  # If it's in seconds
                tiempo_final = tiempo_final / 60                                    # I transform it into minutes
            horas = tiempo_final / 60                                               # I transform it into hours
            resto = tiempo_final - (horas * 60)                                     # I keep the remaining minutes of the hour
            if not scrapertools.find_single_match(item.quality, r'(\[\d+:\d+)'):     # if it already has the duration, we pass
                item.quality += ' [/COLOR][COLOR white][%s:%s h]' % (str(horas).zfill(2), str(resto).zfill(2))     # I add it to Server Quality
    except:
        logger.error(traceback.format_exc())

    # We adjust the category name
    if item.channel != channel_py:
        item.category = item.channel.capitalize()

    # We specially format the title for an episode
    title = ''
    title_gen = ''
    if item.contentType == "episode":                   # Series
        title = '%sx%s' % (str(item.contentSeason), str(item.contentEpisodeNumber).zfill(2))    # Season and Episode
        if item.infoLabels['temporada_num_episodios']:
            title = '%s (de %s)' % (title, str(item.infoLabels['temporada_num_episodios']))     # Total Episodes

        # If they are multiple episodes, and it comes from Video Library, we put series name
        if (" al " in item.title or " Al " in item.title) and not "al " in item.infoLabels['episodio_titulo']:
            title = '%s al %s - ' % (title, scrapertools.find_single_match(item.title, r'[al|Al] (\d+)'))
        else:
            title = '%s %s' % (title, item.infoLabels['episodio_titulo'])               # Title Episode
        title_gen = '%s, ' % title

    if item.contentType == "episode" or item.contentType == "season":                   # Series or Seasons
        title_gen += '%s [COLOR yellow][%s][/COLOR] [%s] [COLOR limegreen][%s][/COLOR] [COLOR red]%s[/COLOR] [%s]' % (item.contentSerieName, item.infoLabels['year'], rating, item.quality, str(item.language), scrapertools.find_single_match(item.title, r'\s\[(\d+,?\d*?\s\w[b|B])\]'))                                      # Rating, Quality, Language, Size
        if item.infoLabels['status'] and item.infoLabels['status'].lower() == "ended":
            title_gen = '[TERM.] %s' % title_gen        # It marks when the Series is finished and there will be no more production
        item.title = title_gen

    else:                                               # Films
        title = item.title
        title_gen = item.title

    # We clean empty labels
    title_gen = re.sub(r'\s?\[COLOR \w+\]\[\[?\s?\]?\]\[\/COLOR\]', '', title_gen).strip()  # We remove empty labels
    title_gen = re.sub(r'\s?\[COLOR \w+\]\s?\[\/COLOR\]', '', title_gen).strip()            # We remove empty colors
    title_gen = title_gen.replace(" []", "").strip()                                    # We remove empty labels
    title_videoteca = title_gen                                                         # We save the title for Video Library

    if not item.unify:                                                      # If Smart Titles NOT selected:
        title_gen = '**- [COLOR gold]Enlaces Ver: [/COLOR]%s[COLOR gold] -**[/COLOR]' % (title_gen)
    else:                                                                   # If Smart Titles YES selected:
        title_gen = '[COLOR gold]Enlaces Ver: [/COLOR]%s' % (title_gen)

    if item.channel_alt:
        title_gen = '[COLOR yellow]%s [/COLOR][ALT]: %s' % (item.category.capitalize(), title_gen)
    # elif (config.get_setting("quit_channel_name", "videolibrary") == 1 or item.channel == channel_py) and item.contentChannel == "videolibrary":
    else:
        title_gen = '[COLOR white]%s: %s' % (item.category.capitalize(), title_gen)

    # If judicial intervention, I warn !!!
    if item.intervencion:
        for clone_inter, autoridad in item.intervencion:
            thumb_intervenido = get_thumb(autoridad)
            itemlist.append(item.clone(action='', title="[COLOR yellow]" + clone_inter.capitalize() + ': [/COLOR]' + intervenido_judicial + '. Reportar el problema en el foro', thumbnail=thumb_intervenido))
        del item.intervencion

    # We paint the pseudo-title with all the information available from the video
    itemlist.append(item.clone(action="", server = "", title=title_gen))		# Title with all the data of the video

    if item.action == 'show_result':                                            # Comes from a global search
        channel = item.channel.capitalize()
        if item.from_channel == channel_py or item.channel == channel_py:
            channel = item.category
        elif item.from_channel:
            channel = item.from_channel.capitalize()
        item.quality = '[COLOR yellow][%s][/COLOR] %s' % (channel, item.quality)

    # we added the option to Add to Video Library for movies (no series)
    if (item.contentType == 'movie' or item.contentType == 'season') and item.contentChannel != "videolibrary":
        # We allow the updating of titles, either for immediate use, or to add to the video library
        itemlist.append(item.clone(title="** [COLOR yelow]Actualizar Títulos - vista previa videoteca[/COLOR] **", action="actualizar_titulos", extra="peliculas", tmdb_stat=False, from_action=item.action, from_title_tmdb=item.title, from_update=True))

    if item.contentType == 'movie' and item.contentChannel != "videolibrary":
        itemlist.append(item.clone(title="**-[COLOR yellow] Añadir a la videoteca [/COLOR]-**", action="add_pelicula_to_library", extra="peliculas", from_action=item.action, from_title_tmdb=item.title))

    # We added the option to watch trailers
    if item.contentChannel != "videolibrary":
        itemlist.append(item.clone(channel="trailertools", title="**-[COLOR magenta] Buscar Trailer [/COLOR]-**", action="buscartrailer", context=""))

    # logger.debug(item)

    return (item, itemlist)


def get_field_from_kodi_DB(item, from_fields='*', files='file'):
    logger.debug()
    """

   Call to read from the Kodi DB the input fields received (from_fields, by default "*") of the video indicated in Item
    Obviously this only works with Kodi and if the movie or series is listed in the Alpha and Kodi Video Libraries.
    You can request that the search be done by files (default), or by folder (series)

    The call is:
        nun_records, records = generictools.get_field_from_kodi_DB (item, from_fields = 'cXX [, cYY, ...]' [, files = 'file | folder'])

    Returns the num of records found and the records. It is important for the caller to verify that "nun_records> 0" before processing "records"

    """

    FOLDER_MOVIES = config.get_setting("folder_movies")
    FOLDER_TVSHOWS = config.get_setting("folder_tvshows")
    VIDEOLIBRARY_PATH = config.get_videolibrary_config_path()
    VIDEOLIBRARY_REAL_PATH = config.get_videolibrary_path()

    if item.contentType == 'movie':                             # I add the folder corresponding to the path of the Video Library
        path = filetools.join(VIDEOLIBRARY_REAL_PATH, FOLDER_MOVIES)
        path2 = filetools.join(VIDEOLIBRARY_PATH, FOLDER_MOVIES)
        folder = FOLDER_MOVIES
    else:
        path = filetools.join(VIDEOLIBRARY_REAL_PATH, FOLDER_TVSHOWS)
        path2 = filetools.join(VIDEOLIBRARY_PATH, FOLDER_TVSHOWS)
        folder = FOLDER_TVSHOWS

    raiz, carpetas, ficheros = filetools.walk(path).next()      # ready the series or movies in the Video Library
    carpetas = [filetools.join(path, f) for f in carpetas]      # I add the content folder to the path
    for carpeta in carpetas:                                    # I search the selected content in the folder list
        if item.contentType == 'movie' and (item.contentTitle.lower() in carpeta or item.contentTitle in carpeta):                                                        # Films?
            path = carpeta                                      # We store the folder in the path
            break
        elif item.contentType in ['tvshow', 'season', 'episode'] and (item.contentSerieName.lower() in carpeta or item.contentSerieName in carpeta):                           # Series?
            path = carpeta                                      #Almacenamos la carpeta en el path
            break

    path2 += '/%s/' % scrapertools.find_single_match(path, r'%s.(.*?\s\[.*?\])' % folder) # We add the Series or Movies folder, Android format
    file_search = '%'                                           # By default it looks for all the files in the folder
    if files == 'file':                                         # If a file is requested (default), it is searched
        if item.contentType == 'episode':                       # If it is an episode, put the name, if not leave%
            file_search = '%sx%s.strm' % (item.contentSeason, str(item.contentEpisodeNumber).zfill(2))  # Name for episodes

    if "\\" in path:                                            # We adjust the / depending on the platform
        path = path.replace("/", "\\")
        path += "\\"                                            # We end the path with a /
    else:
        path += "/"

    if FOLDER_TVSHOWS in path:                                  # I check if it is CINEMA or SERIES
        contentType = "episode_view"                            # I mark the Kodi Video BBDD table
    else:
        contentType = "movie_view"                              # I mark the Kodi Video BBDD table
    path1 = path.replace("\\\\", "\\")                          # for SQL I just need the folder
    path2 = path2.replace("\\", "/")                            # Format no Windows

    # Let's execute the SQL statement
    if not from_fields:
        from_fields = '*'
    else:
        from_fields = 'strFileName, %s' % from_fields           # at least two fields, because one only generates strange things
    sql = 'select %s from %s where (strPath like "%s" or strPath like "%s") and strFileName like "%s"' % (from_fields, contentType, path1, path2, file_search)
    nun_records = 0
    records = None
    try:
        if config.is_xbmc():
            from platformcode import xbmc_videolibrary
            nun_records, records = xbmc_videolibrary.execute_sql_kodi(sql)      # SQL execution
            if nun_records == 0:                                                # is there an error?
                logger.error("SQL error: " + sql + ": 0 records")       # It will not be listed or there is an error in the SQL
    except:
        logger.error(traceback.format_exc())

    return (nun_records, records)


def fail_over_newpct1(item, patron, patron2=None, timeout=None):
    logger.debug()
    import ast

    """

    Call to find an alternative website to a downed channel, clone of NewPct1

    We create an array with the data of the alternative channels. The tuple data is:

        - active = 0.1 Indicates if the channel is not active or if it is
        - channel name of the alternative channel
        - channel_host host of the alternative channel, used to replace part of the url
        - contentType indicates what type of content the new channel supports in fail-overs
        - action_excluded lists the actions that are excluded for that channel

    The method call from the beginning of Submenu, Search_List, Episodes and Findvideos, is:

        from lib import generictools
        item, data = generictools.fail_over_newpct1 (item, pattern [, pattern2 =] [, timeout =])

        - Entry: pattern: with this pattern it is possible to verify if the data of the new website is good
        - Input (optional): pattern 2: optional second pattern
        - Entry (optional): timeout: maximum wait value in page download. Default 3
        - Input (optional): pattern = True: asks to only verify if the channel in use is active, if not, offers another
        - Output: data: returns the data of the new website. If it returns empty it is that no alternative was found

    """
    # logger.debug(item)

    if timeout == None:
        timeout = config.get_setting('clonenewpct1_timeout_downloadpage', channel_py)           # Timeout downloadpage
    if timeout == 0: timeout = None
    if item.action == "search" or item.action == "listado_busqueda": timeout = timeout * 2      # More time for searches

    data = ''
    channel_failed = ''
    url_alt = []
    item.category = scrapertools.find_single_match(item.url, r'http.?\:\/\/(?:www.)?(\w+)\.\w+\/').capitalize()
    if not item.extra2:
        item.extra2 = 'z9z8z7z6z5'

    patron_alt = ''
    verify_torrent = ''
    if patron is not True and '|' in patron:                            # We check if there are two alternative patterns
        try:
            verify_torrent, patron1, patron_alt = patron.split('|')     # If so, we separate them and treat them
            patron = patron1
        except:
            logger.error(traceback.format_exc())

    # Array with the data of the alternative channels
    # We load in .json of the channel to see the lists of values ​​in settings
    fail_over = channeltools.get_channel_json(channel_py)
    for settings in fail_over['settings']:                              # All settings are scrolled
        if settings['id'] == "clonenewpct1_channels_list":              # We found in setting
            fail_over = settings['default']                             # Load list of clones
            break
    fail_over_list = ast.literal_eval(fail_over)
    # logger.debug(str(fail_over_list))

    if item.from_channel and item.from_channel != 'videolibrary': #Desde search puede venir con el nombre de canal equivocado
        item.channel = item.from_channel
    # We walk the Array identifying the channel that fails
    for active, channel, channel_host, contentType, action_excluded in fail_over_list:
        if item.channel == channel_py:
            if channel != item.category.lower():                        # is the channel / category failing?
                continue
        else:
            if channel != item.channel:                                 # is the channel failing?
                continue
        channel_failed = channel                                        # we save the name of the channel or category
        channel_host_failed = channel_host                              # we save the hostname
        channel_url_failed = item.url                                   # we save the url
        #logger.debug(channel_failed + ' / ' + channel_host_failed)

        if patron == True and active == '1':                            # we have only been asked to verify the clone
            return (item, data)                                         # we leave, with the same clone, if it is active
        if (item.action == 'episodios' or item.action == "update_tvshow" or item.action == "get_seasons" or item.action == 'findvideos') and item.contentType not in contentType:          # supports fail_over of this content?
            logger.error("ERROR 99: " + item.action.upper() + ": Unsupported Action for Channel Fail-Over: " + item.url)
            return (item, data)                         # does not support fail_over of this content, we can not do anything
        break

    if not channel_failed:
        logger.error('Pattern: ' + str(patron) + ' / fail_over_list: ' + str(fail_over_list))
        logger.error(item)
        return (item, data)                                             # Something has not worked, we can not do anything

    # We go through the Array identifying active channels that work, other than the fallen one, that support the content
    for active, channel, channel_host, contentType, action_excluded in fail_over_list:
        data_alt = ''
        if channel == channel_failed or active == '0' or item.action in action_excluded or item.extra2 in action_excluded:  # is the new channel valid?
            continue
        if (item.action == 'episodios' or item.action == "update_tvshow" or item.action == "get_seasons" or item.action == 'findvideos') and item.contentType not in contentType:          # does it support content?
            continue

        # We make the channel and url name change, keeping the previous ones as ALT
        item.channel_alt = channel_failed
        if item.channel != channel_py:
            item.channel = channel
        item.category = channel.capitalize()
        item.url_alt = channel_url_failed
        item.url = channel_url_failed
        channel_host_bis = re.sub(r'(?i)http.*://', '', channel_host)
        channel_host_failed_bis = re.sub(r'(?i)http.*://', '', channel_host_failed)
        item.url = item.url.replace(channel_host_failed_bis, channel_host_bis)

        url_alt += [item.url]                               # we save the url for the loop
        item.channel_host = channel_host
        # logger.debug(str(url_alt))

        # We remove the series code, because it can vary between websites
        if item.action == "episodios" or item.action == "get_seasons" or item.action == "update_tvshow":
            item.url = re.sub(r'\/\d+\/?$', '', item.url)   # it seems that with the title only finds the series, usually ...
            url_alt = [item.url]    # we save the url for the loop, but for now we ignore the initial with serial code

        # if it is an episode, we generalize the url so that it can be found in another clone. We remove the quality from the end of the url
        elif item.action == "findvideos" and item.contentType == "episode":
            try:
                # We remove the 0 to the left of the episode. Some clones do not accept it
                inter1, inter2, inter3 = scrapertools.find_single_match(item.url, r'(http.*?\/temporada-\d+.*?\/capitulo.?-)(\d+)(.*?\/)')
                inter2 = re.sub(r'^0', '', inter2)
                if inter1 + inter2 + inter3 not in url_alt:
                    url_alt += [inter1 + inter2 + inter3]

                # in this format we only remove the quality from the end of the url
                if scrapertools.find_single_match(item.url, r'http.*?\/temporada-\d+.*?\/capitulo.?-\d+.*?\/') not in url_alt:
                    url_alt += [scrapertools.find_single_match(item.url, r'http.*?\/temporada-\d+.*?\/capitulo.?-\d+.*?\/')]
            except:
                logger.error("ERROR 88: " + item.action + ": Error converting url: " + item.url)
                logger.error(traceback.format_exc())
            logger.debug('Converted URLs: ' + str(url_alt))

        if patron == True:                                  # we have only been asked to verify the clone
            return (item, data)                             # we leave, with a new clone

        # We read the new url .. There may be several alternatives to the original url
        for url in url_alt:
            try:
                if item.post:
                    data = re.sub(r"\n|\r|\t|\s{2}|(<!--.*?-->)", "", httptools.downloadpage(url, post=item.post, timeout=timeout).data)
                else:
                    data = re.sub(r"\n|\r|\t|\s{2}|(<!--.*?-->)", "", httptools.downloadpage(url, timeout=timeout).data)
                data_comillas = data.replace("'", "\"")
            except:
                data = ''
                logger.error(traceback.format_exc())
            if not data:                                    # no luck, we try the following url
                logger.error("ERROR 01: " + item.action + ": The Web does not respond or the URL is wrong: " + url)
                continue

            # We have managed to read the web, we validate if we find a valid link in this structure
            # Avoid misleading pages that can put the channel in an infinite loop
            if (not ".com/images/no_imagen.jpg" in data and not ".com/images/imagen-no-disponible.jpg" in data) or item.action != "episodios":
                if patron:
                    data_alt = scrapertools.find_single_match(data, patron)
                    if not data_alt:
                        data_alt = scrapertools.find_single_match(data_comillas, patron)
                        if data_alt and patron_alt:
                            data_alt = scrapertools.find_single_match(data, patron_alt)
                            if not data_alt and patron_alt:
                                data_alt = scrapertools.find_single_match(data_comillas, patron_alt)
                    if patron2 != None:
                        data_alt = scrapertools.find_single_match(data_alt, patron2)
                if not data_alt:                            # no luck, we tried the next channel
                    logger.error("ERROR 02: " + item.action + ": The structure of the Web has changed: " + url + " / Patron: " + patron + " / " +patron_alt)
                    web_intervenida(item, data)
                    data = ''
                    continue
            else:
                logger.error("ERROR 02: " + item.action + ": The structure of the Web has changed: " + url + " / Patron: " + patron + " / " +patron_alt)
                web_intervenida(item, data)
                data = ''
                continue

        if not data:                                        # no luck, we tried the following clone
            url_alt = []
            continue
        else:
            break

    del item.extra2                                         # We delete exclusive temporary action
    if not data:                                            # If you have not found anything, we leave cleaning variables
        if item.channel == channel_py:
            if item.channel_alt:
                item.category = item.channel_alt.capitalize()
                del item.channel_alt
        else:
            if item.channel_alt:
                item.channel = item.channel_alt
                del item.channel_alt
        if item.url_alt:
            item.url = item.url_alt
            del item.url_alt
        item.channel_host = channel_host_failed

    # logger.debug(item)

    return (item, data)


def web_intervenida(item, data, desactivar=True):
    logger.debug()

    """

    Call to verify if the crash of a Newpct1 clone is due to judicial intervention

    The method call from is:

        from lib import generictools
        item = generictools.web_intervened (item, data [, disable = True])

        - Entry: data: result of the download. It allows us to analyze if it is an intervention
        - Input: disable = True: indicates that you disable the channel or clone in case of judicial intervention
        - Output: item.intervention: return an array with the name of the intervened clone and the thumb of the intervening authority. The channel can announce it.
        - Output: If it is a clone of Newpct1, the clone is disabled in the Channel's .json. If it's another channel, the channel in your .json is disabled.

    """

    intervencion = ()
    judicial = ''

    # We verify that it is a judicial intervention
    if intervenido_policia in data or intervenido_guardia in data or intervenido_sucuri in data:
        if intervenido_guardia in data:
            judicial = 'intervenido_gc.png'                             # thumb of the Benemérita
        if intervenido_policia in data:
            judicial = 'intervenido_pn.jpeg'                            # thumb of the National Police
        if intervenido_sucuri in data:
            judicial = 'intervenido_sucuri.png'                         # thumb of Juices
        category = item.category
        if not item.category:
            category = item.channel
        intervencion = (category, judicial)                     # We keep the channel / category name and the judicial thumb
        if not item.intervencion:
            item.intervencion = []                                      # If the array does not exist, we create it
        item.intervencion += [intervencion]                             # We add this intervention to the array

        logger.error("ERROR 99: " + category + ": " + judicial + ": " + item.url + ": DISABLED=" + str(desactivar) + " / DATA: " + data)

        if desactivar == False:                                         # If we don't want to disable the channel, we go
            return item

        # We load in .json of the channel to see the lists of values ​​in settings. Load the cluttered keys !!!
        from core import filetools
        import json
        json_data = channeltools.get_channel_json(item.channel)

        if item.channel == channel_py:                                  # If it's a clone of Newpct1, we disable it
            for settings in json_data['settings']:                      # All settings are scrolled
                if settings['id'] == "clonenewpct1_channels_list":      # We found in setting
                    action_excluded = scrapertools.find_single_match(settings['default'], r"\('\d', '%s', '[^']+', '[^']*', '([^']*)'\)" % item.category.lower())               #extraemos el valor de action_excluded
                    if action_excluded:
                        if "intervenido" not in action_excluded:
                            action_excluded += ', %s' % judicial        # We add the thumb of the judicial authority
                    else:
                        action_excluded = '%s' % judicial

                    # We replace the status to disabled and add the thumb of the judicial authority
                    settings['default'] = re.sub(r"\('\d', '%s', ('[^']+', '[^']*'), '[^']*'\)" % item.category.lower(),  r"('0', '%s', \1, '%s')" % (item.category.lower(), action_excluded), settings['default'])

                    break
        else:
            # json_data['active'] = False                               # Channel is disabled
            json_data['thumbnail'] = ', thumb_%s' % judicial            # We keep the thumb of the judicial authority

        # We save the changes made in the .json
        try:
            if item.channel != channel_py:
                disabled = config.set_setting('enabled', False, item.channel)           # We deactivate the channel
                disabled = config.set_setting('include_in_global_search', False, item.channel)      # We get it out of global searches
            channel_path = filetools.join(config.get_runtime_path(), "channels", item.channel + ".json")
            with open(channel_path, 'w') as outfile:                                    # We record the updated .json
                json.dump(json_data, outfile, sort_keys = True, indent = 2, ensure_ascii = False)
        except:
            logger.error("ERROR 98 when saving the file: %s" % channel_path)
            logger.error(traceback.format_exc())

    # logger.debug(item)

    return item


def regenerate_clones():
    logger.debug()
    import json
    from core import videolibrarytools

    """
    Regenerate .json files that have been crushed with migration. Also delete tvshow.nfo files in films.

    Temporary and controlled use method
    """

    try:
        # Find the paths where to leave the control .json file, and the Video Library
        json_path = filetools.exists(filetools.join(config.get_runtime_path(), 'verify_cached_torrents.json'))
        if json_path:
            logger.debug('Previously repaired video library: WE ARE GOING')
            return False
        json_path = filetools.join(config.get_runtime_path(), 'verify_cached_torrents.json')
        filetools.write(json_path, json.dumps({"CINE_verify": True}))   # Prevents another simultaneous process from being launched
        json_error_path = filetools.join(config.get_runtime_path(), 'error_cached_torrents.json')
        json_error_path_BK = filetools.join(config.get_runtime_path(), 'error_cached_torrents_BK.json')

        videolibrary_path = config.get_videolibrary_path()          # We calculate the absolute path from the Video Library
        movies = config.get_setting("folder_movies")
        series = config.get_setting("folder_tvshows")
        torrents_movies = filetools.join(videolibrary_path, config.get_setting("folder_movies"))    # path of CINE
        torrents_series = filetools.join(videolibrary_path, config.get_setting("folder_tvshows"))   # path the SERIES

        # We load in .json from Newpct1 to see the lists of values ​​in settings
        fail_over_list = channeltools.get_channel_json(channel_py)
        for settings in fail_over_list['settings']:                             # All settings are scrolled
            if settings['id'] == "clonenewpct1_channels_list":                  # We found in setting
                fail_over_list = settings['default']                            # Load list of clones

        #Inicializa variables
        torren_list = []
        torren_list.append(torrents_movies)
        # torren_list.append(torrents_series)
        i = 0
        j = 0
        k = 0
        descomprimidos = []
        errores = []
        json_data = dict()

        # Browse the FILM and SERIES folders of the Video Library, reading, unzipping and rewriting the .torrent files
        for contentType in torren_list:
            for root, folders, files in filetools.walk(contentType):
                nfo = ''
                newpct1 = False
                file_list = str(files)
                logger.error(file_list)

                # Delete the Tvshow.nfo files and check if the .nfo has more than one channel and one is clone Newpct1
                for file in files:
                    # logger.debug('file - nfos: ' + file)
                    if 'tvshow.nfo' in file:
                        file_path = filetools.join(root, 'tvshow.nfo')
                        filetools.remove(file_path)
                        continue

                    if '.nfo' in file:
                        peli_name = file.replace('.nfo', '')
                        nfo = ''
                        try:
                            head_nfo, nfo = videolibrarytools.read_nfo(filetools.join(root, file))
                        except:
                            logger.error('** NFO: read error in: ' + file)
                            break
                        if not nfo:
                            logger.error('** NFO: read error in: ' + file)
                            break
                        if nfo.ow_force:                # If you have ow_force we remove it to avoid future problems
                            del nfo.ow_force
                            try:
                                filetools.write(filetools.join(root, file), head_nfo + nfo.tojson())    # I update the .nfo
                            except:
                                logger.error('** NFO: typing error in: ' + file)
                                break

                        if '.torrent' not in file_list and nfo.emergency_urls:
                            del nfo.emergency_urls                              # If you have emergency_urls, we reset it
                            try:
                                filetools.write(filetools.join(root, file), head_nfo + nfo.tojson())    # I update the .nfo
                            except:
                                logger.error('** NFO: typing error in: ' + file)
                                break
                            newpct1 = True                                      # we set to reset the .jsons

                        if len(nfo.library_urls) > 1:                           # Do you have more than one channel?
                            for canal, url in nfo.library_urls.items():
                                canal_json = "[%s].json" % canal
                                if canal_json not in file_list:                 # Zombie channel, we delete it
                                    logger.error('pop: ' + canal)
                                    nfo.library_urls.pop(canal, None)
                                    if nfo.emergency_urls:
                                        del nfo.emergency_urls                  # If you have emergency_urls, we reset it
                                    try:
                                        filetools.write(filetools.join(root, file), head_nfo + nfo.tojson())    # I update the .nfo
                                    except:
                                        logger.error('** NFO: typing error in: ' + file)
                                        break
                                    newpct1 = True                              # we set to reset the .jsons

                                canal_nwepct1 = "'%s'" % canal
                                if canal_nwepct1 in fail_over_list:             # Some channel is clone of Newpct1
                                    newpct1 = True                              # If yes, we mark it
                                    if nfo.emergency_urls:
                                        del nfo.emergency_urls                  # If you have emergency_urls, we reset it
                                        try:
                                            filetools.write(filetools.join(root, file), head_nfo + nfo.tojson())    # I update the .nfo
                                        except:
                                            logger.error('** NFO: typing error in: ' + file)
                                            break

                # Area to fill the .json files
                if not newpct1:
                    continue
                for file in files:
                    file_path = filetools.join(root, file)
                    if '.json' in file:
                        logger.debug('** file: ' + file)
                        canal_json = scrapertools.find_single_match(file, r'\[(\w+)\].json')
                        if canal_json not in nfo.library_urls:
                            filetools.remove(file_path)                             # we delete the .json is a zombie
                        item_movie = ''
                        try:
                            item_movie = Item().fromjson(filetools.read(file_path)) # we read the .json
                        except:
                            logger.error('** JSON: read error in: ' + file)
                            continue
                        if not item_movie:
                            logger.error('** JSON: read error in: ' + file)
                            continue
                        if item_movie.emergency_urls: del item_movie.emergency_urls
                        item_movie.channel = canal_json                             # channel name
                        item_movie.category = canal_json.capitalize()               # category
                        item_movie.url = nfo.library_urls[canal_json]               # url
                        if scrapertools.find_single_match(item_movie.title, r'(.*?)\[\d+.\d+\s*.\s*B\]'):
                            item_movie.title = scrapertools.find_single_match(item_movie.title, r'(.*?)\[\d+.\d+\s*.\s*B\]').strip()    # we remove Size
                        if item_movie.added_replacing: del item_movie.added_replacing   # remove trace from the replaced channel
                        try:
                            filetools.write(file_path, item_movie.tojson())         # We save the new .json from the movie
                        except:
                            logger.error('** JSON: typing error in: ' + file)
                        else:
                            errores += [file]
                    if '.torrent' in file:
                        filetools.remove(file_path)                                 # we delete the saved .torrent


        logger.error('** List of movies repaireds: ' + str(errores))
        filetools.write(json_error_path, json.dumps(json_data))
        filetools.write(json_error_path_BK, json.dumps(json_data))
        filetools.write(json_path, json.dumps({"CINE_verify": True}))
    except:
        filetools.remove(json_path)                             # we delete the lock so that it can be launched again
        logger.error('CINEMA Video Library REPAIR process error')
        logger.error(traceback.format_exc())

    return True


def dejuice(data):
    logger.debug()
    # Method to unobtrusive JuicyCodes data

    import base64
    from lib import jsunpack

    juiced = scrapertools.find_single_match(data, r'JuicyCodes.Run\((.*?)\);')
    b64_data = juiced.replace('+', '').replace('"', '')
    b64_decode = base64.b64decode(b64_data)
    dejuiced = jsunpack.unpack(b64_decode)

    return dejuiced


def privatedecrypt(url, headers=None):

    data = httptools.downloadpage(url, headers=headers, follow_redirects=False).data
    data = re.sub(r'\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)
    packed = scrapertools.find_single_match(data, r'(eval\(.*?);var')
    unpacked = jsunpack.unpack(packed)
    server = scrapertools.find_single_match(unpacked, r"src:.'(http://\D+)/")
    id = scrapertools.find_single_match(unpacked, r"src:.'http://\D+/.*?description:.'(.*?).'")
    if server == '':
        if 'powvideo' in unpacked:
            id = scrapertools.find_single_match(unpacked, ",description:.'(.*?).'")
            server = 'https://powvideo.net'
    if server != '' and id != '':
        url = '%s/%s' % (server, id)
    else:
        url = ''
    return url