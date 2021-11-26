# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# XBMC Config Menu
# ------------------------------------------------------------

from __future__ import division
import sys, os, inspect, xbmcgui, xbmc
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int
from builtins import range
from past.utils import old_div

from core import channeltools, jsontools, servertools, filetools, support
from platformcode import config, logger, platformtools
from core.support import match

if sys.version_info[0] >= 3:
    from concurrent import futures
else:
    from concurrent_py2 import futures

HEADER = 1
LIST = 100
SCROLLBAR = 101

BUTTONS = 200
MUP = 300
MDN = 301
DEL = 302
CONTROLS = [MUP, MDN, DEL]

LEFT = 1
RIGHT =2
UP = 3
DOWN = 4
SCROLLDOWN = 104
SCROLLUP = 105
EXIT = 10
BACKSPACE = 92
PREVIOUS = 10

GESTUREBEGIN = 501
GESTUREPAN = 504

def title(label):
    matches = support.match(label, patron=r'@(\d+)').matches
    if matches:
        for m in matches:
            label = label.replace('@' + m, config.getLocalizedString(int(m)))

    return label

def getControlList(c, v=None):
    labels = []
    values = []
    currents = {}
    if v == None: v = c.get('default', 0)
    if c.get('lvalues'):
        labels = [title(v) for v in c['lvalues']]
        values = range(0, len(labels))

    elif c.get('dvalues'):
        for l, v in c['dvalues'].items():
            labels.append(l)
            values.append(v)
        if v in values: v = values.index(v)

    elif c.get('values'):
        values = c['values']
        labels = [str(v) for v in values]
        if v in values: v = values.index(v)

    elif c.get('rvalues'):
        values = range(c['rvalues'][0], c['rvalues'][1] + 1, c['rvalues'][2])
        labels = [str(v) for v in values]

    if labels and values:
        currents = {'label':labels[v], 'value':values[v]}

    return labels, values, currents
