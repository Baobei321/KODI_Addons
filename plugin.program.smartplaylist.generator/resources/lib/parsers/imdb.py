#   Copyright (C) 2024 Lunatixz
#
#
# This file is part of Smartplaylist Generator.
#
# Smartplaylist Generator is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Smartplaylist Generator is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with PseudoTV Live.  If not, see <http://www.gnu.org/licenses/>.
#
# -*- coding: utf-8 -*-
import requests

from globals  import *
from bs4      import BeautifulSoup
from operator import itemgetter

class IMDB:
    def __init__(self, cache=None):
        if cache is None: self.cache = SimpleCache()
        else:
            self.cache = cache
            self.cache.enable_mem_cache = False
        
        self.enabled = REAL_SETTINGS.getSetting('Enable_Trakt') == 'true'
        self.name    = LANGUAGE(32100)
        self.logo    = os.path.join(ADDON_PATH,'resources','images','imdb.png')
        
        
    def log(self, msg, level=xbmc.LOGDEBUG):
        return log('%s: %s'%(self.__class__.__name__,msg),level)
        
        
    def convert_type(self, list_type):
        return {'movie':'movies','show':'tvshows','episode':'episodes'}[list_type]


    def clean_string(self, string):
        return string.replace('copy','').replace('\r\n\t','')
        
        
    # @cacheit(expiration=datetime.timedelta(minutes=15))
    def get_lists(self):
        imdb_user = REAL_SETTINGS.getSetting('IMDB_ClientID')
        tmp = []
        self.log('get_lists, imdb_user = %s'%(imdb_user))
        url = f"https://www.imdb.com/user/{imdb_user}/lists"
        headers = { "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
                    "Accept-Language": "en-US,en;q=0.9"}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")
        script_tag = soup.find("script", id="__NEXT_DATA__")
        if script_tag:
            data = json.loads(script_tag.string)
            lists_data = data.get('props', {}).get('pageProps', {}).get('lists', [])
            for l in lists_data:
                try:
                    list_id   = l.get('id')
                    list_name = l.get('title') or l.get('name')
                    if list_id and list_name:
                        tmp.append({"name": list_name, "id": list_id, "url": f"https://imdb.com{list_id}/"})
                except Exception as e: self.log(f"get_list_items, failed! Error fetching user profile: {e}")
        if not tmp:
            for link in soup.find_all("a", href=True):
                try:
                    href = link['href']
                    if "/list/ls" in href:
                        list_id = href.split('/')[2]
                        name = link.get_text(strip=True)
                        if list_id.startswith('ls') and name and not any(x['id'] == list_id for x in tmp):
                            tmp.append({"name": name, "id": list_id, "url": f"https://imdb.com{list_id}/"})
                except Exception as e: self.log(f"get_list_items, failed! Error fetching user profile: {e}")
        return sorted(tmp, key=itemgetter('name')) if tmp else None


    # @cacheit(expiration=datetime.timedelta(hours=int(REAL_SETTINGS.getSetting('Run_Every_Hours')), minutes=15))
    def get_list_items(self, list_id):
        self.log('get_list_items, list_id = %s'%(list_id))
        tmp = {}
        url = f"https://www.imdb.com/list/{list_id}/"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                   "Accept-Language": "en-US,en;q=0.5"}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")
        movie_elements = soup.find_all("h3", class_="ipc-title__text")
        for el in movie_elements:
            try:
                if el.string and not el.string.startswith(('Explore', 'More', 'Recently')):
                    parent_link = el.find_parent("a")
                    if parent_link and '/title/tt' in parent_link['href']:
                        imdb_id = parent_link['href'].split('/')[2]
                        title = el.string.split('. ', 1)[-1] if '. ' in el.string else el.string
                        tmp.append({"title": title, "uniqueid": {'imdb':imdb_id}})
            except Exception as e: self.log(f"get_list_items, failed! Error fetching user profile: {e}")
        return tmp