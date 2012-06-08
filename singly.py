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


class Service(dict):
    """Singly Service"""

    def __init__(self, name, d):
        """Construct a Service description from service name response data"""

        self.__dict = d
        for k, v in d.iteritems():
            setattr(self, k, v)
        self.name = name

    def __str__(self):
        return "<Service %s>" % (self.name, )

    def __iter__(self):
        return iter(self.__dict)

    def __repr__(self):
        return repr(self.__dict)


class Singly(object):
    """Singly API"""

    API_ROOT = 'https://api.singly.com/'

    API_ENDPOINT = API_ROOT + 'v0/'

    SINGLY_AUTHORIZE_URL    = API_ROOT + 'oauth/authorize'
    SINGLY_ACCESS_TOKEN_URL = API_ROOT + 'oauth/access_token'

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

        # Filled by _get_services()
        self._services = None
        self._service_names = []

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
        self._log("Endpoint %s returned json %s" % (endpoint, json.dumps(jsondata, indent=2)))

        return jsondata

    def _get_services(self):
        """Internal: get services and their names"""
        if self._services is not None:
            return
        services = self.__endpoint('services')
        if services is not None:
            self._services = dict([(name, Service(name, data))
                                    for (name, data) in services.iteritems()])
            self._service_names = services.keys()
            self._service_names.sort()

    # https://dev.singly.com/services_overview
    def services(self):
        """Get services"""
        self._get_services()
        return self._services

    def service(self, name):
        """Get description of service with name"""
        self._get_services()
        if name in self._services:
            return self._services[name]
        return None

    def service_names(self):
        """Get services"""
        self._get_services()
        return self._service_names


    # user specific
    def profiles(self):
        """Get profiles"""
        return self.__endpoint('profiles')


    # twitter service
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

    val = singly.service_names()
    print "Singly service names are %s" % (str(val), )

    val = singly.services()
    print "Singly services are %s" % (str(val), )

    svc = singly.service('twitter')
    print "Singly service name '%s' description: '%s'" % (svc.name, svc.desc)

    val = singly.profiles()
    print "My Singly profiles are %s" % (json.dumps(val, indent=2), )

    val = singly.twitter_discovery()
    print "My Singly twitter discovery is %s" % (json.dumps(val, indent=2), )


if __name__ == "__main__":
    main()
