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
            # Datos comunes a todos los listados
            infoLabels = self.scraper().get_infoLabels(origen=data_in)

            if "original_language" in infoLabels:
                infoLabels["language"] = self.get_language(infoLabels["original_language"])
            infoLabels["puntuacion"] = "%s/10 (%s)" % (infoLabels.get("rating", "?"), infoLabels.get("votes", "N/A"))

            self.result = infoLabels

    def start(self, data, caption="Información del vídeo", item=None, scraper=Tmdb):
        """
        Muestra una ventana con la info del vídeo. Opcionalmente se puede indicar el titulo de la ventana mendiante
        el argumento 'caption'.

        Si se pasa un item como argumento 'data' usa el scrapper Tmdb para buscar la info del vídeo
            En caso de peliculas:
                Coge el titulo de los siguientes campos (en este orden)
                      1. contentTitle (este tiene prioridad 1)
                      2. fulltitle (este tiene prioridad 2)
                      3. title (este tiene prioridad 3)
                El primero que contenga "algo" lo interpreta como el titulo (es importante asegurarse que el titulo este en
                su sitio)

            En caso de series:
                1. Busca la temporada y episodio en los campos contentSeason y contentEpisodeNumber
                2. Intenta Sacarlo del titulo del video (formato: 1x01)

                Aqui hay dos opciones posibles:
                      1. Tenemos Temporada y episodio
                        Muestra la información del capitulo concreto
                      2. NO Tenemos Temporada y episodio
                        En este caso muestra la informacion generica de la serie

        Si se pasa como argumento 'data' un  objeto InfoLabels(ver item.py) muestra en la ventana directamente
        la información pasada (sin usar el scrapper)
            Formato:
                En caso de peliculas:
                    infoLabels({
                             "type"           : "movie",
                             "title"          : "Titulo de la pelicula",
                             "original_title" : "Titulo original de la pelicula",
                             "date"           : "Fecha de lanzamiento",
                             "language"       : "Idioma original de la pelicula",
                             "rating"         : "Puntuacion de la pelicula",
                             "votes"          : "Numero de votos",
                             "genres"         : "Generos de la pelicula",
                             "thumbnail"      : "Ruta para el thumbnail",
                             "fanart"         : "Ruta para el fanart",
                             "plot"           : "Sinopsis de la pelicula"
                          }
                En caso de series:
                    infoLabels({
                             "type"           : "tv",
                             "title"          : "Titulo de la serie",
                             "episode_title"  : "Titulo del episodio",
                             "date"           : "Fecha de emision",
                             "language"       : "Idioma original de la serie",
                             "rating"         : "Puntuacion de la serie",
                             "votes"          : "Numero de votos",
                             "genres"         : "Generos de la serie",
                             "thumbnail"      : "Ruta para el thumbnail",
                             "fanart"         : "Ruta para el fanart",
                             "plot"           : "Sinopsis de la del episodio o de la serie",
                             "seasons"        : "Numero de Temporadas",
                             "season"         : "Temporada",
                             "episodes"       : "Numero de episodios de la temporada",
                             "episode"        : "Episodio"
                          }
        Si se pasa como argumento 'data' un listado de InfoLabels() con la estructura anterior, muestra los botones
        'Anterior' y 'Siguiente' para ir recorriendo la lista. Ademas muestra los botones 'Aceptar' y 'Cancelar' que
        llamaran a la funcion 'callback' del canal desde donde se realiza la llamada pasandole como parametros el elemento
        actual (InfoLabels()) o None respectivamente.

        @param data: información para obtener datos del scraper.
        @type data: item, InfoLabels, list(InfoLabels)
        @param caption: titulo de la ventana.
        @type caption: str
        @param item: elemento del que se va a mostrar la ventana de información
        @type item: Item
        @param scraper: scraper que tiene los datos de las peliculas o series a mostrar en la ventana.
        @type scraper: Scraper
        """

        # Capturamos los parametros
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

        # Muestra la ventana
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
        #### Compatibilidad con Kodi 18 ####
        if config.get_platform(True)['num_version'] < 18:
            if xbmcgui.__version__ == "1.2":
                self.setCoordinateResolution(1)
            else:
                self.setCoordinateResolution(5)

        # Ponemos el título y las imagenes
        self.getControl(10002).setLabel(self.caption)
        self.getControl(10004).setImage(self.result.get("fanart", ""))
        self.getControl(10005).setImage(self.result.get("thumbnail", "images/img_no_disponible.png"))

        # Cargamos los datos para el formato pelicula
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

        # Cargamos los datos para el formato serie
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
                self.getControl(100017).setLabel(self.result.get("season", "N/A") + " de " +
                                                 self.result.get("seasons", "N/A"))
            if self.result.get("episode"):
                self.getControl(100014).setLabel(config.get_localized_string(60377))
                self.getControl(100015).setLabel(self.result.get("episode_title", "N/A"))
                self.getControl(100018).setLabel(config.get_localized_string(60386))
                self.getControl(100019).setLabel(self.result.get("episode", "N/A") + " de " +
                                                 self.result.get("episodes", "N/A"))
                self.getControl(100020).setLabel(config.get_localized_string(60387))
                self.getControl(100021).setLabel(self.result.get("date", "N/A"))

        # Sinopsis
        if self.result['plot']:
            self.getControl(100022).setLabel(config.get_localized_string(60388))
            self.getControl(100023).setText(self.result.get("plot", "N/A"))
        else:
            self.getControl(100022).setLabel("")
            self.getControl(100023).setText("")

        # Cargamos los botones si es necesario
        self.getControl(10024).setVisible(self.indexList > -1)  # Grupo de botones
        self.getControl(ID_BUTTON_PREVIOUS).setEnabled(self.indexList > 0)  # Anterior

        if self.listData:
            m = len(self.listData)
        else:
            m = 1

        self.getControl(ID_BUTTON_NEXT).setEnabled(self.indexList + 1 != m)  # Siguiente
        self.getControl(100029).setLabel("(%s/%s)" % (self.indexList + 1, m))  # x/m

        # Ponemos el foco en el Grupo de botones, si estuviera desactivado "Anterior" iria el foco al boton "Siguiente"
        # si "Siguiente" tb estuviera desactivado pasara el foco al botón "Cancelar"
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

        # Obtenemos el foco
        focus = self.getFocusId()

        # Accion 1: Flecha izquierda
        if action == 1:

            if focus == ID_BUTTON_OK:
                self.setFocus(self.getControl(ID_BUTTON_CANCEL))

            elif focus == ID_BUTTON_CANCEL:
                if self.indexList + 1 != len(self.listData):
                    # vamos al botón Siguiente
                    self.setFocus(self.getControl(ID_BUTTON_NEXT))
                elif self.indexList > 0:
                    # vamos al botón Anterior ya que Siguiente no está activo (estamos al final de la lista)
                    self.setFocus(self.getControl(ID_BUTTON_PREVIOUS))

            elif focus == ID_BUTTON_NEXT:
                if self.indexList > 0:
                    # vamos al botón Anterior
                    self.setFocus(self.getControl(ID_BUTTON_PREVIOUS))

        # Accion 2: Flecha derecha
        elif action == 2:

            if focus == ID_BUTTON_PREVIOUS:
                if self.indexList + 1 != len(self.listData):
                    # vamos al botón Siguiente
                    self.setFocus(self.getControl(ID_BUTTON_NEXT))
                else:
                    # vamos al botón Cancelar ya que Siguiente no está activo (estamos al final de la lista)
                    self.setFocus(self.getControl(ID_BUTTON_CANCEL))

            elif focus == ID_BUTTON_NEXT:
                self.setFocus(self.getControl(ID_BUTTON_CANCEL))

            elif focus == ID_BUTTON_CANCEL:
                self.setFocus(self.getControl(ID_BUTTON_OK))

        # Pulsa ESC o Atrás, simula click en boton cancelar
        if action in [10, 92]:
            self.onClick(ID_BUTTON_CANCEL)
