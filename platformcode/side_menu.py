# -*- coding: utf-8 -*-
# ------------------------------------------------------------

# from builtins import str
import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

import os
from core.item import Item
from core import jsontools
from platformcode import config, logger, launcher
import xbmc, xbmcgui

media_path = os.path.join(config.get_runtime_path(), "resources/skins/Default/media/side_menu/")
menu_settings_path = os.path.join(config.get_data_path(), "settings_channels", 'menu_settings_data.json')

if os.path.exists(menu_settings_path):
    menu_node = jsontools.get_node_from_file('menu_setting_data.json', 'menu')
else:
    menu_node = {'categoria actual':config.get_setting('category')}
    jsontools.update_node(menu_node, 'menu_settings_data.json', "menu")

info_language = ["de", "en", "es", "fr", "it", "pt"] # from videolibrary.json
def_lang = info_language[config.get_setting("info_language", "videolibrary")]

ACTION_SHOW_FULLSCREEN = 36
ACTION_GESTURE_SWIPE_LEFT = 511
ACTION_SELECT_ITEM = 7
ACTION_PREVIOUS_MENU = 10
ACTION_MOVE_LEFT = 1
ACTION_MOVE_RIGHT = 2
ACTION_MOVE_DOWN = 4
ACTION_MOVE_UP = 3

def set_menu_settings(item):
    if os.path.exists(menu_settings_path):
        menu_node = jsontools.get_node_from_file('menu_settings_data.json', 'menu')
    else:
        menu_node = {}
    menu_node['categoria actual'] = item.extra

    jsontools.update_node(menu_node, 'menu_settings_data.json', "menu")

def check_user_home(item):
    logger.debug()
    if os.path.exists(menu_settings_path):
        menu_node = jsontools.get_node_from_file('menu_settings_data.json', 'menu')
    if 'user_home' in menu_node:
        item = Item().fromurl(menu_node['user_home'])
    else:
        item = Item(channel="channelselector", action="getmainlist", viewmode="movie")
        from platformcode import platformtools
        undefined_start = platformtools.dialog_ok(config.get_localized_string(70664), config.get_localized_string(70665) + '\n' + config.get_localized_string(70666))
    return item

def set_custom_start(item):
    logger.debug()
    if os.path.exists(menu_settings_path):
        menu_node = jsontools.get_node_from_file('menu_settings_data.json', 'menu')
    else:
        menu_node={}
    parent_item= Item().fromurl(item.parent)
    parent_item.start=True
    config.set_setting("custom_start",True)
    if config.get_setting("news_start"):
        config.set_setting("news_start", False)
    menu_node['user_home']=parent_item.tourl()
    jsontools.update_node(menu_node, 'menu_settings_data.json', "menu")

def get_start_page():
    logger.debug()

    dictCategory = {
        config.get_localized_string(70137): 'peliculas',
        config.get_localized_string(30123): 'series',
        config.get_localized_string(30124): 'anime',
        config.get_localized_string(70018): 'infantiles',
        config.get_localized_string(60513): 'documentales',
        config.get_localized_string(70013): 'terror',
        config.get_localized_string(30124): 'castellano',
        config.get_localized_string(59976): 'latino',
        config.get_localized_string(70171): 'torrent',
    }
    category = dictCategory[config.get_setting("category")]

    custom_start= config.get_setting("custom_start")
    #if category != 'definido':
    if custom_start == False:
        item = Item(channel="news", action="novedades", extra=category, mode='silent')
    else:
        item = Item()
        item = side_menu.check_user_home(item)
    return item



def open_menu(item):
    main = Main('side_menu.xml', config.get_runtime_path())
    main.doModal()
    del main

def open_shortcut_menu(item):
    from platformcode import keymaptools
    keymaptools.open_shortcut_menu()