class SettingsWindow(xbmcgui.WindowXMLDialog):
    def start(self, *args, **kwargs):
        logger.debug()

        # Params
        # logger.dbg()
        self.controls = kwargs.get('list_controls', [])
        self.values = kwargs.get('dict_values', {})
        self.caption = kwargs.get('caption', '')
        self.callback = kwargs.get('callback', None)
        self.item = kwargs.get('item', None)
        self.customButtons = kwargs.get('custom_buttons', [kwargs.get('custom_button', {})])
        self.listPosition = 0
        self.buttonPosition = 0

        channelpath = kwargs.get('channelpath', inspect.currentframe().f_back.f_back.f_code.co_filename)

        if channelpath:
            self.channel = filetools.basename(channelpath).replace('.py', '')
            self.ch_type = filetools.basename(filetools.dirname(channelpath))

        if not self.controls:
            self.controls, default_values = channeltools.get_channel_controls_settings(self.channel)

        if not self.caption:
            if self.ch_type in ['channels', 'specials']:
                self.caption = config.getLocalizedString(30100) + ' - ' + channeltools.get_channel_json(self.channel)['name']
            elif self.ch_type in ['servers']:
                self.caption = config.getLocalizedString(30100) + ' - ' + servertools.get_server_parameters(self.channel)['name']

        self.ret = None
        self.doModal()
        return self.ret

    def onInit(self):
        xbmc.sleep(150)
        self.getControl(HEADER).setLabel(self.caption)
        self.LIST = self.getControl(LIST)
        self.BUTTONS = self.getControl(BUTTONS)
        self.makeControls()
        self.makeButtons()


    def makeControls(self, index = 0, index2 = None):
        itemlist = []
        hidden = 0
        controllist = []

        def makeControl(n, control):
            label2 = ''
            currentval = control.get('control', config.getSetting(control['id'], self.channel))

            control['control'] = currentval
            label = title(control.get('label', ''))
            if control.get('submenu', False):
                label = "•• " + label

            if control['type'] == 'list':
                if type(currentval) == list: currentval = control['default']
                labels, values, currents = getControlList(control, currentval)
                label2 = currents.get('label', '')
            elif control['type'] == 'multi':
                if type(currentval) == list:
                    currents = [c for l, v, c in [getControlList(control, v) for v in currentval]]
                else:
                    l, v, c = getControlList(control, currentval)
                    currents = [c]
                label2 = ', '.join(c.get('label', '') for c in currents)
            elif control['type'] == 'text':
                if currentval and control.get('hidden', False) or control.get('mode', '') == 'pass' : label2 = '•' * 10
                else: label2 = str(currentval if currentval else '')
            else: label2 = str(currentval)
            item = xbmcgui.ListItem(label, label2)
            item.setProperty('type', control['type'])
            item.setProperties({'id': str(n), 'type':control['type']})
            if control['type'] == 'bool': item.setProperty('bool', 'on.png' if currentval else 'off.png')
            return n, item

        # for n, control in enumerate(self.controls):
        #     controllist.append(makeControl(n, control))

        with futures.ThreadPoolExecutor() as executor:
            itlist = [executor.submit(makeControl, n, control) for n, control in enumerate(self.controls)]
            for res in futures.as_completed(itlist):
                if res.result():
                    controllist.append(res.result())

        controllist.sort(key=lambda x: x[0])
        for n, item in controllist:
            if self.evalute('visible', n):
                item.setProperty('enabled', str(self.evalute('enabled', n)))
                itemlist.append(item)
            elif index >= n:
                hidden += 1
        if hidden:
            index -= 1

        self.LIST.reset()
        self.LIST.addItems(itemlist)
        self.setFocusId(LIST)
        self.LIST.selectItem(index)
        if index2:
            self.setFocusId(index2)


    def makeButtons(self):
        for button in ['ok', 'close', 'reset'] + [b.get('icon', 'btn') for b in self.customButtons]:
            item = xbmcgui.ListItem(button)
            item.setArt({'button': button + '.png'})
            self.BUTTONS.addItem(item)


    def evalute(self, name, index):
        ok = False
        control_value = None
        condition = self.controls[index].get(name, True)
        if type(condition) == bool:
            return condition
        conditions = support.match(condition, patron=r'''(!?eq|!?gt|!?lt)?\s*\(\s*([^, ]+)\s*,\s*["']?([^"'\)]+)["']?\)([+|])?''').matches

        for operator, _id, value, next in conditions:
            value = title(value)
            logger.debug('CONDITIONS', operator, _id, value, next)

            try:
                # The control to evaluate on has to be within range, otherwise it returns False
                if index + int(_id) < 0 or index + int(_id) >= len(self.controls):
                    return False

                else:
                    # Obtain the value of the control on which it is compared
                    control_value = self.controls[index + int(_id)]["control"]
                    if type(value) == str:
                        c = self.controls[index + int(_id)]
                        if c.get('lvalues'): control_value = title(c['lvalues'][control_value])
                        elif c.get('dvalues'): control_value = title(c['lvalues'][control_value])
                        else: return False
            except:
                for control in self.controls:
                    if control['id'] == int(_id):
                        control_value = control["control"]

            if not control_value:
                continue

            # Operations lt "less than" and gt "greater than" require comparisons to be numbers, otherwise it returns
            # False
            if operator in ["lt", "!lt", "gt", "!gt"]:
                try:
                    value = int(value)
                except ValueError:
                    return False

            # Operation eq "equal to"
            if operator in ["eq", "!eq"]:
                # int
                try:
                    value = int(value)
                except ValueError:
                    pass

                # bool
                if not isinstance(value, int) and value.lower() == "true":
                    value = True
                elif not isinstance(value, int) and value.lower() == "false":
                    value = False

            # Operation eq "equal to"
            if operator == "eq":
                if control_value == value:
                    ok = True
                else:
                    ok = False

            # Operation !eq "not equal to"
            if operator == "!eq":
                if not control_value == value:
                    ok = True
                else:
                    ok = False

            # operation "gt" "greater than"
            if operator == "gt":
                if control_value > value:
                    ok = True
                else:
                    ok = False

            # operation "!gt" "not greater than"
            if operator == "!gt":
                if not control_value > value:
                    ok = True
                else:
                    ok = False

            # operation "lt" "less than"
            if operator == "lt":
                if control_value < value:
                    ok = True
                else:
                    ok = False

            # operation "!lt" "not less than"
            if operator == "!lt":
                if not control_value < value:
                    ok = True
                else:
                    ok = False

            # Next operation, if it is "|" (or) and the result is True, there is no sense to follow, it is True
            if next == "|" and ok is True:
                break
            # Next operation, if it is "+" (and) and the result is False, there is no sense to follow, it is False
            if next == "+" and ok is False:
                break

        return ok


    def onClick(self, control):
        logger.debug('CONTROL', control)
        if control in [LIST] and self.getControl(control).getSelectedItem().getProperty('enabled') == 'False':
            pass
        elif control in [LIST]:
            item = self.LIST.getSelectedItem()
            _type = item.getProperty('type')
            _id = int(item.getProperty('id'))
            value = self.controls[_id]['control']

            if _type == 'bool':
                self.controls[_id]['control'] = False if value else True

            elif _type == 'list':
                labels, values, c = getControlList(self.controls[_id])

                default = labels.index(item.getLabel2())
                selection = platformtools.dialogSelect(item.getLabel(), labels, default)
                if selection > -1:
                    self.controls[_id]['control'] = values[selection]

            elif _type == 'multi':
                labels, values, c = getControlList(self.controls[_id])
                default = [labels.index(val.strip()) for val in item.getLabel2().split(',')]
                selection = platformtools.dialogMultiselect(item.getLabel(), labels, preselect=default)
                self.controls[_id]['control'] = [values[v] for v in selection]

            elif _type == 'text':
                mode = {'':None, 'number':0, 'date':1, 'time':2, 'ip':3, 'pass':4}[self.controls[_id].get('mode', '')]
                if mode != None:
                    self.controls[_id]['control'] = platformtools.dialogNumeric(4, item.getLabel(), self.controls[_id]['control'])
                else:
                    self.controls[_id]['control'] = platformtools.dialogInput(item.getLabel2(), item.getLabel(), hidden=self.controls[_id].get('hidden', False))

            elif _type == 'insert':
                self.insertControls(_id)

            self.makeControls(_id)

        elif control in [MUP]:
            pos = self.LIST.getSelectedPosition()
            if self.controls[pos-1]['type'] == 'insert' and self.controls[pos-1].get('label'):
                self.controls[pos], self.controls[pos-1] = self.controls[pos-1], self.controls[pos]
                self.makeControls(pos-1, MUP)
        elif control in [MDN]:
            pos = self.LIST.getSelectedPosition()
            if self.controls[pos+1]['type'] == 'insert' and self.controls[pos+1].get('label'):
                self.controls[pos], self.controls[pos+1] = self.controls[pos+1], self.controls[pos]
                self.makeControls(pos+1, MDN)
        elif control in [DEL]:
            pos = self.LIST.getSelectedPosition()
            if self.controls[pos]['type'] == 'insert' and self.controls[pos].get('label'):
                self.controls.pop(pos)
                self.makeControls(pos, DEL if self.controls[pos].get('label') else None)


        elif control in [BUTTONS]:
            pos = self.BUTTONS.getSelectedPosition()
            if pos == 0:
                self.saveControls()
                self.close()
            elif pos == 1:
                self.close()
            elif pos == 2:
                self.resetControls()
            else:
                self.customAction(pos)


    def onAction(self, action):
        action = action.getId()
        control = self.getFocusId()
        self.listPosition = self.LIST.getSelectedPosition()
        self.buttonPosition = self.BUTTONS.getSelectedPosition()
        item = self.LIST.getSelectedItem()
        # logger.dbg()
        if item:
            if item.getProperty('type') == 'label':
                if action in [UP]: self.LIST.selectItem(self.listPosition - 1)
                elif action in [DOWN]: self.LIST.selectItem(self.listPosition + 1)
            if action in [LEFT]:
                if control not in CONTROLS:
                    self.setFocusId(LIST)
                    self.LIST.selectItem(self.listPosition)
            if action in [RIGHT]:
                if control in [LIST]:
                    if item.getProperty('insert') and item.getLabel():
                        self.setFocusId(MUP)
                    elif len(self.controls) > 10:
                        self.setFocusId(SCROLLBAR)
                    else:
                        self.setFocusId(BUTTONS)
                        self.BUTTONS.selectItem(self.buttonPosition)
                if control in [SCROLLBAR]:
                    self.setFocusId(BUTTONS)
                    self.BUTTONS.selectItem(self.buttonPosition)
            if action in [BACKSPACE, EXIT]:
                self.close()


    def resetControls(self):
        # logger.dbg()
        controls = []
        for control in self.controls:
            if control['type'] == 'insert' and control.get('label'):
                continue
            control['control'] = control['default']
            controls.append(control)
        self.controls = controls
        self.makeControls()


    def customAction(self, position):
        _id = position - 3
        if '.' in self.customButtons[_id]['function']: package, function = self.customButtons[_id]['function'].rsplit('.', 1)
        else:
            package = '{}.{}'.format(self.ch_type, self.channel)
            function = self.customButtons[_id]['function']
        try: cb_channel = __import__(package, None, None, [package])
        except ImportError: logger.error('Unable to import ' + package)
        values = {}
        for control in self.controls:
            values[control['id']] = control['control']
        results = getattr(cb_channel, function)(self.item, values, self.customButtons[_id])

        btn = results.get('button',{})
        value = results.get('result',{})

        if btn.get('icon'): self.BUTTONS.getListItem(position).setArt({'button':btn['icon'] + '.png'})
        # if btn.get('label'): self.BUTTONS.getListItem(position).setLabel(btn['label'])

        _reload = False
        if value and type(values) == dict:
            for c in (self.controls):
                if c['type'] in value:
                    if c['control'] != value[c['type']]:
                        c['control'] = value[c['type']]
                        _reload = True
                if c['id'] in value:
                    if c['control'] != value[c['id']]:
                        c['control'] = value[c['id']]
                        _reload = True

        if _reload: self.makeControls(self.listPosition)


    def saveControls(self):
        if self.callback:
            if '.' in self.callback: package, self.callback = self.callback.rsplit('.', 1)
            else: package = '{}.{}'.format(self.ch_type, self.channel)
            try: cb_channel = __import__(package, None, None, [package])
            except ImportError: logger.error('Unable to import ' + package)
            values = {}
            for control in self.controls:
                if control['type'] == 'insert' and not control.get('label'): continue
                if control['type'] == 'list':
                    if control.get('dvalues'):
                        control['control'] = list(control['dvalues'].values())[control['control']]
                    elif control.get('values'):
                        control['control'] = control['values'][control['control']]
                values[control['id']] = control['control']
            self.return_value = getattr(cb_channel, self.callback)(self.item, values)
        for control in self.controls:
            if control['type'] == 'insert': continue
            if control['type'] == 'list':
                if control.get('dvalues'):
                    control['control'] = list(control['dvalues'].values())[control['control']]
                elif control.get('values'):
                    control['control'] = control['values'][control['control']]
            if self.ch_type in ['channels', 'specials']:
                config.setSetting(control['id'], control['control'], self.channel)
            elif self.ch_type in ['servers']:
                config.setSetting(control['id'], control['control'], server=self.channel)


    def insertControls(self, _id):
        if '.' in self.controls[_id]['function']: package, function = self.controls[_id]['function'].rsplit('.', 1)
        else:
            package = '{}.{}'.format(self.ch_type, self.channel)
            function = self.controls[_id]['function']
        try: cb_channel = __import__(package, None, None, [package])
        except ImportError: logger.error('Unable to import ' + package)
        values = {}
        for control in self.controls:
            values[control['id']] = control['control']
        results = getattr(cb_channel, function)(self.item, values)

        for n, result in enumerate(results):
            self.controls.insert(_id, result)
