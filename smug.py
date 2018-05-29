# -*- coding: utf-8 -*-
#
'''
SmugMug RSS Class
'''
#
# Standard Imports
#
from __future__ import print_function
from datetime import date, datetime
import json
import logging
from urllib.parse import urlparse
#
# Non-standard imports
#
import feedparser
#
##############################################################################
#
# SmugRss
#
class SmugRss(object):
    """SmugRss Feed Class"""
    #
    ####################################################################################
    #
    # Class variables
    #
    NICK_URL = 'https://{url}/hack/feed.mg?Type=nickname&Data={nick}&format=rss200'
    # 159365802_Wp7NDr
    GALLERY_URL = 'https://{url}/hack/feed.mg?Type=gallery&Data={gallery}&format=rss200'
    #
    ####################################################################################
    #
    # __init__()
    #
    def __init__(self, debug=False, site_url=None, nickname=None):
        super(SmugRss, self).__init__()

        self._logger = logging.getLogger(type(self).__name__)

        self._debug = debug
        if debug:
            self._logger.info("Debugging enabled")

        if None in [site_url, nickname]:
            raise RuntimeError("Need site_url and nickname to proceed!")

        self._entries = None
        self._nickname = nickname
        self._recent = None
        self._recent_feed_url = self.NICK_URL.format(url=site_url, nick=nickname)
        self._site_url = site_url

    #
    ####################################################################################
    #
    # get_recent()
    #
    def get_gallery_feed(self, gallery=None, category=None, year=None):
        '''
        get_gallery_feed(category, year) - Load the feed of recent items

            category - Limit items to provided category (first port of URL path)
            year - Limit items to provided year of modification
        '''
        results = None

        if None not in [gallery]:
            gallery_url = self.GALLERY_URL.format(url=self.site_url, gallery=gallery)
            results = feedparser.parse(gallery_url).get('entries')

            if None not in [year]:
                filtered = []

                for entry in results:
                    if str(entry.get('published_parsed')[0]) == str(year):
                        filtered.append(entry)

                results = filtered

            if None not in [category]:
                filtered = []
                for entry in results:
                    link_info = urlparse(entry.get('link'))
                    # ['', 'Travel', '2018', 'Belgium']
                    paths = link_info.path.split('/')

                    if paths[1] == category:
                        filtered.append(entry)
                results = filtered
        return results
    #
    ####################################################################################
    #
    # get_recent()
    #
    def get_recent(self, category=None, year=None):
        '''
        get_recent(category, year) - Load the feed of recent items

            category - Limit items to provided category (first port of URL path)
            year - Limit items to provided year of modification
        '''
        self._recent = feedparser.parse(self._recent_feed_url).get('entries')

        if None not in [year]:
            filtered = []

            for entry in self._recent:
                if str(entry.get('published_parsed')[0]) == str(year):
                    filtered.append(entry)

            self._recent = filtered

        if None not in [category]:
            filtered = []
            for entry in self._recent:
                link_info = urlparse(entry.get('link'))
                # ['', 'Travel', '2018', 'Belgium']
                paths = link_info.path.split('/')

                if paths[1] == category:
                    filtered.append(entry)
            self._recent = filtered

    #
    ##############################################################################
    #
    # _json_dump() - Little output to DRY
    #
    def _json_dump(self, the_thing, pretty=False):
        '''_json_dump() - Little output to DRY'''
        output = None
        if pretty:
            output = json.dumps(the_thing, sort_keys=True, indent=4,
                                separators=(',', ': '))
        else:
            output = json.dumps(the_thing, default=self._json_serial)
        return output

    @staticmethod
    def _json_serial(obj):
        '''JSON serializer for objects not serializable by default json code'''

        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        # else:
        #     return obj.__dict__
        raise TypeError("Type %s not serializable" % type(obj))
    #
    ##############################################################################
    ##############################################################################
    #
    @property
    def entries(self):
        '''entries - current RSS feed entries'''
        return self._entries

    @property
    def site_url(self):
        '''site_url - URL of the loaded feed'''
        return self._site_url
