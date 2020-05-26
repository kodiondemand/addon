# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from lib import js2py
import re

def unpack(source):
    fun, data = re.match("""eval\((function\(p,a,c,k,e,d\){.*?})\((['"].*?)\)\)$""", source.strip(), re.MULTILINE).groups()
    funPy = js2py.eval_js(fun)
    return eval('funPy(' + data + ')')

