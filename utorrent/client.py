#coding=utf8
import urllib
import urllib2
import urlparse
import cookielib
import re
import StringIO
try:
    import json 
except ImportError:
    import simplejson as json

from upload import MultiPartForm

class UTorrentClient(object):

    def __init__(self, base_url, username, password):
        self.base_url = base_url
        self.username = username
        self.password = password
        self.opener = self._make_opener('uTorrent', base_url, username, password)
        self.token = self._get_token()
        #TODO refresh token, when necessary

    def _make_opener(self, realm, base_url, username, password):
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

    def _get_token(self):
        url = urlparse.urljoin(self.base_url, 'token.html')
        response = self.opener.open(url)
        token_re = "<div id='token' style='display:none;'>([^<>]+)</div>"
        match = re.search(token_re, response.read())
        return match.group(1)

       
    def list(self, **kwargs):
        params = [('list', '1')]
        params += kwargs.items()
        return self._action(params)

    def getfiles(self, hash):
        params = [('action', 'getfiles'), ('hash', hash)]
        return self._action(params)
 
    def getprops(self, hash):
        params = [('action', 'getprops'), ('hash', hash)]
        return self._action(params)
        
    def setprio(self, hash, priority, files):
        params = [('action', 'setprio'), ('hash', hash), ('p', str(priority))]
        if type(files) in (list, tuple):
            for file_index in files:
                params.append(('f', str(file_index)))
        else:
            params.append(('f', str(files)))

        return self._action(params)
        
    def addfile(self, filename, filepath=None, bytes=None):
        params = [('action', 'add-file')]

        form = MultiPartForm()
        if filepath is not None:
            file_handler = open(filepath)
        else:
            file_handler = StringIO(bytes)
            
        form.add_file('torrent_file', filename, file_handler)

        return self._action(params, str(form), form.get_content_type())

    def _action(self, params, body=None, content_type=None):
        #about token, see https://github.com/bittorrent/webui/wiki/TokenSystem
        url = self.base_url + '?token=' + self.token + '&' + urllib.urlencode(params)
        request = urllib2.Request(url)

        if body:
            request.add_data(body)
            request.add_header('Content-length', len(body))
        if content_type:
            request.add_header('Content-type', content_type)

        try:
            response = self.opener.open(request)
            return response.code, json.loads(response.read())
        except urllib2.HTTPError,e:
            raise
        