class ControlEdit(xbmcgui.ControlButton):
    def __new__(cls, *args, **kwargs):
        del kwargs["isPassword"]
        del kwargs["window"]
        args = list(args)
        return xbmcgui.ControlButton.__new__(cls, *args, **kwargs)

    def __init__(self, *args, **kwargs):
        self.isPassword = kwargs["isPassword"]
        self.window = kwargs["window"]
        self.label = ""
        self.text = ""
        self.textControl = xbmcgui.ControlLabel(self.getX(), self.getY(), self.getWidth(), self.getHeight(), self.text,
                                                font=kwargs["font"], textColor=kwargs["textColor"], alignment= 4 | 1)
        self.window.addControl(self.textControl)

    def setLabel(self, val):
        self.label = val
        xbmcgui.ControlButton.setLabel(self, val)

    def getX(self):
        return xbmcgui.ControlButton.getPosition(self)[0]

    def getY(self):
        return xbmcgui.ControlButton.getPosition(self)[1]

    def setEnabled(self, e):
        xbmcgui.ControlButton.setEnabled(self, e)
        self.textControl.setEnabled(e)

    def setWidth(self, w):
        xbmcgui.ControlButton.setWidth(self, w)
        self.textControl.setWidth(old_div(w, 2))

    def setHeight(self, w):
        xbmcgui.ControlButton.setHeight(self, w)
        self.textControl.setHeight(w)

    def setPosition(self, x, y):
        xbmcgui.ControlButton.setPosition(self, x, y)
        if xbmcgui.__version__ == "1.2":
            self.textControl.setPosition(x + self.getWidth(), y)
        else:
            self.textControl.setPosition(x + old_div(self.getWidth(), 2), y)

    def setText(self, text):
        self.text = text
        if self.isPassword:
            self.textControl.setLabel("*" * len(self.text))
        else:
            self.textControl.setLabel(self.text)

    def getText(self):
        return self.text


if not hasattr(xbmcgui, "ControlEdit"):
    xbmcgui.ControlEdit = ControlEdit
