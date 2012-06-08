#!/usr/bin/env python
# License - see UNLICENSE.md

"""
Simple python API to Singly
"""

import urllib
import urllib2
import urlparse

try:
    import simplejson as json
except ImportError:
    import json

class Singly(object):
    """Singly API"""

    API_ENDPOINT = 'https://api.singly.com/'

    SINGLY_AUTHORIZE_URL    = API_ENDPOINT + 'oauth/authorize'
    SINGLY_ACCESS_TOKEN_URL = API_ENDPOINT + 'oauth/access_token'

    DEFAULT_REDIRECT_URI = 'http://localhost:9999'

    # Generic
    #    API_ENDPOINT + 'profiles'
    # 
    # Service specific
    # Twitter:
    #    API_ENDPOINT + 'services/twitter'

    def __init__(self, app_key, app_secret, redirect_uri = None):
        """Singly API - pass in application key and secret"""

        self.app_key = app_key
        self.app_secret = app_secret

        if redirect_uri is None:
            redirect_uri = self.DEFAULT_REDIRECT_URI
        self.redirect_uri = redirect_uri

        self.access_token = None
        self._debug = False

    def debug(self, debug):
        """Set debug flag"""
        self._debug = debug

    def _log(self, msg):
        """Log a debug message"""
        if self._debug:
            print msg

    def auth(self, service, callback, redirect_uri = None):
        """
        Authenticate a service against Singly

        service  - service to authenticate against e.g. 'twitter'
        callback - authorize callback function taking url parameter and returning response (HTTP status, HTTP url) tuple e.g. (301, 'http://example.org/')
        redirect_uri - optional redirect uri
        """

        if redirect_uri is None:
            redirect_uri = self.redirect_uri

        # Format of authorize URL:
        # https://api.singly.com/oauth/authorize?client_id=CLIENT-ID&
        #   redirect_uri=REDIRECT-URI&service=SERVICE
        authorize_params = {
            'client_id'    : self.app_key,
            'redirect_uri' : redirect_uri,
            'service'      : service
            }
        query_params = urllib.urlencode(authorize_params)
        authorize_uri = self.SINGLY_AUTHORIZE_URL + '?' + query_params

        self._log("Calling authorize callback (%s)" % (authorize_uri, ))
        (status1, oauth_code_uri) = callback(authorize_uri)
        self._log("authorize callback response is (HTTP %s, URL %s)" % 
                 (status1, oauth_code_uri))

        urlobj1 = urlparse.urlparse(oauth_code_uri)
        urlquery1 = urlparse.parse_qs(urlobj1.query)
        code = urlquery1['code'][0]

        self._log("OAuth code is %s" % (code, ))

        # Now get the access token

        # Need to POST to this URL
        oauth_get_access_token_uri = self.SINGLY_ACCESS_TOKEN_URL
        # with these parameters
        post_params = {
            'client_id' : self.app_key,
            'app_secret' : self.app_secret,
            'code' : code
        }
        post_data = urllib.urlencode(post_params)

        self._log("Calling %s with params %s" % 
                  (oauth_get_access_token_uri, post_data))
        request2 = urllib2.Request(oauth_get_access_token_uri, post_data)
        response2 = urllib2.urlopen(request2)

        access_token_data = response2.read()
        self._log("Access token response data is %s" % (access_token_data, ))

        # Expect
        # {
        # "access_token": "S0meAcc3ssT0k3n"
        # }
        access_token_json = json.loads(access_token_data)

        access_token = access_token_json['access_token']
        self._log("Access token is %s" % (access_token, ))
        self.access_token = access_token

        return access_token

    def __endpoint(self, endpoint):
        """Internal: call a Singly API endpoint"""
        url = self.API_ENDPOINT + endpoint + '?access_token=' + self.access_token
        response = urllib2.urlopen(url)
        data = response.read()
        self._log("Endpoint %s returned data %s" % (endpoint, data))
        jsondata = json.loads(data)
        self._log("Endpoint %s returned json %s" % (endpoint, jsondata))

        return jsondata

    def profiles(self):
        """Get profiles"""
        return self.__endpoint('profiles')

    def twitter_discovery(self):
        """Get twitter discovery"""
        return self.__endpoint('services/twitter')


def main():
    """Test main"""

    # This is where the private stuff is stored
    import secrets

    def my_authorize_callback(authentication_url):
        """
        Takes the authorization URI to show to a user and returns the
        HTTP response HTTP status and final URI
        """
        return ('301', secrets.MY_CODE_URI)


    singly = Singly(secrets.CLIENT_KEY, secrets.CLIENT_SECRET)

    singly.debug(True)

    if secrets.OFFLINE:
        singly.access_token = secrets.MY_ACCESS_TOKEN
    else:
        access_token = singly.auth('twitter', my_authorize_callback)
        print "Result access token is %s - add to secrets.py" % (access_token, )

    val = singly.profiles()
    print "My Singly profiles are %s" % (str(val), )

    val = singly.twitter_discovery()
    print "My Singly twitter discovery is %s" % (str(val), )


if __name__ == "__main__":
    main()
