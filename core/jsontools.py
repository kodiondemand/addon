# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------------
# json_tools - JSON load and parse functions with library detection
# --------------------------------------------------------------------------------

import traceback

from platformcode import logger
from inspect import stack

import json

import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int


def load(*args, **kwargs):
    silent = False
    if 'silent' in kwargs:
        silent = kwargs['silent']
        kwargs.pop('silent')

    if "object_hook" not in kwargs:
        kwargs["object_hook"] = to_utf8

    try:
        value = json.loads(*args, **kwargs)
    except:
        if not silent:
            logger.error("**NOT** able to load the JSON")
            logger.error(traceback.format_exc())
            if len(stack()) > 1:
                logger.error('ERROR STACK {}'.format(stack()[2]) )
        value = {}

    return value


def dump(*args, **kwargs):
    if not kwargs:
        kwargs = {"indent": 4, "skipkeys": True, "sort_keys": True, "ensure_ascii": True}

    try:
        value = json.dumps(*args, **kwargs)
    except:
        logger.error("JSON could **NOT** be saved")
        logger.error(traceback.format_exc())
        value = ""
    return value


def to_utf8(dct):
    if isinstance(dct, dict):
        return dict((to_utf8(key), to_utf8(value)) for key, value in dct.items())
    elif isinstance(dct, list):
        return [to_utf8(element) for element in dct]
    elif isinstance(dct, unicode):
        dct = dct.encode("utf8")
        if PY3: dct = dct.decode("utf8")
        return dct
    elif PY3 and isinstance(dct, bytes):
        return dct.decode('utf-8')
    else:
        return dct


def get_node_from_file(name_file, node, path=None):
    """
    Gets the node of a JSON file

    @param name_file: It can be the name of a channel or server (not including extension) or the name of a json file (with extension)
    @type name_file: str
    @param node: name of the node to obtain
    @type node: str
    @param path: Base path of the json file. By default the path of settings_channels.
    @return: dict with the node to return
    @rtype: dict
    """
    logger.debug()
    from platformcode import config
    from core import filetools

    dict_node = {}

    if not name_file.endswith(".json"):
        name_file += "_data.json"

    if not path:
        path = filetools.join(config.get_data_path(), "settings_channels")

    fname = filetools.join(path, name_file)

    if filetools.isfile(fname):
        data = filetools.read(fname)
        dict_data = load(data)

        check_to_backup(data, fname, dict_data)

        if node in dict_data:
            dict_node = dict_data[node]

    #logger.debug("dict_node: %s" % dict_node)

    return dict_node


def check_to_backup(data, fname, dict_data):
    """
    Check that if dict_data (conversion of the JSON file to dict) is not a dictionary, a file with data name fname.bk will be generated.

    @param data: fname file content
    @type data: str
    @param fname: name of the read file
    @type fname: str
    @param dict_data: dictionary name
    @type dict_data: dict
    """
    logger.debug()

    if not dict_data:
        logger.error("Error loading json from file %s" % fname)

        if data != "":
            # a new file is created
            from core import filetools
            title = filetools.write("%s.bk" % fname, data)
            if title != "":
                logger.error("There was an error saving the file: %s.bk" % fname)
            else:
                logger.debug("A copy with the name has been saved: %s.bk" % fname)
        else:
            logger.debug("The file is empty: %s" % fname)


def update_node(dict_node, name_file, node, path=None, silent=False):
    """
    update the json_data of a file with the last dictionary

    @param dict_node: dictionary with node
    @type dict_node: dict
    @param name_file: It can be the name of a channel or server (not including extension) or the name of a json file (with extension)
    @type name_file: str
    @param node: node to update
    @param path: Base path of the json file. By default the path of settings_channels.
    @return result: Returns True if it was written correctly or False if it gave an error
    @rtype: bool
    @return json_data
    @rtype: dict
    """
    if not silent: logger.info()

    from platformcode import config
    from core import filetools
    json_data = {}
    result = False

    if not name_file.endswith(".json"):
        name_file += "_data.json"

    if not path:
        path = filetools.join(config.get_data_path(), "settings_channels")

    fname = filetools.join(path, name_file)

    try:
        data = filetools.read(fname)
        dict_data = load(data)
        # it's a dict
        if dict_data:
            if node in dict_data:
                if not silent: logger.debug("   the key exists %s" % node)
                dict_data[node] = dict_node
            else:
                if not silent: logger.debug("   The key does NOT exist %s" % node)
                new_dict = {node: dict_node}
                dict_data.update(new_dict)
        else:
            if not silent: logger.debug("   It is NOT a dict")
            dict_data = {node: dict_node}
        json_data = dump(dict_data)
        result = filetools.write(fname, json_data)
    except:
        logger.error("Could not update %s" % fname)

    return result, json_data
