#coding=utf8
import urllib
import urllib2
import urlparse
import cookielib
import re
try:
    import json 
except ImportError:
    import simplejson as json

class UTorrentClient(object):

    def __init__(self, base_url, username, password):
        self.base_url = base_url
        self.username = username
        self.password = password
        self.opener = self.make_opener('uTorrent', base_url, username, password)
        self.token = self.get_token()
        #TODO refresh token, when necessary

    def make_opener(self, realm, base_url, username, password):
        '''uTorrent API need HTTP Basic Auth and cookie support for token verify.'''

        auth_handler = urllib2.HTTPBasicAuthHandler()
        auth_handler.add_password(realm=realm,
                                  uri=base_url,
                                  user=username,
                                  passwd=password)
        opener = urllib2.build_opener(auth_handler)
        urllib2.install_opener(opener)     

        cookie_jar = cookielib.CookieJar()
        cookie_handler = urllib2.HTTPCookieProcessor(cookie_jar)

        handlers = [auth_handler, cookie_handler]
        opener = urllib2.build_opener(*handlers)
        return opener

    def get_token(self):
        url = urlparse.urljoin(self.base_url, 'token.html')
        response = self.opener.open(url)
        token_re = "<div id='token' style='display:none;'>([^<>]+)</div>"
        match = re.search(token_re, response.read())
        return match.group(1)

    def action_getfiles(self, hash, **kwargs):
        args = {'action' : 'getfiles', 'hash' : hash}
        args.update(kwargs)
        return self.action(**args)
        
    def action_list(self, **kwargs):
        args = {'list' : '1'}
        args.update(kwargs)
        return self.action(**args)

    def action(self, **kwargs):
        #about token, see https://github.com/bittorrent/webui/wiki/TokenSystem
        url = self.base_url + '?token=' + self.token + '&' + urllib.urlencode(kwargs)
        response = self.opener.open(url)
        return response.code, json.loads(response.read())
        
