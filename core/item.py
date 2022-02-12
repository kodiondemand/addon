# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------------
# Item is the object we use for representing data 
# --------------------------------------------------------------------------------

#from builtins import str
from future.builtins import object
import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

if PY3:
    #from future import standard_library
    #standard_library.install_aliases()
    import urllib.parse as urllib                               # It is very slow in PY2. In PY3 it is native
else:
    import urllib                                               # We use the native of PY2 which is faster
from core.scrapertools import unescape

import base64
import copy

from core import jsontools as json


class InfoLabels(dict):
    def __str__(self):
        return self.tostring(separador=',\r\t')

    def __setitem__(self, name, value):
        if name in ["season", "episode"]:
            # we force int () in season and episode
            try:
                super(InfoLabels, self).__setitem__(name, int(value))
            except:
                pass

        elif name in ['IMDBNumber', 'imdb_id']:
            # For compatibility we have to save the value in the three fields
            super(InfoLabels, self).__setitem__('IMDBNumber', str(value))
            # super(InfoLabels, self).__setitem__('code', value)
            super(InfoLabels, self).__setitem__('imdb_id', str(value))

        elif name == "mediatype" and value not in ["list", "movie", "tvshow", "season", "episode", "music", "undefined"]:
            super(InfoLabels, self).__setitem__('mediatype', 'list')

        elif name in ['tmdb_id', 'tvdb_id', 'noscrap_id']:
            super(InfoLabels, self).__setitem__(name, str(value))
        else:
            super(InfoLabels, self).__setitem__(name, value)

    # Python 2.4
    def __getitem__(self, key):
        try:
            return super(InfoLabels, self).__getitem__(key)
        except:
            return self.__missing__(key)

    def __missing__(self, key):
        """
        Valores por defecto en caso de que la clave solicitada no exista.
        El parametro 'default' en la funcion obj_infoLabels.get(key,default) tiene preferencia sobre los aqui definidos.
        """
        if key in ['rating']:
            # Key example q returns a str formatted as float by default
            return '0.0'

        elif key == 'code':
            code = []
            # Add imdb_id to the code list
            if 'imdb_id' in list(super(InfoLabels, self).keys()) and super(InfoLabels, self).__getitem__('imdb_id'):
                code.append(super(InfoLabels, self).__getitem__('imdb_id'))

            # Complete with the rest of the codes
            for scr in ['tmdb_id', 'tvdb_id', 'noscrap_id']:
                if scr in list(super(InfoLabels, self).keys()) and super(InfoLabels, self).__getitem__(scr):
                    value = "%s%s" % (scr[:-2], super(InfoLabels, self).__getitem__(scr))
                    code.append(value)

            # Option to add a code of the random type
            if not code:
                import time
                value = time.strftime("%Y%m%d%H%M%S", time.gmtime())
                code.append(value)
                super(InfoLabels, self).__setitem__('noscrap_id', value)

            return code

        elif key == 'mediatype':
            # "list", "movie", "tvshow", "season", "episode"
            if 'tvshowtitle' in list(super(InfoLabels, self).keys()) \
                    and super(InfoLabels, self).__getitem__('tvshowtitle') != "":
                if 'episode' in list(super(InfoLabels, self).keys()) and super(InfoLabels, self).__getitem__('episode') != "":
                    return 'episode'

                if 'episodeName' in list(super(InfoLabels, self).keys()) \
                        and super(InfoLabels, self).__getitem__('episodeName') != "":
                    return 'episode'

                if 'season' in list(super(InfoLabels, self).keys()) and super(InfoLabels, self).__getitem__('season') != "":
                    return 'season'
                else:
                    return 'tvshow'

            elif 'title' in list(super(InfoLabels, self).keys()) and super(InfoLabels, self).__getitem__('title') != "":
                return 'movie'

            else:
                return 'list'

        else:
            # The rest of the keys return empty strings by default
            return ""

    def tostring(self, separador=', '):
        ls = []
        dic = dict(list(super(InfoLabels, self).items()))

        for i in sorted(dic.items()):
            i_str = str(i)[1:-1]
            if isinstance(i[0], str):
                old = i[0] + "',"
                new = i[0] + "':"
            else:
                old = str(i[0]) + ","
                new = str(i[0]) + ":"
            ls.append(i_str.replace(old, new, 1))

        return "{%s}" % separador.join(ls)


