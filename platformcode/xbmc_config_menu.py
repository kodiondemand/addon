# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# XBMC Config Menu
# ------------------------------------------------------------

import inspect
import os

import xbmcgui
from core import channeltools
from core import servertools
from platformcode import config, logger


class SettingsWindow(xbmcgui.WindowXMLDialog):
    """ Clase derivada que permite utilizar cuadros de configuracion personalizados.

    Esta clase deriva de xbmcgui.WindowXMLDialog y permite crear un cuadro de dialogo con controles del tipo:
    Radio Button (bool), Cuadro de texto (text), Lista (list) y Etiquetas informativas (label).
    Tambien podemos personalizar el cuadro añadiendole un titulo (title).

    Metodo constructor:
        SettingWindow(listado_controles, dict_values, title, callback, item)
            Parametros:
                listado_controles: (list) Lista de controles a incluir en la ventana, segun el siguiente esquema:
                    (opcional)list_controls= [
                                {'id': "nameControl1",
                                  'type': "bool",                       # bool, text, list, label
                                  'label': "Control 1: tipo RadioButton",
                                  'color': '0xFFee66CC',                # color del texto en formato ARGB hexadecimal
                                  'default': True,
                                  'enabled': True,
                                  'visible': True
                                },
                                {'id': "nameControl2",
                                  'type': "text",                       # bool, text, list, label
                                  'label': "Control 2: tipo Cuadro de texto",
                                  'color': '0xFFee66CC',
                                  'default': "Valor por defecto",
                                  'hidden': False,                      # only for type = text Indica si hay que ocultar
                                                                            el texto (para passwords)
                                  'enabled': True,
                                  'visible': True
                                },
                                {'id': "nameControl3",
                                  'type': "list",                       # bool, text, list, label
                                  'label': "Control 3: tipo Lista",
                                  'color': '0xFFee66CC',
                                  'default': 0,                         # Indice del valor por defecto en lvalues
                                  'enabled': True,
                                  'visible': True,
                                  'lvalues':["item1", "item2", "item3", "item4"],  # only for type = list
                                },
                                {'id': "nameControl4",
                                  'type': "label",                       # bool, text, list, label
                                  'label': "Control 4: tipo Etiqueta",
                                  'color': '0xFFee66CC',
                                  'enabled': True,
                                  'visible': True
                                }]
                    Si no se incluye el listado_controles, se intenta obtener del json del canal desde donde se hace la
                    llamada.

                    El formato de los controles en el json es:
                        {
                            ...
                            ...
                            "settings": [
                                {
                                   "id": "name_control_1",
                                    "type": "bool",
                                    "label": "Control 1: tipo RadioButton",
                                    "default": false,
                                    "enabled": true,
                                    "visible": true,
                                    "color": "0xFFee66CC"
                                },
                                {
                                    "id": "name_control_2",
                                    "type": "text",
                                    "label": "Control 2: tipo Cuadro de texto",
                                    "default": "Valor por defecto",
                                    "hidden": true,
                                    "enabled": true,
                                    "visible": true,
                                    "color": "0xFFee66CC"
                                },
                                {
                                    "id": "name_control_3",
                                    "type": "list",
                                    "label": "Control 3: tipo Lista",
                                    "default": 0,
                                    "enabled": true,
                                    "visible": true,
                                    "color": "0xFFee66CC",
                                    "lvalues": [
                                        "item1",
                                        "item2",
                                        "item3",
                                        "item4"
                                    ]
                                },
                                {
                                    "id": "name_control_4",
                                    "type": "label",
                                    "label": "Control 4: tipo Etiqueta",
                                    "enabled": true,
                                    "visible": true,
                                    "color": "0xFFee66CC"
                                },
                            ]
                        }

                    Los campos 'label', 'default', 'enabled' y 'lvalues' pueden ser un numero precedido de '@'. En cuyo caso se
                    buscara el literal en el archivo string.xml del idioma seleccionado.
                    Los campos 'enabled' y 'visible' admiten los comparadores eq(), gt() e it() y su funcionamiento se
                    describe en: http://kodi.wiki/view/Add-on_settings#Different_types

                (opcional)dict_values: (dict) Diccionario que representa el par (id: valor) de los controles de la
                lista.
                    Si algun control de la lista no esta incluido en este diccionario se le asignara el valor por
                    defecto.
                        dict_values={"nameControl1": False,
                                     "nameControl2": "Esto es un ejemplo"}

                (opcional) caption: (str) Titulo de la ventana de configuracion. Se puede localizar mediante un numero
                precedido de '@'
                (opcional) callback (str) Nombre de la funcion, del canal desde el que se realiza la llamada, que sera
                invocada al pulsar el boton aceptar de la ventana. A esta funcion se le pasara como parametros el
                objeto 'item' y el dicionario 'dict_values'. Si este parametro no existe, se busca en el canal una
                funcion llamada 'cb_validate_config' y si existe se utiliza como callback.

            Retorno: Si se especifica 'callback' o el canal incluye 'cb_validate_config' se devolvera lo que devuelva
                esa funcion. Si no devolvera None

    Ejemplos de uso:
        platformtools.show_channel_settings(): Así tal cual, sin pasar ningún argumento, la ventana detecta de que canal
        se ha hecho la llamada,
            y lee los ajustes del json y carga los controles, cuando le das a Aceptar los vuelve a guardar.

        return platformtools.show_channel_settings(list_controls=list_controls, dict_values=dict_values, callback='cb',
        item=item):
            Así abre la ventana con los controles pasados y los valores de dict_values, si no se pasa dict_values, carga
            los valores por defecto de los controles,
            cuando le das a aceptar, llama a la función 'callback' del canal desde donde se ha llamado, pasando como
            parámetros, el item y el dict_values
    """

    def start(self, list_controls=None, dict_values=None, caption="", callback=None, item=None,
              custom_button=None, channelpath=None):
        logger.info()

        # Ruta para las imagenes de la ventana
        self.mediapath = os.path.join(config.get_runtime_path(), 'resources', 'skins', 'Default', 'media')

        # Capturamos los parametros
        self.list_controls = list_controls
        self.values = dict_values
        self.caption = caption
        self.callback = callback
        self.item = item

        if type(custom_button) == dict:
            self.custom_button = {}
            self.custom_button["label"] = custom_button.get("label", "")
            self.custom_button["function"] = custom_button.get("function", "")
            self.custom_button["visible"] = bool(custom_button.get("visible", True))
            self.custom_button["close"] = bool(custom_button.get("close", False))
        else:
            self.custom_button = None

        # Obtenemos el canal desde donde se ha echo la llamada y cargamos los settings disponibles para ese canal
        if not channelpath:
            channelpath = inspect.currentframe().f_back.f_back.f_code.co_filename
        self.channel = os.path.basename(channelpath).replace(".py", "")
        self.ch_type = os.path.basename(os.path.dirname(channelpath))
        logger.info('PATH= ' + channelpath)
        # Si no tenemos list_controls, hay que sacarlos del json del canal
        if not self.list_controls:

            # Si la ruta del canal esta en la carpeta "channels", obtenemos los controles y valores mediante chaneltools
            if os.path.join(config.get_runtime_path(), "channels") or os.path.join(config.get_runtime_path(), "specials")  in channelpath:

                # La llamada se hace desde un canal
                self.list_controls, default_values = channeltools.get_channel_controls_settings(self.channel)
                self.kwargs = {"channel": self.channel}

            # Si la ruta del canal esta en la carpeta "servers", obtenemos los controles y valores mediante servertools
            elif os.path.join(config.get_runtime_path(), "servers") in channelpath:

                # La llamada se hace desde un canal
                self.list_controls, default_values = servertools.get_server_controls_settings(self.channel)
                self.kwargs = {"server": self.channel}

            # En caso contrario salimos
            else:
                return None

        # Si no se pasan dict_values, creamos un dict en blanco
        if self.values is None:
            self.values = {}

        # Ponemos el titulo
        if self.caption == "":
            self.caption = str(config.get_localized_string(30100)) + " -- " + self.channel.capitalize()

        elif self.caption.startswith('@') and unicode(self.caption[1:]).isnumeric():
            self.caption = config.get_localized_string(int(self.caption[1:]))

        # Muestra la ventana
        self.return_value = None
        self.doModal()
        return self.return_value

    @staticmethod
    def set_enabled(c, val):
        if c["type"] == "list":
            c["control"].setEnabled(val)
            c["downBtn"].setEnabled(val)
            c["upBtn"].setEnabled(val)
            c["label"].setEnabled(val)
        else:
            c["control"].setEnabled(val)

    @staticmethod
    def set_visible(c, val):
        if c["type"] == "list":
            c["control"].setVisible(val)
            c["downBtn"].setVisible(val)
            c["upBtn"].setVisible(val)
            c["label"].setVisible(val)
        else:
            c["control"].setVisible(val)

    def evaluate_conditions(self):
        for c in self.list_controls:
            c["active"] = self.evaluate(self.list_controls.index(c), c["enabled"])
            self.set_enabled(c, c["active"])
            c["show"] = self.evaluate(self.list_controls.index(c), c["visible"])
            if not c["show"]:
                self.set_visible(c, c["show"])
        self.visible_controls = [c for c in self.list_controls if c["show"]]

    def evaluate(self, index, cond):
        import re

        # Si la condicion es True o False, no hay mas que evaluar, ese es el valor
        if type(cond) == bool:
            return cond

        # Obtenemos las condiciones
        conditions = re.compile("(!?eq|!?gt|!?lt)?\(([^,]+),[\"|']?([^)|'|\"]*)['|\"]?\)[ ]*([+||])?").findall(cond)
        for operator, id, value, next in conditions:
            # El id tiene que ser un numero, sino, no es valido y devuelve False
            try:
                id = int(id)
            except:
                return False

            # El control sobre el que evaluar, tiene que estar dentro del rango, sino devuelve False
            if index + id < 0 or index + id >= len(self.list_controls):
                return False

            else:
                # Obtenemos el valor del control sobre el que se compara
                c = self.list_controls[index + id]
                if c["type"] == "bool":
                    control_value = bool(c["control"].isSelected())
                if c["type"] == "text":
                    control_value = c["control"].getText()
                if c["type"] == "list":
                    control_value = c["label"].getLabel()
                if c["type"] == "label":
                    control_value = c["control"].getLabel()

                if value.startswith('@') and unicode(value[1:]).isnumeric():
                    value = config.get_localized_string(int(value[1:]))
            
            # Operaciones lt "menor que" y gt "mayor que", requieren que las comparaciones sean numeros, sino devuelve
            # False
            if operator in ["lt", "!lt", "gt", "!gt"]:
                try:
                    value = int(value)
                except ValueError:
                    return False

            # Operacion eq "igual a"
            if operator in ["eq", "!eq"]:
                # valor int
                try:
                    value = int(value)
                except ValueError:
                    pass

                # valor bool
                if value.lower() == "true":
                    value = True
                elif value.lower() == "false":
                    value = False

            # operacion "eq" "igual a"
            if operator == "eq":
                if control_value == value:
                    ok = True
                else:
                    ok = False

            # operacion "!eq" "no igual a"
            if operator == "!eq":
                if not control_value == value:
                    ok = True
                else:
                    ok = False

            # operacion "gt" "mayor que"
            if operator == "gt":
                if control_value > value:
                    ok = True
                else:
                    ok = False

            # operacion "!gt" "no mayor que"
            if operator == "!gt":
                if not control_value > value:
                    ok = True
                else:
                    ok = False

            # operacion "lt" "menor que"
            if operator == "lt":
                if control_value < value:
                    ok = True
                else:
                    ok = False

            # operacion "!lt" "no menor que"
            if operator == "!lt":
                if not control_value < value:
                    ok = True
                else:
                    ok = False

            # Siguiente operación, si es "|" (or) y el resultado es True, no tiene sentido seguir, es True
            if next == "|" and ok is True:
                break
            # Siguiente operación, si es "+" (and) y el resultado es False, no tiene sentido seguir, es False
            if next == "+" and ok is False:
                break

                # Siguiente operación, si es "+" (and) y el resultado es True, Seguira, para comprobar el siguiente valor
                # Siguiente operación, si es "|" (or) y el resultado es False, Seguira, para comprobar el siguiente valor

        return ok

    def add_control_label(self, c):
        control = xbmcgui.ControlLabel(0, -100, self.controls_width, 30, "", alignment=4, font=self.font,
                                       textColor=c["color"])

        self.addControl(control)

        control.setVisible(False)
        control.setLabel(c["label"])

        # Lo añadimos al listado
        c["control"] = control

    def add_control_list(self, c):
        control = xbmcgui.ControlButton(0, -100, self.controls_width, self.height_control,
                                        c["label"], os.path.join(self.mediapath, 'Controls', 'MenuItemFO.png'),
                                        os.path.join(self.mediapath, 'Controls', 'MenuItemNF.png'),
                                        0, textColor=c["color"],
                                        font=self.font)

        label = xbmcgui.ControlLabel(0, -100, self.controls_width - 30, self.height_control,
                                     "", font=self.font, textColor=c["color"], alignment=4 | 1)

        upBtn = xbmcgui.ControlButton(0, -100, 20, 15, "",
                                      focusTexture=os.path.join(self.mediapath, 'Controls', 'spinUp-Focus.png'),
                                      noFocusTexture=os.path.join(self.mediapath, 'Controls', 'spinUp-noFocus.png'))

        downBtn = xbmcgui.ControlButton(0, -100 + 15, 20, 15, "",
                                        focusTexture=os.path.join(self.mediapath, 'Controls', 'spinDown-Focus.png'),
                                        noFocusTexture=os.path.join(self.mediapath, 'Controls', 'spinDown-noFocus.png'))

        self.addControl(control)
        self.addControl(label)
        self.addControl(upBtn)
        self.addControl(downBtn)

        control.setVisible(False)
        label.setVisible(False)
        upBtn.setVisible(False)
        downBtn.setVisible(False)
        label.setLabel(c["lvalues"][self.values[c["id"]]])

        c["control"] = control
        c["label"] = label
        c["downBtn"] = downBtn
        c["upBtn"] = upBtn

    def add_control_text(self, c):
        if xbmcgui.ControlEdit == ControlEdit:
            control = xbmcgui.ControlEdit(0, -100, self.controls_width, self.height_control,
                                          c["label"], os.path.join(self.mediapath, 'Controls', 'MenuItemFO.png'),
                                          os.path.join(self.mediapath, 'Controls', 'MenuItemNF.png'),
                                          0, textColor=c["color"],
                                          font=self.font, isPassword=c["hidden"], window=self)

        else:
            control = xbmcgui.ControlEdit(0, -100, self.controls_width - 5, self.height_control,
                                          c["label"], self.font, c["color"], '', 4, isPassword=c["hidden"],
                                          focusTexture=os.path.join(self.mediapath, 'Controls', 'MenuItemFO.png'),
                                          noFocusTexture=os.path.join(self.mediapath, 'Controls', 'MenuItemNF.png'))

        self.addControl(control)

        control.setVisible(False)
        control.setLabel(c["label"])
        # frodo fix
        s = self.values[c["id"]]
        if s is None:
            s = ''
        control.setText(s)
        # control.setText(self.values[c["id"]])
        control.setWidth(self.controls_width - 5)
        control.setHeight(self.height_control)

        c["control"] = control

    def add_control_bool(self, c):
        # Versiones antiguas no admite algunas texturas
        if xbmcgui.__version__ in ["1.2", "2.0"]:
            control = xbmcgui.ControlRadioButton(0 - 10, -100, self.controls_width + 10, self.height_control,
                                                 label=c["label"], font=self.font, textColor=c["color"],
                                                 focusTexture=os.path.join(self.mediapath, 'Controls',
                                                                           'MenuItemFO.png'),
                                                 noFocusTexture=os.path.join(self.mediapath, 'Controls',
                                                                             'MenuItemNF.png'))
        else:
            control = xbmcgui.ControlRadioButton(0 - 10, -100, self.controls_width + 10,
                                                 self.height_control, label=c["label"], font=self.font,
                                                 textColor=c["color"],
                                                 focusTexture=os.path.join(self.mediapath, 'Controls',
                                                                           'MenuItemFO.png'),
                                                 noFocusTexture=os.path.join(self.mediapath, 'Controls',
                                                                             'MenuItemNF.png'),
                                                 focusOnTexture=os.path.join(self.mediapath, 'Controls',
                                                                             'radiobutton-focus.png'),
                                                 noFocusOnTexture=os.path.join(self.mediapath, 'Controls',
                                                                               'radiobutton-focus.png'),
                                                 focusOffTexture=os.path.join(self.mediapath, 'Controls',
                                                                              'radiobutton-nofocus.png'),
                                                 noFocusOffTexture=os.path.join(self.mediapath, 'Controls',
                                                                                'radiobutton-nofocus.png'))

        self.addControl(control)

        control.setVisible(False)
        control.setRadioDimension(x=self.controls_width + 10 - (self.height_control - 5), y=0,
                                  width=self.height_control - 5, height=self.height_control - 5)
        control.setSelected(self.values[c["id"]])

        c["control"] = control

    def onInit(self):
        self.getControl(10004).setEnabled(False)
        self.getControl(10005).setEnabled(False)
        self.getControl(10006).setEnabled(False)
        self.ok_enabled = False
        self.default_enabled = False

        #### Compatibilidad con Kodi 18 ####
        if config.get_platform(True)['num_version'] < 18:
            if xbmcgui.__version__ == "1.2":
                self.setCoordinateResolution(1)
            else:
                self.setCoordinateResolution(5)

        # Ponemos el título
        self.getControl(10002).setLabel(self.caption)

        if self.custom_button is not None:
            if self.custom_button['visible']:
                self.getControl(10006).setLabel(self.custom_button['label'])
            else:
                self.getControl(10006).setVisible(False)
                self.getControl(10004).setPosition(self.getControl(10004).getPosition()[0] + 80,
                                                   self.getControl(10004).getPosition()[1])
                self.getControl(10005).setPosition(self.getControl(10005).getPosition()[0] + 80,
                                                   self.getControl(10005).getPosition()[1])

        # Obtenemos las dimensiones del area de controles
        self.controls_width = self.getControl(10007).getWidth() - 20
        self.controls_height = self.getControl(10007).getHeight()
        self.controls_pos_x = self.getControl(10007).getPosition()[0] + self.getControl(10001).getPosition()[0] + 10
        self.controls_pos_y = self.getControl(10007).getPosition()[1] + self.getControl(10001).getPosition()[1]
        self.height_control = 35
        self.font = "font12"

        # En versiones antiguas: creamos 5 controles, de lo conrtario al hacer click al segundo control,
        # automaticamente cambia el label del tercero a "Short By: Name" no se porque...
        if xbmcgui.ControlEdit == ControlEdit:
            for x in range(5):
                control = xbmcgui.ControlRadioButton(-500, 0, 0, 0, "")
                self.addControl(control)

        for c in self.list_controls:
            # Saltamos controles que no tengan los valores adecuados
            if "type" not in c:
                continue
            if "label" not in c:
                continue
            if c["type"] != "label" and "id" not in c:
                continue
            if c["type"] == "list" and "lvalues" not in c:
                continue
            if c["type"] == "list" and not type(c["lvalues"]) == list:
                continue
            if c["type"] == "list" and not len(c["lvalues"]) > 0:
                continue
            if c["type"] != "label" and len(
                    [control.get("id") for control in self.list_controls if c["id"] == control.get("id")]) > 1:
                continue

            # Translation label y lvalues
            if c['label'].startswith('@') and unicode(c['label'][1:]).isnumeric():
                c['label'] = config.get_localized_string(int(c['label'][1:]))
            if c['type'] == 'list':
                lvalues = []
                for li in c['lvalues']:
                    if li.startswith('@') and unicode(li[1:]).isnumeric():
                        lvalues.append(config.get_localized_string(int(li[1:])))
                    else:
                        lvalues.append(li)
                c['lvalues'] = lvalues

            # Valores por defecto en caso de que el control no disponga de ellos
            if c["type"] == "bool":
                default = False
            elif c["type"] == "list":
                default = 0
            else:
                # label or text
                default = ""

            c["default"] = c.get("default", default)
            c["color"] = c.get("color", "0xFFFFFFFF")
            c["visible"] = c.get("visible", True)
            c["enabled"] = c.get("enabled", True)

            if c["type"] == "label" and "id" not in c:
                c["id"] = None

            if c["type"] == "text":
                c["hidden"] = c.get("hidden", False)

            # Decidimos si usar el valor por defecto o el valor guardado
            if c["type"] in ["bool", "text", "list"]:
                if c["id"] not in self.values:
                    if not self.callback:
                        self.values[c["id"]] = config.get_setting(c["id"], **self.kwargs)
                    else:
                        self.values[c["id"]] = c["default"]

            if c["type"] == "bool":
                self.add_control_bool(c)

            elif c["type"] == 'text':
                self.add_control_text(c)

            elif c["type"] == 'list':
                self.add_control_list(c)

            elif c["type"] == 'label':
                self.add_control_label(c)

        self.list_controls = [c for c in self.list_controls if "control" in c]

        self.evaluate_conditions()
        self.index = -1
        self.dispose_controls(0)
        self.getControl(100010).setVisible(False)
        self.getControl(10004).setEnabled(True)
        self.getControl(10005).setEnabled(True)
        self.getControl(10006).setEnabled(True)
        self.ok_enabled = True
        self.default_enabled = True
        self.check_default()
        self.check_ok(self.values)

    def dispose_controls(self, index, focus=False, force=False):
        show_controls = self.controls_height / self.height_control - 1

        visible_count = 0

        if focus:
            if not index >= self.index or not index <= self.index + show_controls:
                if index < self.index:
                    new_index = index
                else:
                    new_index = index - show_controls
            else:
                new_index = self.index
        else:

            if index + show_controls >= len(self.visible_controls): index = len(
                self.visible_controls) - show_controls - 1
            if index < 0: index = 0
            new_index = index

        if self.index <> new_index or force:
            for x, c in enumerate(self.visible_controls):
                if x < new_index or visible_count > show_controls or not c["show"]:
                    self.set_visible(c, False)
                else:
                    c["y"] = self.controls_pos_y + visible_count * self.height_control
                    visible_count += 1

                    if c["type"] != "list":
                        if c["type"] == "bool":
                            c["control"].setPosition(self.controls_pos_x - 10, c["y"])
                        else:
                            c["control"].setPosition(self.controls_pos_x, c["y"])

                    else:
                        c["control"].setPosition(self.controls_pos_x, c["y"])
                        if xbmcgui.__version__ == "1.2":
                            c["label"].setPosition(self.controls_pos_x + self.controls_width - 30, c["y"])
                        else:
                            c["label"].setPosition(self.controls_pos_x, c["y"])
                        c["upBtn"].setPosition(self.controls_pos_x + c["control"].getWidth() - 25, c["y"] + 3)
                        c["downBtn"].setPosition(self.controls_pos_x + c["control"].getWidth() - 25, c["y"] + 18)

                    self.set_visible(c, True)

            # Calculamos la posicion y tamaño del ScrollBar
            hidden_controls = len(self.visible_controls) - show_controls - 1
            if hidden_controls < 0: hidden_controls = 0

            scrollbar_height = self.getControl(10008).getHeight() - (hidden_controls * 3)
            scrollbar_y = self.getControl(10008).getPosition()[1] + (new_index * 3)
            self.getControl(10009).setPosition(self.getControl(10008).getPosition()[0], scrollbar_y)
            self.getControl(10009).setHeight(scrollbar_height)

        self.index = new_index

        if focus:
            self.setFocus(self.visible_controls[index]["control"])

    def check_ok(self, dict_values=None):
        if not self.callback:
            if dict_values:
                self.init_values = dict_values.copy()
                self.getControl(10004).setEnabled(False)
                self.ok_enabled = False

            else:
                if self.init_values == self.values:
                    self.getControl(10004).setEnabled(False)
                    self.ok_enabled = False
                else:
                    self.getControl(10004).setEnabled(True)
                    self.ok_enabled = True

    def check_default(self):
        if self.custom_button is None:
            def_values = dict([[c["id"], c.get("default")] for c in self.list_controls if not c["type"] == "label"])

            if def_values == self.values:
                self.getControl(10006).setEnabled(False)
                self.default_enabled = False
            else:
                self.getControl(10006).setEnabled(True)
                self.default_enabled = True

    def onClick(self, id):
        # Valores por defecto
        if id == 10006:
            if self.custom_button is not None:
                if self.custom_button["close"]:
                    self.close()

                if '.' in self.callback:
                    package, self.callback = self.callback.rsplit('.', 1)
                else:
                    package = '%s.%s' % (self.ch_type, self.channel)

                try:
                    cb_channel = __import__(package, None, None, [package])
                except ImportError:
                    logger.error('Imposible importar %s' % package)
                else:
                    self.return_value = getattr(cb_channel, self.custom_button['function'])(self.item, self.values)
                    if not self.custom_button["close"]:
                        if isinstance(self.return_value, dict) and self.return_value.has_key("label"):
                            self.getControl(10006).setLabel(self.return_value['label'])

                        for c in self.list_controls:
                            if c["type"] == "text":
                                c["control"].setText(self.values[c["id"]])
                            if c["type"] == "bool":
                                c["control"].setSelected(self.values[c["id"]])
                            if c["type"] == "list":
                                c["label"].setLabel(c["lvalues"][self.values[c["id"]]])

                        self.evaluate_conditions()
                        self.dispose_controls(self.index, force=True)

            else:
                for c in self.list_controls:
                    if c["type"] == "text":
                        c["control"].setText(c["default"])
                        self.values[c["id"]] = c["default"]
                    if c["type"] == "bool":
                        c["control"].setSelected(c["default"])
                        self.values[c["id"]] = c["default"]
                    if c["type"] == "list":
                        c["label"].setLabel(c["lvalues"][c["default"]])
                        self.values[c["id"]] = c["default"]

                self.evaluate_conditions()
                self.dispose_controls(self.index, force=True)
                self.check_default()
                self.check_ok()

        # Boton Cancelar y [X]
        if id == 10003 or id == 10005:
            self.close()

        # Boton Aceptar
        if id == 10004:
            self.close()
            if self.callback and '.' in self.callback:
                package, self.callback = self.callback.rsplit('.', 1)
            else:
                package = '%s.%s' % (self.ch_type, self.channel)

            cb_channel = None
            try:
                cb_channel = __import__(package, None, None, [package])
            except ImportError:
                logger.error('Imposible importar %s' % package)

            if self.callback:
                # Si existe una funcion callback la invocamos ...
                self.return_value = getattr(cb_channel, self.callback)(self.item, self.values)
            else:
                # si no, probamos si en el canal existe una funcion 'cb_validate_config' ...
                try:
                    self.return_value = getattr(cb_channel, 'cb_validate_config')(self.item, self.values)
                except AttributeError:
                    # ... si tampoco existe 'cb_validate_config'...
                    for v in self.values:
                        config.set_setting(v, self.values[v], **self.kwargs)

        # Controles de ajustes, si se cambia el valor de un ajuste, cambiamos el valor guardado en el diccionario de
        # valores
        # Obtenemos el control sobre el que se ha echo click
        control = self.getControl(id)

        # Lo buscamos en el listado de controles
        for cont in self.list_controls:

            # Si el control es un "downBtn" o "upBtn" son los botones del "list"
            # en este caso cambiamos el valor del list
            if cont["type"] == "list" and (cont["downBtn"] == control or cont["upBtn"] == control):

                # Para bajar una posicion
                if cont["downBtn"] == control:
                    index = cont["lvalues"].index(cont["label"].getLabel())
                    if index > 0:
                        cont["label"].setLabel(cont["lvalues"][index - 1])

                # Para subir una posicion
                elif cont["upBtn"] == control:
                    index = cont["lvalues"].index(cont["label"].getLabel())
                    if index < len(cont["lvalues"]) - 1:
                        cont["label"].setLabel(cont["lvalues"][index + 1])

                # Guardamos el nuevo valor en el diccionario de valores
                self.values[cont["id"]] = cont["lvalues"].index(cont["label"].getLabel())

            # Si esl control es un "bool", guardamos el nuevo valor True/False
            if cont["type"] == "bool" and cont["control"] == control:
                self.values[cont["id"]] = bool(cont["control"].isSelected())

            # Si esl control es un "text", guardamos el nuevo valor
            if cont["type"] == "text" and cont["control"] == control:
                # Versiones antiguas requieren abrir el teclado manualmente
                if xbmcgui.ControlEdit == ControlEdit:
                    import xbmc
                    keyboard = xbmc.Keyboard(cont["control"].getText(), cont["control"].getLabel(),
                                             cont["control"].isPassword)
                    keyboard.setHiddenInput(cont["control"].isPassword)
                    keyboard.doModal()
                    if keyboard.isConfirmed():
                        cont["control"].setText(keyboard.getText())

                self.values[cont["id"]] = cont["control"].getText()

        self.evaluate_conditions()
        self.dispose_controls(self.index, force=True)
        self.check_default()
        self.check_ok()

    # Versiones antiguas requieren esta funcion
    def onFocus(self, a):
        pass

    def onAction(self, raw_action):
        # Obtenemos el foco
        focus = self.getFocusId()

        action = raw_action.getId()
        # Accion 1: Flecha izquierda
        if action == 1:
            # Si el foco no está en ninguno de los tres botones inferiores, y esta en un "list" cambiamos el valor
            if focus not in [10004, 10005, 10006]:
                control = self.getFocus()
                for cont in self.list_controls:
                    if cont["type"] == "list" and cont["control"] == control:
                        index = cont["lvalues"].index(cont["label"].getLabel())
                        if index > 0:
                            cont["label"].setLabel(cont["lvalues"][index - 1])

                        # Guardamos el nuevo valor en el listado de controles
                        self.values[cont["id"]] = cont["lvalues"].index(cont["label"].getLabel())

                self.evaluate_conditions()
                self.dispose_controls(self.index, force=True)
                self.check_default()
                self.check_ok()

            # Si el foco está en alguno de los tres botones inferiores, movemos al siguiente
            else:
                if focus == 10006:
                    self.setFocusId(10005)
                if focus == 10005 and self.ok_enabled:
                    self.setFocusId(10004)

        # Accion 1: Flecha derecha
        elif action == 2:
            # Si el foco no está en ninguno de los tres botones inferiores, y esta en un "list" cambiamos el valor
            if focus not in [10004, 10005, 10006]:
                control = self.getFocus()
                for cont in self.list_controls:
                    if cont["type"] == "list" and cont["control"] == control:
                        index = cont["lvalues"].index(cont["label"].getLabel())
                        if index < len(cont["lvalues"]) - 1:
                            cont["label"].setLabel(cont["lvalues"][index + 1])

                        # Guardamos el nuevo valor en el listado de controles
                        self.values[cont["id"]] = cont["lvalues"].index(cont["label"].getLabel())

                self.evaluate_conditions()
                self.dispose_controls(self.index, force=True)
                self.check_default()
                self.check_ok()

            # Si el foco está en alguno de los tres botones inferiores, movemos al siguiente
            else:
                if focus == 10004:
                    self.setFocusId(10005)
                if focus == 10005 and self.default_enabled:
                    self.setFocusId(10006)

        # Accion 4: Flecha abajo
        elif action == 4:
            # Si el foco no está en ninguno de los tres botones inferiores, bajamos el foco en los controles de ajustes
            if focus not in [10004, 10005, 10006]:
                try:
                    focus_control = \
                        [self.visible_controls.index(c) for c in self.visible_controls if
                         c["control"] == self.getFocus()][
                            0]
                    focus_control += 1
                except:
                    focus_control = 0

                while not focus_control == len(self.visible_controls) and (
                                self.visible_controls[focus_control]["type"] == "label" or not
                        self.visible_controls[focus_control]["active"]):
                    focus_control += 1

                if focus_control >= len(self.visible_controls):
                    self.setFocusId(10005)
                    return

                self.dispose_controls(focus_control, True)

        # Accion 4: Flecha arriba
        elif action == 3:
            # Si el foco no está en ninguno de los tres botones inferiores, subimos el foco en los controles de ajustes
            if focus not in [10003, 10004, 10005, 10006]:
                try:
                    focus_control = \
                        [self.visible_controls.index(c) for c in self.visible_controls if
                         c["control"] == self.getFocus()][
                            0]
                    focus_control -= 1

                    while not focus_control == -1 and (self.visible_controls[focus_control]["type"] == "label" or not
                    self.visible_controls[focus_control]["active"]):
                        focus_control -= 1

                    if focus_control < 0: focus_control = 0
                except:
                    focus_control = 0

                self.dispose_controls(focus_control, True)

            # Si el foco está en alguno de los tres botones inferiores, ponemos el foco en el ultimo ajuste.
            else:
                focus_control = len(self.visible_controls) - 1
                while not focus_control == -1 and (self.visible_controls[focus_control]["type"] == "label" or not
                self.visible_controls[focus_control]["active"]):
                    focus_control -= 1
                if focus_control < 0: focus_control = 0

                self.setFocus(self.visible_controls[focus_control]["control"])

        # Accion 104: Scroll arriba
        elif action == 104:
            self.dispose_controls(self.index - 1)

        # Accion 105: Scroll abajo
        elif action == 105:
            self.dispose_controls(self.index + 1)

        # ACTION_PREVIOUS_MENU 10
        # ACTION_NAV_BACK 92
        elif action in [10, 92]:
            self.close()

        elif action == 504:

            if self.xx > raw_action.getAmount2():
                if (self.xx - int(raw_action.getAmount2())) / self.height_control:
                    self.xx -= self.height_control
                    self.dispose_controls(self.index + 1)
            else:
                if (int(raw_action.getAmount2()) - self.xx) / self.height_control:
                    self.xx += self.height_control
                self.dispose_controls(self.index - 1)
            return

        elif action == 501:
            self.xx = int(raw_action.getAmount2())


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
                                                font=kwargs["font"], textColor=kwargs["textColor"], alignment=4 | 1)
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
        self.textControl.setWidth(w / 2)

    def setHeight(self, w):
        xbmcgui.ControlButton.setHeight(self, w)
        self.textControl.setHeight(w)

    def setPosition(self, x, y):
        xbmcgui.ControlButton.setPosition(self, x, y)
        if xbmcgui.__version__ == "1.2":
            self.textControl.setPosition(x + self.getWidth(), y)
        else:
            self.textControl.setPosition(x + self.getWidth() / 2, y)

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