class Main(xbmcgui.WindowXMLDialog):
    def __init__(self, *args, **kwargs):
        self.items = []

    def onInit(self):
        #### Kodi 18 compatibility ####
        if config.get_platform(True)['num_version'] < 18:
            self.setCoordinateResolution(2)
        
        self.focus = -1
        self.buttons = []
        posx= 0
        posy= 145
        space = 30

        selected = 'selected0.png'
        width = 260
        height = 30
        textcolor = "0xFFCCCCCC"
        conditional_textcolor = "0xFF0081C2"
        shadow = "0x00000000"
        offsetx = 30
        offsety = 5
        font = 'font25_title'

        if config.get_setting('start_page'):
            label = config.get_localized_string(70663)
            self.button_start = xbmcgui.ControlButton(posx, posy, width, height, label, font=font, alignment=0x00000000,
                                                       noFocusTexture='', focusTexture=media_path + selected,
                                                       textColor=textcolor, shadowColor=shadow, textOffsetX=offsetx,
                                                       textOffsetY=offsety)
            self.addControl(self.button_start)
            self.buttons.append(self.button_start)

        posy += space * 2
        label = config.get_localized_string(70009)
        self.button_alfa = xbmcgui.ControlButton(posx, posy, width, height, label, font=font, alignment=0x00000000,
                                                 noFocusTexture='', focusTexture=media_path+selected, 
                                                 textColor=textcolor, shadowColor=shadow, textOffsetX=offsetx,
                                                 textOffsetY=offsety)
        self.addControl(self.button_alfa)
        self.buttons.append(self.button_alfa)


        posy += space
        label = config.get_localized_string(30100)
        self.button_config = xbmcgui.ControlButton(posx, posy, width, height, label, font=font, alignment=0x00000000,
                                                   noFocusTexture='', focusTexture=media_path + selected,
                                                   textColor=textcolor, shadowColor=shadow, textOffsetX=offsetx,
                                                   textOffsetY=offsety)
        self.addControl(self.button_config)
        self.buttons.append(self.button_config)
        posy += space*2
        label = config.get_localized_string(30122)
        self.button_peliculas = xbmcgui.ControlButton(posx, posy, width, height, label, font=font,
                                                      alignment=0x00000000, noFocusTexture='',
                                                      focusTexture=media_path+selected, textColor=textcolor,
                                                      shadowColor=shadow, textOffsetX=offsetx, textOffsetY=offsety)
        self.addControl(self.button_peliculas)
        self.buttons.append(self.button_peliculas)
        posy += space
        label = config.get_localized_string(70017)
        self.button_series = xbmcgui.ControlButton(posx, posy, width, height, label, font=font,
                                                   alignment=0x00000000, noFocusTexture='',
                                                   focusTexture=media_path+selected, textColor=textcolor,
                                                   shadowColor=shadow, textOffsetX=offsetx, textOffsetY=offsety)
        self.addControl(self.button_series)
        self.buttons.append(self.button_series)
        posy += space
        label = config.get_localized_string(30124)
        self.button_anime = xbmcgui.ControlButton(posx, posy, width, height, label, font=font, alignment=0x00000000,
                                                  noFocusTexture='', focusTexture=media_path+selected,
                                                  textColor=textcolor, shadowColor=shadow, textOffsetX=offsetx,
                                                  textOffsetY=offsety)
        self.addControl(self.button_anime)
        self.buttons.append(self.button_anime)
        # posy += space
        # label = config.get_localized_string(70018)
        # self.button_infantil = xbmcgui.ControlButton(posx, posy, width, height, label, font=font,
        #                                              alignment=0x00000000, noFocusTexture='',
        #                                              focusTexture=media_path+selected, textColor=textcolor,
        #                                              shadowColor=shadow, textOffsetX=offsetx, textOffsetY=offsety)
        # self.addControl(self.button_infantil)
        # self.buttons.append(self.button_infantil)
        posy += space
        label = config.get_localized_string(70019)
        self.button_docu = xbmcgui.ControlButton(posx, posy, width, height, label, font=font,
                                                     alignment=0x00000000, noFocusTexture='',
                                                     focusTexture=media_path + selected, textColor=textcolor,
                                                     shadowColor=shadow, textOffsetX=offsetx, textOffsetY=offsety)
        self.addControl(self.button_docu)
        self.buttons.append(self.button_docu)
        posy += space

        # label = config.get_localized_string(70013)
        # self.button_terror = xbmcgui.ControlButton(posx, posy, width, height, label, font=font,
        #                                            alignment=0x00000000, noFocusTexture='',
        #                                            focusTexture=media_path+selected, textColor=textcolor,
        #                                            shadowColor=shadow, textOffsetX=offsetx, textOffsetY=offsety)
        # self.addControl(self.button_terror)
        # self.buttons.append(self.button_terror)

        # if channelselector.auto_filter() == 'esp':
        #     posy += space
        #     label = config.get_localized_string(59981)
        #     self.button_lat = xbmcgui.ControlButton(posx, posy, width, height, label, font=font, alignment=0x00000000,
        #                                             noFocusTexture='', focusTexture=media_path+selected,
        #                                             textColor=textcolor, shadowColor=shadow, textOffsetX=offsetx,
        #                                             textOffsetY=offsety)
        #     self.addControl(self.button_lat)
        #     self.buttons.append(self.button_lat)
        #     posy += space
        #     label = config.get_localized_string(70014)
        #     self.button_cast = xbmcgui.ControlButton(posx, posy, width, height, label, font=font, alignment=0x00000000,
        #                                              noFocusTexture='', focusTexture=media_path + selected,
        #                                              textColor=textcolor, shadowColor=shadow, textOffsetX=offsetx,
        #                                              textOffsetY=offsety)
        #     self.addControl(self.button_cast)
        #     self.buttons.append(self.button_cast)
        # posy += space
        # label = config.get_localized_string(70015)
        # self.button_torrent = xbmcgui.ControlButton(posx, posy, width, height, label, font=font,
        #                                             alignment=0x00000000, noFocusTexture='',
        #                                             focusTexture=media_path+selected, textColor=textcolor,
        #                                             shadowColor=shadow, textOffsetX=offsetx, textOffsetY=offsety)
        # self.addControl(self.button_torrent)
        # self.buttons.append(self.button_torrent)

        start_page_item = get_start_page()
        if config.get_setting('start_page') and start_page_item.channel == 'news':
            posy += space
            label = config.get_localized_string(70016)
            self.button_config = xbmcgui.ControlButton(posx, posy, width, height, label, font=font,
                                                       alignment=0x00000000, noFocusTexture='',
                                                       focusTexture=media_path+selected, textColor=conditional_textcolor,
                                                       shadowColor=shadow, textOffsetX=offsetx, textOffsetY=offsety)
            self.addControl(self.button_config)
            self.buttons.append(self.button_config)

        posy += space*2
        label = config.get_localized_string(60423)
        self.button_buscar = xbmcgui.ControlButton(posx, posy, width, height, label, font=font, alignment=0x00000000,
                                                   noFocusTexture='', focusTexture=media_path + selected,
                                                   textColor=textcolor, shadowColor=shadow, textOffsetX=offsetx,
                                                   textOffsetY=offsety)
        self.addControl(self.button_buscar)
        self.buttons.append(self.button_buscar)
        posy += space
        label = config.get_localized_string(70036)
        self.button_actor = xbmcgui.ControlButton(posx, posy, width, height, label, font=font, alignment=0x00000000,
                                                   noFocusTexture='', focusTexture=media_path + selected,
                                                   textColor=textcolor, shadowColor=shadow, textOffsetX=offsetx,
                                                   textOffsetY=offsety)
        self.addControl(self.button_actor)
        self.buttons.append(self.button_actor)

        posy += space
        label = config.get_localized_string(70010)
        self.button_config_search = xbmcgui.ControlButton(posx, posy, width, height, label, font=font,
                                                       alignment=0x00000000,
                                                   noFocusTexture='', focusTexture=media_path + selected,
                                                   textColor=conditional_textcolor, shadowColor=shadow,
                                                   textOffsetX=offsetx, textOffsetY=offsety)
        self.addControl(self.button_config_search)
        self.buttons.append(self.button_config_search)


        label=''
        self.button_close = xbmcgui.ControlButton(260, 0, 1020, 725, label, noFocusTexture='', focusTexture='')
        self.addControl(self.button_close)



    def onClick(self, control):
        new_item=''

        control = self.getControl(control).getLabel()

        if control == config.get_localized_string(70663):
            new_item = get_start_page()
        elif control == config.get_localized_string(70009):
            new_item = Item(channel='', action='getmainlist', title='Menú Alfa')
        elif control == config.get_localized_string(30100):
            new_item = Item(channel='setting', action="settings")
        elif control == config.get_localized_string(30122):
            new_item = Item(channel='news', action="novedades", extra="peliculas", mode='silent')
        elif control == config.get_localized_string(70017):
            new_item = Item(channel='news', action="novedades", extra="series", mode='silent')
        elif control == config.get_localized_string(30124):
            new_item = Item(channel='news', action="novedades", extra="anime", mode='silent')
        elif control == config.get_localized_string(70018):
            new_item = Item(channel='news', action="novedades", extra="infantiles", mode='silent')
        elif control == config.get_localized_string(70019):
            new_item = Item(channel='news', action="novedades", extra="documentales", mode='silent')
        elif control == config.get_localized_string(70013):
            new_item = Item(channel='news', action="novedades", extra="terror", mode='silent')
        elif control == config.get_localized_string(59981):
            new_item = Item(channel='news', action="novedades", extra="castellano", mode='silent')
        elif control == config.get_localized_string(70014):
            new_item = Item(channel='news', action="novedades", extra="latino", mode='silent')
        elif control == config.get_localized_string(70015):
            new_item = Item(channel='news', action="novedades", extra="torrent", mode='silent')
        elif control == config.get_localized_string(70016):
            menu_node = jsontools.get_node_from_file('menu_settings_data.json', 'menu')
            if 'categoria actual' in menu_node:
                category = menu_node['categoria actual']
            new_item = Item(channel='news', action="setting_channel", extra=category, menu=True)
        elif control == config.get_localized_string(60423):
            new_item = Item(channel='search', action="search")
        elif control == config.get_localized_string(70036):
            new_item = Item(channel='tvmoviedb', title="Buscar actor/actriz", action="search_",
                            search={'url': 'search/person', 'language': def_lang, 'page': 1}, star=True)
        elif control == config.get_localized_string(70010):
            new_item = Item(channel='search', action="setting_channel")
        elif control == '':
            self.close()
        if new_item !='':
            self.run_action(new_item)


    def onAction(self, action):


        if action == ACTION_PREVIOUS_MENU or action == ACTION_GESTURE_SWIPE_LEFT or action == 110 or action == 92:
            self.close()

        if action == ACTION_MOVE_RIGHT or action == ACTION_MOVE_DOWN:
            self.focus += 1
            if self.focus > len(self.buttons)-1:
                self.focus = 0
            while True:
                id_focus = str(self.buttons[self.focus].getId())

                if xbmc.getCondVisibility('[Control.IsVisible(' + id_focus + ')]'):
                    self.setFocus(self.buttons[self.focus])
                    break
                self.focus += 1

        if action == ACTION_MOVE_LEFT or action == ACTION_MOVE_UP:
            self.focus -= 1
            if self.focus < 0:
                self.focus = len(self.buttons) - 1
            while True:
                id_focus = str(self.buttons[self.focus].getId())
                if xbmc.getCondVisibility('[Control.IsVisible(' + id_focus + ')]'):
                    self.setFocus(self.buttons[self.focus])
                    break
                self.focus -= 1

    def run_action(self, item):
        logger.debug()
        if item.menu != True:
            self.close()
        xbmc.executebuiltin("Container.update(%s)"%launcher.run(item))



