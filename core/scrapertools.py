# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------------
# Scraper tools for reading and processing web elements
# --------------------------------------------------------------------------------

#from future import standard_library
#standard_library.install_aliases()
#from builtins import str
#from builtins import chr
import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

import re
import time

# from core import httptools
from core.entities import html5
from platformcode import logger


# def get_header_from_response(url, header_to_get="", post=None, headers=None):
#     header_to_get = header_to_get.lower()
#     response = httptools.downloadpage(url, post=post, headers=headers, only_headers=True)
#     return response.headers.get(header_to_get)


# def read_body_and_headers(url, post=None, headers=None, follow_redirects=False, timeout=None):
#     response = httptools.downloadpage(url, post=post, headers=headers, follow_redirects=follow_redirects,
#                                       timeout=timeout)
#     return response.data, response.headers


def printMatches(matches):
    i = 0
    for match in matches:
        logger.debug("%d %s" % (i, match))
        i = i + 1


def find_single_match(data, patron, index=0):
    try:
        if index == 0:
            matches = re.search(patron, data, flags=re.DOTALL)
            if matches:
                if len(matches.groups()) == 1:
                    return matches.group(1)
                elif len(matches.groups()) > 1:
                    return matches.groups()
                else:
                    return matches.group()
            else:
                return ""
        else:
            matches = re.findall(patron, data, flags=re.DOTALL)
            return matches[index]
    except:
        return ""


# Parse string and extracts multiple matches using regular expressions
def find_multiple_matches(text, pattern):
    return re.findall(pattern, text, re.DOTALL)


def find_multiple_matches_groups(text, pattern):
    r = re.compile(pattern)
    return [m.groupdict() for m in r.finditer(text)]


# Convert html codes "&ntilde;" and replace it with "ñ" unicode utf-8 character
def decodeHtmlentities(data):
    entity_re = re.compile(r"&(#?)(\d{1,5}|\w{1,8})(;?)")

    def substitute_entity(match):
        ent = match.group(2) + match.group(3)
        res = ""
        while not ent in html5 and not ent.endswith(";") and match.group(1) != "#":
            # Exception for when '&' is used as an argument in the urls contained in the data
            try:
                res = ent[-1] + res
                ent = ent[:-1]
            except:
                break

        if match.group(1) == "#" and ent.replace(";", "").isdigit():
            ent = unichr(int(ent.replace(";", "")))
            return ent if PY3 else ent.encode('utf-8')
        else:
            cp = html5.get(ent)
            if cp:
                if PY3: return cp + res
                else: return cp.decode("unicode-escape").encode('utf-8') + res
            else:
                return match.group()

    return entity_re.subn(substitute_entity, data)[0]


def unescape(text):
    """
    Removes HTML or XML character references and entities from a text string.
    keep &amp;, &gt;, &lt; in the source code.
    from Fredrik Lundh
    http://effbot.org/zone/re-sub.htm#unescape-html
    """

    if not ('&' in text and ';' in text):
        return text

    def fixup(m):
        text = m.group(0)
        if text[:2] == "&#":
            # character reference
            try:
                if text[:3] == "&#x":
                    ret = unichr(int(text[3:-1], 16))
                    return ret if PY3 else ret.encode("utf-8")
                else:
                    ret = unichr(int(text[2:-1]))
                    return ret if PY3 else ret.encode("utf-8")

            except ValueError:
                logger.error("error de valor")
                pass
        else:
            # named entity
            try:
                if PY3:
                    import html.entities as htmlentitydefs
                else:
                    import htmlentitydefs
                ret = unichr(htmlentitydefs.name2codepoint[text[1:-1]]).encode("utf-8")
            except KeyError:
                logger.error("keyerror")
                pass
            except:
                pass
        # from core.support import dbg;dbg()
        if type(ret) != str:
            ret = ret.decode()
        return ret  # leave as is

    return re.sub("&#?\w+;", fixup, str(text))

    # Convert html codes "&ntilde;" and replace it with "ñ" unicode utf-8 character


# def decodeHtmlentities(string):
#     string = entitiesfix(string)
#     entity_re = re.compile("&(#?)(\d{1,5}|\w{1,8});")

