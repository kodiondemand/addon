# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------------
# Scraper tools v2 for reading and processing web elements
# --------------------------------------------------------------------------------

import re
import time

import urlparse

from core.entities import html5
from platformcode import logger


def printMatches(matches):
    i = 0
    for match in matches:
        logger.info("%d %s" % (i, match))
        i = i + 1


def find_single_match(data, patron, index=0):
    try:
        matches = re.findall(patron, data, flags=re.DOTALL)
        return matches[index]
    except:
        return ""


# Parse string and extracts multiple matches using regular expressions
def find_multiple_matches(text, pattern):
    return re.findall(pattern, text, re.DOTALL)


# Convierte los codigos html "&ntilde;" y lo reemplaza por "ñ" caracter unicode utf-8
def decodeHtmlentities(data):
    entity_re = re.compile("&(#?)(\d{1,5}|\w{1,8})(;?)")

    def substitute_entity(match):
        ent = match.group(2) + match.group(3)
        res = ""
        while not ent in html5 and not ent.endswith(";") and match.group(1) != "#":
            # Excepción para cuando '&' se usa como argumento en la urls contenidas en los datos
            try:
                res = ent[-1] + res
                ent = ent[:-1]
            except:
                break

        if match.group(1) == "#":
            ent = unichr(int(ent.replace(";", "")))
            return ent.encode('utf-8')
        else:
            cp = html5.get(ent)
            if cp:
                return cp.decode("unicode-escape").encode('utf-8') + res
            else:
                return match.group()

    return entity_re.subn(substitute_entity, data)[0]


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

    # Sustituye acentos y eñes
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

    # Pasa a minúsculas
    title = title.lower().strip()

    # Elimina caracteres no válidos
    validchars = "abcdefghijklmnopqrstuvwxyz1234567890- "
    title = ''.join(c for c in title if c in validchars)

    # Sustituye espacios en blanco duplicados y saltos de línea
    title = re.compile("\s+", re.DOTALL).sub(" ", title)

    # Sustituye espacios en blanco por guiones
    title = re.compile("\s", re.DOTALL).sub("-", title.strip())

    # Sustituye espacios en blanco duplicados y saltos de línea
    title = re.compile("\-+", re.DOTALL).sub("-", title)

    # Arregla casos especiales
    if title.startswith("-"):
        title = title[1:]

    if title == "":
        title = "-" + str(time.time())

    return title


def remove_htmltags(string):
    return re.sub('<[^<]+?>', '', string)


def remove_show_from_title(title, show):
    # print slugify(title)+" == "+slugify(show)
    # Quita el nombre del programa del título
    if slugify(title).startswith(slugify(show)):

        # Convierte a unicode primero, o el encoding se pierde
        title = unicode(title, "utf-8", "replace")
        show = unicode(show, "utf-8", "replace")
        title = title[len(show):].strip()

        if title.startswith("-"):
            title = title[1:].strip()

        if title == "":
            title = str(time.time())

        # Vuelve a utf-8
        title = title.encode("utf-8", "ignore")
        show = show.encode("utf-8", "ignore")

    return title


# scrapertools.get_filename_from_url(media_url)[-4:]
def get_filename_from_url(url):
    parsed_url = urlparse.urlparse(url)
    try:
        filename = parsed_url.path
    except:
        # Si falla es porque la implementación de parsed_url no reconoce los atributos como "path"
        if len(parsed_url) >= 4:
            filename = parsed_url[2]
        else:
            filename = ""

    if "/" in filename:
        filename = filename.split("/")[-1]

    return filename


def get_domain_from_url(url):
    parsed_url = urlparse.urlparse(url)
    try:
        filename = parsed_url.netloc
    except:
        # Si falla es porque la implementación de parsed_url no reconoce los atributos como "path"
        if len(parsed_url) >= 4:
            filename = parsed_url[1]
        else:
            filename = ""

    return filename


def get_season_and_episode(title):
    """
    Retorna el numero de temporada y de episodio en formato "1x01" obtenido del titulo de un episodio
    Ejemplos de diferentes valores para title y su valor devuelto:
        "serie 101x1.strm", "s101e1.avi", "t101e1.avi"  -> '101x01'
        "Name TvShow 1x6.avi" -> '1x06'
        "Temp 3 episodio 2.avi" -> '3x02'
        "Alcantara season 13 episodie 12.avi" -> '13x12'
        "Temp1 capitulo 14" -> '1x14'
        "Temporada 1: El origen Episodio 9" -> '' (entre el numero de temporada y los episodios no puede haber otro texto)
        "Episodio 25: titulo episodio" -> '' (no existe el numero de temporada)
        "Serie X Temporada 1" -> '' (no existe el numero del episodio)
    @type title: str
    @param title: titulo del episodio de una serie
    @rtype: str
    @return: Numero de temporada y episodio en formato "1x01" o cadena vacia si no se han encontrado
    """
    filename = ""

    patrons = ["(\d+)x(\d+)", "(?:s|t)(\d+)e(\d+)",
               "(?:season|temp\w*)\s*(\d+)\s*(?:capitulo|epi\w*)\s*(\d+)"]

    for patron in patrons:
        try:
            matches = re.compile(patron, re.I).search(title)
            if matches:
                filename = matches.group(1) + "x" + matches.group(2).zfill(2)
                break
        except:
            pass

    logger.info("'" + title + "' -> '" + filename + "'")

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
