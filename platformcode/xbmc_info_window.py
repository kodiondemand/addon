# -*- coding: utf-8 -*-

import xbmcgui

from core.tmdb import Tmdb
from platformcode import config, logger

ID_BUTTON_CLOSE = 10003
ID_BUTTON_PREVIOUS = 10025
ID_BUTTON_NEXT = 10026
ID_BUTTON_CANCEL = 10027
ID_BUTTON_OK = 10028


class InfoWindow(xbmcgui.WindowXMLDialog):
    otmdb = None

    item_title = ""
    item_serie = ""
    item_temporada = 0
    item_episodio = 0
    result = {}

    # PARA TMDB
    @staticmethod
    def get_language(lng):
        # Cambiamos el formato del Idioma
        languages = {
            'aa': 'Afar', 'ab': 'Abkhazian', 'af': 'Afrikaans', 'ak': 'Akan', 'sq': 'Albanian', 'am': 'Amharic',
            'ar': 'Arabic', 'an': 'Aragonese', 'as': 'Assamese', 'av': 'Avaric', 'ae': 'Avestan', 'ay': 'Aymara',
            'az': 'Azerbaijani', 'ba': 'Bashkir', 'bm': 'Bambara', 'eu': 'Basque', 'be': 'Belarusian', 'bn': 'Bengali',
            'bh': 'Bihari languages', 'bi': 'Bislama', 'bo': 'Tibetan', 'bs': 'Bosnian', 'br': 'Breton',
            'bg': 'Bulgarian', 'my': 'Burmese', 'ca': 'Catalan; Valencian', 'cs': 'Czech', 'ch': 'Chamorro',
            'ce': 'Chechen', 'zh': 'Chinese',
            'cu': 'Church Slavic; Old Slavonic; Church Slavonic; Old Bulgarian; Old Church Slavonic', 'cv': 'Chuvash',
            'kw': 'Cornish', 'co': 'Corsican', 'cr': 'Cree', 'cy': 'Welsh', 'da': 'Danish', 'de': 'German',
            'dv': 'Divehi; Dhivehi; Maldivian', 'nl': 'Dutch; Flemish', 'dz': 'Dzongkha', 'en': 'English',
            'eo': 'Esperanto', 'et': 'Estonian', 'ee': 'Ewe', 'fo': 'Faroese', 'fa': 'Persian', 'fj': 'Fijian',
            'fi': 'Finnish', 'fr': 'French', 'fy': 'Western Frisian', 'ff': 'Fulah', 'Ga': 'Georgian',
            'gd': 'Gaelic; Scottish Gaelic', 'ga': 'Irish', 'gl': 'Galician', 'gv': 'Manx',
            'el': 'Greek, Modern (1453-)', 'gn': 'Guarani', 'gu': 'Gujarati', 'ht': 'Haitian; Haitian Creole',
            'ha': 'Hausa', 'he': 'Hebrew', 'hz': 'Herero', 'hi': 'Hindi', 'ho': 'Hiri Motu', 'hr': 'Croatian',
            'hu': 'Hungarian', 'hy': 'Armenian', 'ig': 'Igbo', 'is': 'Icelandic', 'io': 'Ido',
            'ii': 'Sichuan Yi; Nuosu', 'iu': 'Inuktitut', 'ie': 'Interlingue; Occidental',
            'ia': 'Interlingua (International Auxiliary Language Association)', 'id': 'Indonesian', 'ik': 'Inupiaq',
            'it': 'Italian', 'jv': 'Javanese', 'ja': 'Japanese', 'kl': 'Kalaallisut; Greenlandic', 'kn': 'Kannada',
            'ks': 'Kashmiri', 'ka': 'Georgian', 'kr': 'Kanuri', 'kk': 'Kazakh', 'km': 'Central Khmer',
            'ki': 'Kikuyu; Gikuyu', 'rw': 'Kinyarwanda', 'ky': 'Kirghiz; Kyrgyz', 'kv': 'Komi', 'kg': 'Kongo',
            'ko': 'Korean', 'kj': 'Kuanyama; Kwanyama', 'ku': 'Kurdish', 'lo': 'Lao', 'la': 'Latin', 'lv': 'Latvian',
            'li': 'Limburgan; Limburger; Limburgish', 'ln': 'Lingala', 'lt': 'Lithuanian',
            'lb': 'Luxembourgish; Letzeburgesch', 'lu': 'Luba-Katanga', 'lg': 'Ganda', 'mk': 'Macedonian',
            'mh': 'Marshallese', 'ml': 'Malayalam', 'mi': 'Maori', 'mr': 'Marathi', 'ms': 'Malay', 'Mi': 'Micmac',
            'mg': 'Malagasy', 'mt': 'Maltese', 'mn': 'Mongolian', 'na': 'Nauru', 'nv': 'Navajo; Navaho',
            'nr': 'Ndebele, South; South Ndebele', 'nd': 'Ndebele, North; North Ndebele', 'ng': 'Ndonga',
            'ne': 'Nepali', 'nn': 'Norwegian Nynorsk; Nynorsk, Norwegian', 'nb': 'Bokmål, Norwegian; Norwegian Bokmål',
            'no': 'Norwegian', 'oc': 'Occitan (post 1500)', 'oj': 'Ojibwa', 'or': 'Oriya', 'om': 'Oromo',
            'os': 'Ossetian; Ossetic', 'pa': 'Panjabi; Punjabi', 'pi': 'Pali', 'pl': 'Polish', 'pt': 'Portuguese',
            'ps': 'Pushto; Pashto', 'qu': 'Quechua', 'ro': 'Romanian; Moldavian; Moldovan', 'rn': 'Rundi',
            'ru': 'Russian', 'sg': 'Sango', 'rm': 'Romansh', 'sa': 'Sanskrit', 'si': 'Sinhala; Sinhalese',
            'sk': 'Slovak', 'sl': 'Slovenian', 'se': 'Northern Sami', 'sm': 'Samoan', 'sn': 'Shona', 'sd': 'Sindhi',
            'so': 'Somali', 'st': 'Sotho, Southern', 'es': 'Spanish', 'sc': 'Sardinian', 'sr': 'Serbian', 'ss': 'Swati',
            'su': 'Sundanese', 'sw': 'Swahili', 'sv': 'Swedish', 'ty': 'Tahitian', 'ta': 'Tamil', 'tt': 'Tatar',
            'te': 'Telugu', 'tg': 'Tajik', 'tl': 'Tagalog', 'th': 'Thai', 'ti': 'Tigrinya',
            'to': 'Tonga (Tonga Islands)', 'tn': 'Tswana', 'ts': 'Tsonga', 'tk': 'Turkmen', 'tr': 'Turkish',
            'tw': 'Twi', 'ug': 'Uighur; Uyghur', 'uk': 'Ukrainian', 'ur': 'Urdu', 'uz': 'Uzbek', 've': 'Venda',
            'vi': 'Vietnamese', 'vo': 'Volapük', 'wa': 'Walloon', 'wo': 'Wolof', 'xh': 'Xhosa', 'yi': 'Yiddish',
            'yo': 'Yoruba', 'za': 'Zhuang; Chuang', 'zu': 'Zulu'}

        return languages.get(lng, lng)

    def get_scraper_data(self, data_in):
        self.otmdb = None
        # logger.debug(str(data_in))

        if self.listData:
            # Data common to all listings
            infoLabels = self.scraper().get_infoLabels(origen=data_in)

            if "original_language" in infoLabels:
                infoLabels["language"] = self.get_language(infoLabels["original_language"])
            infoLabels["puntuacion"] = "%s/10 (%s)" % (infoLabels.get("rating", "?"), infoLabels.get("votes", "N/A"))

            self.result = infoLabels

    def start(self, data, caption="Información del vídeo", item=None, scraper=Tmdb):
        """
        It shows a window with the info of the video. Optionally, the title of the window can be indicated by means of the argument 'caption'.

        If an item is passed as the 'data' argument use the Tmdb scrapper to find the video info
            In case of movies:
                Take the title from the following fields (in this order)
                      1. contentTitle (this has priority 1)
                      2. title (this has priority 2)
                The first one containing "something" interprets it as the title (it is important to make sure that the title is in
                your site)

            In case of series:
                1. Find the season and episode in the contentSeason and contentEpisodeNumber fields
                2. Try to remove it from the video title (format: 1x01)

                Here are two possible options:
                      1. We have Season and episode
                        Shows the information of the specific chapter
                      2. We DO NOT have Season and episode
                        In this case it shows the generic information of the series

        If an InfoLabels object (see item.py) is passed as an argument 'data' it shows in the window directly
        the past information (without using the scrapper)
            Format:
                In case of movies:
                    infoLabels ({
                             "type"           : "movie",
                             "title": "Title of the movie",
                             "original_title": "Original movie title",
                             "date": "Release date",
                             "language": "Original language of the movie",
                             "rating": "Rating of the movie",
                             "votes": "Number of votes",
                             "genres": "Genres of the movie",
                             "thumbnail": "Path for the thumbnail",
                             "fanart": "Route for the fanart",
                             "plot": "Synopsis of the movie"
                          }
                In case of series:
                    infoLabels ({
                             "type"           : "tv",
                             "title": "Title of the series",
                             "episode_title": "Episode title",
                             "date": "Date of issue",
                             "language": "Original language of the series",
                             "rating": "Punctuation of the series",
                             "votes": "Number of votes",
                             "genres": "Genres of the series",
                             "thumbnail": "Path for the thumbnail",
                             "fanart": "Route for the fanart",
                             "plot": "Synopsis of the episode or series",
                             "seasons": "Number of Seasons",
                             "season": "Season",
                             "episodes": "Number of episodes of the season",
                             "episode": "Episode"
                          }
        If a list of InfoLabels () with the previous structure is passed as the 'data' argument, it shows the buttons
        'Previous' and 'Next' to scroll through the list. It also shows the 'Accept' and 'Cancel' buttons that
        call the function 'callback' of the channel from where the call is made, passing the element as parameters
        current (InfoLabels ()) or None respectively.

        @param data: information to get scraper data.
        @type data: item, InfoLabels, list(InfoLabels)
        @param caption: window title.
        @type caption: str
        @param item: item for which the information window is to be displayed
        @type item: Item
        @param scraper: scraper that has the data of the movies or series to show in the window.
        @type scraper: Scraper
        """

        # We capture the parameters
        self.caption = caption
        self.item = item
        self.indexList = -1
        self.listData = None
        self.return_value = None
        self.scraper = scraper

        logger.debug(data)
        if type(data) == list:
            self.listData = data
            self.indexList = 0
            data = self.listData[self.indexList]

        self.get_scraper_data(data)

        # Show window
        self.doModal()
        return self.return_value

    def __init__(self, *args):
        self.caption = ""
        self.item = None
        self.listData = None
        self.indexList = 0
        self.return_value = None
        self.scraper = Tmdb

    def onInit(self):
        #### Kodi 18 compatibility ####
        if config.get_platform(True)['num_version'] < 18:
            if xbmcgui.__version__ == "1.2":
                self.setCoordinateResolution(1)
            else:
                self.setCoordinateResolution(5)

        # We put the title and the images
        self.getControl(10002).setLabel(self.caption)
        self.getControl(10004).setImage(self.result.get("fanart", ""))
        self.getControl(10005).setImage(self.result.get("thumbnail", "images/img_no_disponible.png"))

        # We load the data for the movie format
        if self.result.get("mediatype", "movie") == "movie":
            self.getControl(10006).setLabel(config.get_localized_string(60377))
            self.getControl(10007).setLabel(self.result.get("title", "N/A"))
            self.getControl(10008).setLabel(config.get_localized_string(60378))
            self.getControl(10009).setLabel(self.result.get("originaltitle", "N/A"))
            self.getControl(100010).setLabel(config.get_localized_string(60379))
            self.getControl(100011).setLabel(self.result.get("language", "N/A"))
            self.getControl(100012).setLabel(config.get_localized_string(60380))
            self.getControl(100013).setLabel(self.result.get("puntuacion", "N/A"))
            self.getControl(100014).setLabel(config.get_localized_string(60381))
            self.getControl(100015).setLabel(self.result.get("release_date", "N/A"))
            self.getControl(100016).setLabel(config.get_localized_string(60382))
            self.getControl(100017).setLabel(self.result.get("genre", "N/A"))

        # We load the data for the serial format
        else:
            self.getControl(10006).setLabel(config.get_localized_string(60383))
            self.getControl(10007).setLabel(self.result.get("title", "N/A"))
            self.getControl(10008).setLabel(config.get_localized_string(60379))
            self.getControl(10009).setLabel(self.result.get("language", "N/A"))
            self.getControl(100010).setLabel(config.get_localized_string(60380))
            self.getControl(100011).setLabel(self.result.get("puntuacion", "N/A"))
            self.getControl(100012).setLabel(config.get_localized_string(60382))
            self.getControl(100013).setLabel(self.result.get("genre", "N/A"))

            if self.result.get("season"):
                self.getControl(100014).setLabel(config.get_localized_string(60384))
                self.getControl(100015).setLabel(self.result.get("temporada_nombre", "N/A"))
                self.getControl(100016).setLabel(config.get_localized_string(60385))
                self.getControl(100017).setLabel(self.result.get("season", "N/A") + " de " + self.result.get("seasons", "N/A"))
            if self.result.get("episode"):
                self.getControl(100014).setLabel(config.get_localized_string(60377))
                self.getControl(100015).setLabel(self.result.get("episode_title", "N/A"))
                self.getControl(100018).setLabel(config.get_localized_string(60386))
                self.getControl(100019).setLabel(self.result.get("episode", "N/A") + " de " + self.result.get("episodes", "N/A"))
                self.getControl(100020).setLabel(config.get_localized_string(60387))
                self.getControl(100021).setLabel(self.result.get("date", "N/A"))

        # Synopsis
        if self.result['plot']:
            self.getControl(100022).setLabel(config.get_localized_string(60388))
            self.getControl(100023).setText(self.result.get("plot", "N/A"))
        else:
            self.getControl(100022).setLabel("")
            self.getControl(100023).setText("")

        # We load the buttons if necessary
        self.getControl(10024).setVisible(self.indexList > -1)  # Button group
        self.getControl(ID_BUTTON_PREVIOUS).setEnabled(self.indexList > 0)  # Previous

        if self.listData:
            m = len(self.listData)
        else:
            m = 1

        self.getControl(ID_BUTTON_NEXT).setEnabled(self.indexList + 1 != m)  # Following
        self.getControl(100029).setLabel("(%s/%s)" % (self.indexList + 1, m))  # x/m

        # We put the focus in the Group of buttons, if "Previous" was deactivated the focus would go to the "Next" button
        # if "Next" tb is deactivated it will pass the focus to the "Cancel" button
        self.setFocus(self.getControl(10024))

        return self.return_value

    def onClick(self, _id):
        logger.info("onClick id=" + repr(_id))
        if _id == ID_BUTTON_PREVIOUS and self.indexList > 0:
            self.indexList -= 1
            self.get_scraper_data(self.listData[self.indexList])
            self.onInit()

        elif _id == ID_BUTTON_NEXT and self.indexList < len(self.listData) - 1:
            self.indexList += 1
            self.get_scraper_data(self.listData[self.indexList])
            self.onInit()

        elif _id == ID_BUTTON_OK or _id == ID_BUTTON_CLOSE or _id == ID_BUTTON_CANCEL:
            self.close()

            if _id == ID_BUTTON_OK:
                self.return_value = self.listData[self.indexList]
            else:
                self.return_value = None

    def onAction(self, action):
        logger.info("action=" + repr(action.getId()))
        action = action.getId()

        # Find Focus
        focus = self.getFocusId()

        # Left
        if action == 1:

            if focus == ID_BUTTON_OK:
                self.setFocus(self.getControl(ID_BUTTON_CANCEL))

            elif focus == ID_BUTTON_CANCEL:
                if self.indexList + 1 != len(self.listData):
                    # Next
                    self.setFocus(self.getControl(ID_BUTTON_NEXT))
                elif self.indexList > 0:
                    # Previous
                    self.setFocus(self.getControl(ID_BUTTON_PREVIOUS))

            elif focus == ID_BUTTON_NEXT:
                if self.indexList > 0:
                    # Next
                    self.setFocus(self.getControl(ID_BUTTON_PREVIOUS))

        # Right
        elif action == 2:

            if focus == ID_BUTTON_PREVIOUS:
                if self.indexList + 1 != len(self.listData):
                    # Next
                    self.setFocus(self.getControl(ID_BUTTON_NEXT))
                else:
                    # Cancel
                    self.setFocus(self.getControl(ID_BUTTON_CANCEL))

            elif focus == ID_BUTTON_NEXT:
                self.setFocus(self.getControl(ID_BUTTON_CANCEL))

            elif focus == ID_BUTTON_CANCEL:
                self.setFocus(self.getControl(ID_BUTTON_OK))

        # Up
        elif action == 3:
            self.setFocus(self.getControl(ID_BUTTON_CLOSE))

        # Down
        elif action == 4:
            self.setFocus(self.getControl(ID_BUTTON_OK))
        # Press ESC or Back, simulate click on cancel button
        if action in [10, 92]:
            self.onClick(ID_BUTTON_CANCEL)