#     def substitute_entity(match):
#         if PY3:
#             from html.entities import name2codepoint as n2cp
#         else:
#             from htmlentitydefs import name2codepoint as n2cp
#         ent = match.group(2)
#         if match.group(1) == "#":
#             return unichr(int(ent)).encode('utf-8')
#         else:
#             cp = n2cp.get(ent)

#             if cp:
#                 return unichr(cp).encode('utf-8')
#             else:
#                 return match.group()

#     return entity_re.subn(substitute_entity, string)[0]


# def entitiesfix(string):
#     # Las entidades comienzan siempre con el símbolo & , y terminan con un punto y coma ( ; ).
#     string = string.replace("&aacute", "&aacute;")
#     string = string.replace("&eacute", "&eacute;")
#     string = string.replace("&iacute", "&iacute;")
#     string = string.replace("&oacute", "&oacute;")
#     string = string.replace("&uacute", "&uacute;")
#     string = string.replace("&Aacute", "&Aacute;")
#     string = string.replace("&Eacute", "&Eacute;")
#     string = string.replace("&Iacute", "&Iacute;")
#     string = string.replace("&Oacute", "&Oacute;")
#     string = string.replace("&Uacute", "&Uacute;")
#     string = string.replace("&uuml", "&uuml;")
#     string = string.replace("&Uuml", "&Uuml;")
#     string = string.replace("&ntilde", "&ntilde;")
#     string = string.replace("&#191", "&#191;")
#     string = string.replace("&#161", "&#161;")
#     string = string.replace(";;", ";")
#     return string


