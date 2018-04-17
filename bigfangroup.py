# -*- coding: utf-8 -*-
import urllib
import re
import sys
import xbmcaddon
import os
import socket
import SearcherABC
#Понеслась!
class bigfangroup(SearcherABC.SearcherABC):

    __torrenter_settings__ = xbmcaddon.Addon(id='plugin.video.torrenter')
    #__torrenter_language__ = __settings__.getLocalizedString
    #__torrenter_root__ = __torrenter_settings__.getAddonInfo('path')

    ROOT_PATH=os.path.dirname(__file__)
    addon_id=ROOT_PATH.replace('\\','/').rstrip('/').split('/')[-1]
    __settings__ = xbmcaddon.Addon(id=addon_id)
    __addonpath__ = __settings__.getAddonInfo('path')
    __version__ = __settings__.getAddonInfo('version')
    __plugin__ = __settings__.getAddonInfo('name') + " v." + __version__

    username = __settings__.getSetting("username")
    password = __settings__.getSetting("password")
    baseurl = 'www.bigfangroup.org' # TODO: change this!

    '''
    Setting the timeout
    '''
    torrenter_timeout_multi=int(sys.modules["__main__"].__settings__.getSetting("timeout"))
    timeout_multi=int(__settings__.getSetting("timeout"))

    '''
    Weight of source with this searcher provided. Will be multiplied on default weight.
    '''
    sourceWeight = 1

    '''
    Full path to image will shown as source image at result listing
    '''
    searchIcon = os.path.join(__addonpath__,'icon.png')

    '''
    Flag indicates is this source - magnet links source or not.
    '''
    @property
    def isMagnetLinkSource(self):
        return False

    def __init__(self):
        if self.__settings__.getSetting("usemirror")=='true':
            self.baseurl = self.__settings__.getSetting("baseurl")
            self.log('baseurl: '+str(self.baseurl))

        self.logout()

        if self.timeout_multi==0:
            socket.setdefaulttimeout(10+(10*self.torrenter_timeout_multi))
        else:
            socket.setdefaulttimeout(10+(10*(self.timeout_multi-1)))

        self.debug=self.log

    def logout(self): ####не робив
        old_username = self.__settings__.getSetting("old_username")
        if old_username in [None,''] or old_username!=self.username:
            self.__settings__.setSetting("old_username", self.username)
            self.clear_cookie(self.baseurl)
            self.login() #####

    def search(self, keyword):
        filesList = []
        url = "http://%s/browse.php?search=%s" % (self.baseurl, urllib.quote_plus(keyword.decode('utf-8').encode('cp1251')))
        response = self.makeRequest(url).decode('cp1251').encode('utf-8')
        if None != response and 0 < len(response):
            self.debug(response)
            regex = '''<tr style="font-size: 8pt; ">.+?</tr>'''
            regex_tr='''<td align="left" class="indented" style="border-right: 0px; font-size: 8pt; "><a href=".+?"><b>(.+?)</b></a>.+?<a href="(.+?)".+?<td align="center" style="white-space: nowrap; font-size: 8pt; ">(.+?)</td>.+?">(\d+)<.+?">(\d+)'''

            for tr in re.compile(regex, re.DOTALL).findall(response):
                result=re.compile(regex_tr, re.DOTALL).findall(tr)
                self.debug(tr+' -> '+str(result))
                if result:
                    (title, link, size, seeds,leechers)=result[0]
                    size,seeds,leechers=size,seeds,leechers
                    filesList.append((
                        int(int(self.sourceWeight) * int(seeds)),
                        int(seeds), int(leechers), size,
                        self.unescape(self.stripHtml(title)),
                        self.__class__.__name__ + '::''http://www.bigfangroup.org/'+ link,
                        self.searchIcon,
                    ))
        return filesList

    def check_login(self, response=None):
        if None != response and 0 < len(response):
            if re.compile('value="Вход!"').search(response):
                self.showMessage('bigfangroup', 'Внесите настройки плагина!!!')
                xbmc.sleep(2000)
                self.log('bigfangroup Not logged!')
                self.login()
                return False
        return True

    def getTorrentFile(self, url):
        self.timeout(5)
        content = self.makeRequest(url)
        self.debug('getTorrentFile: '+content)
        if not self.check_login(content):
            content = self.makeRequest(url)

        else:
            return self.saveTorrentFile(url, content)

    def login(self):
        data = {
            'username': self.username,
            'password': self.password,
            'login': 'Вход!'
        }
        self.makeRequest(
            'http://%s/takelogin.php' % self.baseurl,
            data
        )
        self.cookieJar.save(ignore_discard=True)
        for cookie in self.cookieJar:
            uid, passed = None, None
            if cookie.name == 'uid':
                uid = cookie.value
            if cookie.name == 'pass':
                passed = cookie.value
            if uid and passed:
                return 'uid=' + uid + '; pass=' + passed
        return False