class Item(object):
    def __init__(self, **kwargs):
        """
        Item initialization
        """

        # Creamos el atributo infoLabels
        self.__dict__["infoLabels"] = InfoLabels()
        if "infoLabels" in kwargs:
            if isinstance(kwargs["infoLabels"], dict):
                self.__dict__["infoLabels"].update(kwargs["infoLabels"])
            del kwargs["infoLabels"]

        if "parentContent" in kwargs:
            self.set_parent_content(kwargs["parentContent"])
            del kwargs["parentContent"]

        kw = copy.copy(kwargs)
        for k in kw:
            if k in ["contentTitle", "contentPlot", "contentSerieName", "show", "contentType", "contentEpisodeTitle",
                     "contentSeason", "contentEpisodeNumber", "contentThumbnail", "plot", "duration", "contentQuality",
                     "quality", "year"]:
                self.__setattr__(k, kw[k])
                del kwargs[k]

        self.__dict__.update(kwargs)
        self.__dict__ = self.toutf8(self.__dict__)

    def __contains__(self, m):
        """
        Check if an attribute exists in the item
        """
        return m in self.__dict__

    def __setattr__(self, name, value):
        """
        Function called when modifying any attribute of the item, modifies some attributes based on the modified data.
        """
        if PY3: name = self.toutf8(name)
        value = self.toutf8(value)
        if name == "__dict__":
            for key in value:
                self.__setattr__(key, value[key])
            return

        # We decode the HTML entities
        if name in ["title", "plot", "fulltitle", "contentPlot", "contentTitle"]:
            value = self.decode_html(value)

        # By modifying any of these attributes content...
        if name in ["contentTitle", "contentPlot", "plot", "contentSerieName", "contentType", "contentEpisodeTitle",
                    "contentSeason", "contentEpisodeNumber", "contentThumbnail", "show", "contentQuality", "quality", "year"]:
            # ...and update infoLables
            if name == "contentTitle":
                self.__dict__["infoLabels"]["title"] = value
            elif name == "contentPlot" or name == "plot":
                self.__dict__["infoLabels"]["plot"] = value
            elif name == "contentSerieName" or name == "show":
                self.__dict__["infoLabels"]["tvshowtitle"] = value
            elif name == "contentType":
                self.__dict__["infoLabels"]["mediatype"] = value
            elif name == "contentEpisodeTitle":
                self.__dict__["infoLabels"]["episodeName"] = value
            elif name == "contentSeason":
                self.__dict__["infoLabels"]["season"] = value
            elif name == "contentEpisodeNumber":
                self.__dict__["infoLabels"]["episode"] = value
            elif name == "contentThumbnail":
                self.__dict__["infoLabels"]["thumbnail"] = value
            elif name == "contentQuality" or name == "quality":
                self.__dict__["infoLabels"]["quality"] = value
            elif name == "year":
                self.__dict__["infoLabels"]["year"] = value

        elif name == "duration":
            # String q represents the duration of the video in seconds
            self.__dict__["infoLabels"]["duration"] = str(value)

        elif name == "viewcontent" and value not in ["files", "movies", "tvshows", "seasons", "episodes"]:
            super(Item, self).__setattr__("viewcontent", "files")

        # When assigning a value to infoLables
        elif name == "infoLabels":
            if isinstance(value, dict):
                value_defaultdict = InfoLabels(value)
                self.__dict__["infoLabels"] = value_defaultdict

        else:
            super(Item, self).__setattr__(name, value)

    def __getattr__(self, name):
        """
        Returns the default values ​​in case the requested attribute does not exist in the item
        """
        if name.startswith("__"):
            return super(Item, self).__getattribute__(name)

        # default value for folder
        if name == "folder":
            return True

        # default value for contentChannel
        elif name == "contentChannel":
            return "list"

        # default value for viewcontent
        elif name == "viewcontent":
            # we try to fix it according to the type of content...
            if self.__dict__["infoLabels"]["mediatype"] == 'movie':
                viewcontent = 'movies'
            elif self.__dict__["infoLabels"]["mediatype"] in ["tvshow", "season", "episode"]:
                viewcontent = "episodes"
            else:
                viewcontent = "files"

            self.__dict__["viewcontent"] = viewcontent
            return viewcontent

        # values ​​saved in infoLabels
        elif name in ["contentTitle", "contentPlot", "contentSerieName", "show", "contentType", "contentEpisodeTitle",
                      "contentSeason", "contentEpisodeNumber", "contentThumbnail", "plot", "duration",
                      "contentQuality", "quality"]:
            if name == "contentTitle":
                return self.__dict__["infoLabels"]["title"]
            elif name == "contentPlot" or name == "plot":
                return self.__dict__["infoLabels"]["plot"]
            elif name == "contentSerieName" or name == "show":
                return self.__dict__["infoLabels"]["tvshowtitle"]
            elif name == "contentType":
                ret = self.__dict__["infoLabels"]["mediatype"]
                if ret == 'list' and self.__dict__.get("fulltitle", None):  # backward compatibility
                    ret = 'movie'
                    self.__dict__["infoLabels"]["mediatype"] = ret
                return ret
            elif name == "contentEpisodeTitle":
                return self.__dict__["infoLabels"]["episodeName"]
            elif name == "contentSeason":
                return self.__dict__["infoLabels"]["season"]
            elif name == "contentEpisodeNumber":
                return self.__dict__["infoLabels"]["episode"]
            elif name == "contentThumbnail":
                return self.__dict__["infoLabels"]["thumbnail"]
            elif name == "contentQuality" or name == "quality":
                return self.__dict__["infoLabels"]["quality"]
            else:
                return self.__dict__["infoLabels"][name]

        # default value for all other attributes
        else:
            return ""

    def __str__(self):
        return '\r\t' + self.tostring('\r\t')

    def __eq__(self, other):
        if type(other) == Item:
            return self.__dict__ == other.__dict__
        else:
            return False

    def set_parent_content(self, parentContent):
        """
        Fill the contentDetails fields with the information of the item "parent"
        @param parentContent: item father
        @type parentContent: item
        """
        # Check that parentContent is an Item
        if not type(parentContent) == type(self):
            return
        # Copy all the attributes that start with "content" and are declared and the infoLabels
        for attr in parentContent.__dict__:
            if attr.startswith("content") or attr == "infoLabels":
                self.__setattr__(attr, parentContent.__dict__[attr])

    def tostring(self, separator=", "):
        """
        Generate a text string with the item's data for the log
        Use: logger.info(item.tostring())
        @param separator: string to be used as a separator
        @type separator: str
        '"""
        dic = self.__dict__.copy()

        # We add the content fields... if they have any value
        for key in ["contentTitle", "contentPlot", "contentSerieName", "contentEpisodeTitle",
                    "contentSeason", "contentEpisodeNumber", "contentThumbnail"]:
            value = self.__getattr__(key)
            if value:
                dic[key] = value

        if 'mediatype' in self.__dict__["infoLabels"]:
            dic["contentType"] = self.__dict__["infoLabels"]['mediatype']

        ls = []
        for var in sorted(dic):
            if isinstance(dic[var], str):
                valor = "'%s'" % dic[var]
            elif isinstance(dic[var], InfoLabels):
                if separator == '\r\t':
                    valor = dic[var].tostring(',\r\t\t')
                else:
                    valor = dic[var].tostring()
            elif PY3 and isinstance(dic[var], bytes):
                valor = "'%s'" % dic[var].decode('utf-8')
            else:
                valor = str(dic[var])

            if PY3 and isinstance(var, bytes):
                var = var.decode('utf-8')
            ls.append(var + "= " + valor)

        return separator.join(ls)

    def tourl(self):
        """
        Generate a text string with the item data to create a url, to re-generate the Item use item.fromurl ().

        Use: url = item.tourl()
        """
        dump = json.dump(self.__dict__).encode("utf8")
        # if empty dict
        if not dump:
            # set a str to avoid b64encode fails
            dump = "".encode("utf8")
        return str(urllib.quote(base64.b64encode(dump)))

    def fromurl(self, url, silent=False):
        """
        Generate an item from a text string. The string can be created by the tourl () function or have
        the old format: plugin: //plugin.video.kod/? channel = ... (+ other parameters)
        Use: item.fromurl("string")

        @param url: url
        @type url: str
        """
        if "?" in url:
            url = url.split("?")[1]
        decoded = False
        try:
            str_item = base64.b64decode(urllib.unquote(url))
            json_item = json.load(str_item, object_hook=self.toutf8, silent=silent)
            if json_item is not None and len(json_item) > 0:
                self.__dict__.update(json_item)
                decoded = True
        except:
            pass

        if not decoded:
            url = urllib.unquote_plus(url)
            dct = dict([[param.split("=")[0], param.split("=")[1]] for param in url.split("&") if "=" in param])
            self.__dict__.update(dct)
            self.__dict__ = self.toutf8(self.__dict__)

        if 'infoLabels' in self.__dict__ and not isinstance(self.__dict__['infoLabels'], InfoLabels):
            self.__dict__['infoLabels'] = InfoLabels(self.__dict__['infoLabels'])

        return self

    def tojson(self, path=""):
        from core import filetools
        """
        Create a JSON from the item, to save favorite files, download list, etc....
        If a path is specified, it saves it in the specified path, if not, it returns the string json
        Applications: item.tojson(path="path\archivo\json.json")
                      file.write(item.tojson())

        @param path: path
        @type path: str
        """
        if path:
            #open(path, "wb").write(json.dump(self.__dict__))
            res = filetools.write(path, json.dump(self.__dict__))
        else:
            return json.dump(self.__dict__)

    def fromjson(self, json_item=None, path=""):
        from core import filetools
        """
        Generate an item from a JSON file
        If a path is specified, it directly reads the file, if not, it reads the passed text string.
        Applications: item = Item().fromjson(path="path\archivo\json.json")
                      item = Item().fromjson("Cadena de texto json")

        @param json_item: item
        @type json_item: json
        @param path: path
        @type path: str
        """
        if path:
            if filetools.exists(path):
                #json_item = open(path, "rb").read()
                json_item = filetools.read(path)
            else:
                json_item = {}

        if json_item is None:
            json_item = {}

        item = json.load(json_item, object_hook=self.toutf8)
        self.__dict__.update(item)

        if 'infoLabels' in self.__dict__ and not isinstance(self.__dict__['infoLabels'], InfoLabels):
            self.__dict__['infoLabels'] = InfoLabels(self.__dict__['infoLabels'])

        return self

    def clone(self, **kwargs):
        """
        Generate a new item by cloning the current item
        Applications: NewItem = item.clone()
                      NuewItem = item.clone(title="New Title", action = "New Action")
        """
        newitem = copy.deepcopy(self)
        if "infoLabels" in kwargs:
            kwargs["infoLabels"] = InfoLabels(kwargs["infoLabels"])
        for kw in kwargs:
            newitem.__setattr__(kw, kwargs[kw])
        newitem.__dict__ = newitem.toutf8(newitem.__dict__)

        return newitem

    @staticmethod
    def decode_html(value):
        """
        Decode the HTML entities
        @param value: value to decode
        @type value: str
        """
        try:
            unicode_title = unicode(value, "utf8", "ignore")
            return unescape(unicode_title).encode("utf8")
        except:
            if PY3 and isinstance(value, bytes):
                value = value.decode("utf8")
            return value

    def toutf8(self, *args):
        """
        Pass the item to utf8
        """
        if len(args) > 0:
            value = args[0]
        else:
            value = self.__dict__

        if isinstance(value, unicode):
            value = value.encode("utf8")
            if PY3: value = value.decode("utf8")
            return value

        elif not PY3 and isinstance(value, str):
            return unicode(value, "utf8", "ignore").encode("utf8")

        elif PY3 and isinstance(value, bytes):
            return value.decode("utf8")

        elif isinstance(value, list):
            for x, key in enumerate(value):
                value[x] = self.toutf8(value[x])
            return value

        elif isinstance(value, dict):
            newdct = {}
            for key in value:
                value_unc = self.toutf8(value[key])
                key_unc = self.toutf8(key)
                #if isinstance(key, unicode):
                #    key = key.encode("utf8")

                newdct[key_unc] = value_unc

            if len(args) > 0:
                if isinstance(value, InfoLabels):
                    return InfoLabels(newdct)
                else:
                    return newdct

        else:
            return value