def htmlclean(cadena):
    cadena = re.compile("<!--.*?-->", re.DOTALL).sub("", cadena)

    cadena = cadena.replace("<center>", "")
    cadena = cadena.replace("</center>", "")
    cadena = cadena.replace("<cite>", "")
    cadena = cadena.replace("</cite>", "")
    cadena = cadena.replace("<em>", "")
    cadena = cadena.replace("</em>", "")
    cadena = cadena.replace("<u>", "")
    cadena = cadena.replace("</u>", "")
    cadena = cadena.replace("<li>", "")
    cadena = cadena.replace("</li>", "")
    cadena = cadena.replace("<turl>", "")
    cadena = cadena.replace("</tbody>", "")
    cadena = cadena.replace("<tr>", "")
    cadena = cadena.replace("</tr>", "")
    cadena = cadena.replace("<![CDATA[", "")
    cadena = cadena.replace("<wbr>", "")
    cadena = cadena.replace("<Br />", " ")
    cadena = cadena.replace("<BR />", " ")
    cadena = cadena.replace("<Br>", " ")
    cadena = re.compile("<br[^>]*>", re.DOTALL).sub(" ", cadena)

    cadena = re.compile("<script.*?</script>", re.DOTALL).sub("", cadena)

    cadena = re.compile("<option[^>]*>", re.DOTALL).sub("", cadena)
    cadena = cadena.replace("</option>", "")

    cadena = re.compile("<button[^>]*>", re.DOTALL).sub("", cadena)
    cadena = cadena.replace("</button>", "")

    cadena = re.compile("<i[^>]*>", re.DOTALL).sub("", cadena)
    cadena = cadena.replace("</iframe>", "")
    cadena = cadena.replace("</i>", "")

    cadena = re.compile("<table[^>]*>", re.DOTALL).sub("", cadena)
    cadena = cadena.replace("</table>", "")

    cadena = re.compile("<td[^>]*>", re.DOTALL).sub("", cadena)
    cadena = cadena.replace("</td>", "")

    cadena = re.compile("<div[^>]*>", re.DOTALL).sub("", cadena)
    cadena = cadena.replace("</div>", "")

    cadena = re.compile("<dd[^>]*>", re.DOTALL).sub("", cadena)
    cadena = cadena.replace("</dd>", "")

    cadena = re.compile("<b[^>]*>", re.DOTALL).sub("", cadena)
    cadena = cadena.replace("</b>", "")

    cadena = re.compile("<font[^>]*>", re.DOTALL).sub("", cadena)
    cadena = cadena.replace("</font>", "")

    cadena = re.compile("<strong[^>]*>", re.DOTALL).sub("", cadena)
    cadena = cadena.replace("</strong>", "")

    cadena = re.compile("<small[^>]*>", re.DOTALL).sub("", cadena)
    cadena = cadena.replace("</small>", "")

    cadena = re.compile("<span[^>]*>", re.DOTALL).sub("", cadena)
    cadena = cadena.replace("</span>", "")

    cadena = re.compile("<a[^>]*>", re.DOTALL).sub("", cadena)
    cadena = cadena.replace("</a>", "")

    cadena = re.compile("<p[^>]*>", re.DOTALL).sub("", cadena)
    cadena = cadena.replace("</p>", "")

    cadena = re.compile("<ul[^>]*>", re.DOTALL).sub("", cadena)
    cadena = cadena.replace("</ul>", "")

    cadena = re.compile("<h1[^>]*>", re.DOTALL).sub("", cadena)
    cadena = cadena.replace("</h1>", "")

    cadena = re.compile("<h2[^>]*>", re.DOTALL).sub("", cadena)
    cadena = cadena.replace("</h2>", "")

    cadena = re.compile("<h3[^>]*>", re.DOTALL).sub("", cadena)
    cadena = cadena.replace("</h3>", "")

    cadena = re.compile("<h4[^>]*>", re.DOTALL).sub("", cadena)
    cadena = cadena.replace("</h4>", "")

    cadena = re.compile("<!--[^-]+-->", re.DOTALL).sub("", cadena)

    cadena = re.compile("<img[^>]*>", re.DOTALL).sub("", cadena)

    cadena = re.compile("<object[^>]*>", re.DOTALL).sub("", cadena)
    cadena = cadena.replace("</object>", "")
    cadena = re.compile("<param[^>]*>", re.DOTALL).sub("", cadena)
    cadena = cadena.replace("</param>", "")
    cadena = re.compile("<embed[^>]*>", re.DOTALL).sub("", cadena)
    cadena = cadena.replace("</embed>", "")

    cadena = re.compile("<title[^>]*>", re.DOTALL).sub("", cadena)
    cadena = cadena.replace("</title>", "")

    cadena = re.compile("<link[^>]*>", re.DOTALL).sub("", cadena)

    cadena = cadena.replace("\t", "")
    # cadena = entityunescape(cadena)
    return cadena


def slugify(title):
    # print title

    # Substitutes accents and eñes
    title = title.replace("Á", "a")
    title = title.replace("É", "e")
    title = title.replace("Í", "i")
    title = title.replace("Ó", "o")
    title = title.replace("Ú", "u")
    title = title.replace("á", "a")
    title = title.replace("é", "e")
    title = title.replace("í", "i")
    title = title.replace("ó", "o")
    title = title.replace("ú", "u")
    title = title.replace("À", "a")
    title = title.replace("È", "e")
    title = title.replace("Ì", "i")
    title = title.replace("Ò", "o")
    title = title.replace("Ù", "u")
    title = title.replace("à", "a")
    title = title.replace("è", "e")
    title = title.replace("ì", "i")
    title = title.replace("ò", "o")
    title = title.replace("ù", "u")
    title = title.replace("ç", "c")
    title = title.replace("Ç", "C")
    title = title.replace("Ñ", "n")
    title = title.replace("ñ", "n")
    title = title.replace("/", "-")
    title = title.replace("&amp;", "&")

    # Lowercase
    title = title.lower().strip()

    # Remove invalid characters
    validchars = "abcdefghijklmnopqrstuvwxyz1234567890- "
    title = ''.join(c for c in title if c in validchars)

    # Replace duplicate blanks and line breaks
    title = re.compile(r"\s+", re.DOTALL).sub(" ", title)

    # Replace blanks with hyphens
    title = re.compile(r"\s", re.DOTALL).sub("-", title.strip())

    # Replace duplicate blanks and line breaks
    title = re.compile(r"\-+", re.DOTALL).sub("-", title)

    # Fix special cases
    if title.startswith("-"):
        title = title[1:]

    if title == "":
        title = "-" + str(time.time())

    return title


