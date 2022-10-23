#!/bin/bash
rm tests/home/userdata/addon_data/plugin.video.kod/settings_channels/*.json
rm tests/home/userdata/addon_data/plugin.video.kod/settings_servers/*.json
rm tests/home/userdata/addon_data/plugin.video.kod/cookies.dat
rm tests/home/userdata/addon_data/plugin.video.kod/kod_db.sqlite
python3.9 -m pip install --upgrade pip
pip3.9 install -U sakee
pip3.9 install -U html-testRunner
pip3.9 install -U parameterized
export PYTHONPATH=$PWD
export KODI_INTERACTIVE=0
export KODI_HOME=$PWD/tests/home
if (( $# >= 1 ))
then
  export KOD_TST_CH=$1
fi
python3.9 tests/test_generic.py