def remove_htmltags(string):
    return re.sub('<[^<]+?>', '', string)


def remove_show_from_title(title, show):
    # print slugify(title)+" == "+slugify(show)
    # Remove program name from title
    if slugify(title).startswith(slugify(show)):

        # Convert to unicode first, or encoding is lost
        title = unicode(title, "utf-8", "replace")
        show = unicode(show, "utf-8", "replace")
        title = title[len(show):].strip()

        if title.startswith("-"):
            title = title[1:].strip()

        if title == "":
            title = str(time.time())

        # Return to utf-8
        title = title.encode("utf-8", "ignore")
        show = show.encode("utf-8", "ignore")

    return title


def get_filename_from_url(url):
    if PY3:
        import urllib.parse as urlparse                             # It is very slow in PY2. In PY3 it is native
    else:
        import urlparse                                             # We use the native of PY2 which is faster

    parsed_url = urlparse.urlparse(url)
    try:
        filename = parsed_url.path
    except:
        # If it fails it is because the implementation of parsed_url does not recognize the attributes as "path"
        if len(parsed_url) >= 4:
            filename = parsed_url[2]
        else:
            filename = ""

    if "/" in filename:
        filename = filename.split("/")[-1]

    return filename


def get_domain_from_url(url):
    if PY3:
       import urllib.parse as urlparse                             # It is very slow in PY2. In PY3 it is native
    else:
       import urlparse                                             # We use the native of PY2 which is faster

    parsed_url = urlparse.urlparse(url)
    try:
        filename = parsed_url.netloc
    except:
        # If it fails it is because the implementation of parsed_url does not recognize the attributes as "path"
        if len(parsed_url) >= 4:
            filename = parsed_url[1]
        else:
            filename = ""

    return filename


def get_season_and_episode(title):
    """
    Returns the season and episode number in "1x01" format obtained from the title of an episode
    Examples of different values ​​for title and its return value:
        "serie 101x1.strm", "s101e1.avi", "t101e1.avi"  -> '101x01'
        "Name TvShow 1x6.avi" -> '1x06'
        "Temp 3 episodio 2.avi" -> '3x02'
        "Alcantara season 13 episodie 12.avi" -> '13x12'
        "Temp1 capitulo 14" -> '1x14'
        "Temporada 1: El origen Episodio 9" -> '' (entre el numero de temporada y los episodios no puede haber otro texto)
        "Episodio 25: titulo episodio" -> '' (no existe el numero de temporada)
        "Serie X Temporada 1" -> '' (no existe el numero del episodio)
    @type title: str
    @param title: title of a series episode
    @rtype: str
    @return: Nseason and episode number in "1x01" format or empty string if not found
    """
    filename = ""

    patrons = ["(\d+)\s*[x-]\s*(\d+)", "(\d+)\s*×\s*(\d+)", "(?:[Ss]|[Tt])(\d+)\s?(?:[Ee]|Ep\.?)(\d+)",
               "(?:[Ss]tag|[Ss]eason|[Ss]tagione\w*)\s*(\d+)\s*(?:[Ee]pi|[Ee]pisode|[Ee]pisodio\w*)\s*(\d+)"]

    for patron in patrons:
        try:
            matches = re.compile(patron, re.I).search(title)
            if matches:
                filename =  str(int(matches.group(1))) + "x" + str(int(matches.group(2))).zfill(2)
                break
        except:
            pass

    logger.debug("'" + title + "' -> '" + filename + "'")

    return filename


def get_sha1(cadena):
    try:
        import hashlib
        devuelve = hashlib.sha1(cadena).hexdigest()
    except:
        import sha
        import binascii
        devuelve = binascii.hexlify(sha.new(cadena).digest())

    return devuelve


def get_md5(cadena):
    try:
        import hashlib
        devuelve = hashlib.md5(cadena).hexdigest()
    except:
        import md5
        import binascii
        devuelve = binascii.hexlify(md5.new(cadena).digest())

    return devuelve
