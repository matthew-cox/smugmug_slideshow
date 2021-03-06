# -*- coding: utf-8 -*-
#
'''
SmugMug Classes
'''
#
# Standard Imports
#
from __future__ import print_function
from datetime import date, datetime
import json
import logging
import os
import random
import re
import sys
from urllib.parse import urlparse
#
# Non-standard imports
#
# import exifread
import feedparser
import requests
#
##############################################################################
#
# SmugBase
#
# pylint: disable=too-few-public-methods
class SmugBase(object):
    '''SmugBase - base class for inheritance and DRY'''
    #
    ####################################################################################
    #
    # __init__()
    #
    def __init__(self, debug=False):
        super(SmugBase, self).__init__()

        self._logger = logging.getLogger(type(self).__name__)

        self._debug = debug
        if debug:
            self._logger.info("Debugging enabled")
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
#
# SmugRss
#
class SmugRss(SmugBase):
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
        super(SmugRss, self).__init__(debug=False)

        if None in [site_url, nickname]:
            raise RuntimeError("Need site_url and nickname to proceed!")

        self._gallery_url = None
        self._entries = None
        self._nickname = nickname
        self._recent = None
        self._recent_feed_url = self.NICK_URL.format(url=site_url, nick=nickname)
        self._site_url = site_url

    #
    ####################################################################################
    #
    # get_gallery_feed()
    #
    def get_gallery_feed(self, gallery=None, category=None, year=None):
        '''
        Load the feed of recent items

        Args:
            category (str): Limit items to provided category (first portion of URL path)
            gallery (str): SmugMug gallery id
            year (str): Limit items to provided year of modification

        Returns:
            list: List of matching galleries from the feed

        Raises:
            RuntimeError: if missing arguments needed to execute requests
        '''
        results = None

        if [gallery, self._gallery_url].count(None) == 2:
            raise RuntimeError("Need either gallery id OR gallery URL")

        if None not in [gallery]:
            gallery_url = self.GALLERY_URL.format(url=self.site_url, gallery=gallery)
        else:
            gallery_url = self._gallery_url

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
        Load the feed of recent items

        Args:
            category (str): Limit items to provided category (first portion of URL path)
            gallery (str): SmugMug gallery id
            year (str): Limit items to provided year of modification
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
                #      Cetegory   Year    Gallery
                # ['', 'Travel', '2018', 'Belgium']
                paths = link_info.path.split('/')

                if paths[1] == category:
                    filtered.append(entry)
            self._recent = filtered
    #
    ##############################################################################
    ##############################################################################
    #
    @property
    def entries(self):
        '''list: current RSS feed entries'''
        return self._entries

    @property
    def site_url(self):
        '''str: URL of the loaded feed'''
        return self._site_url
#
##############################################################################
#
# SmugRssUrl
#
class SmugRssGalleryUrl(SmugRss):
    """SmugRssUrl Feed Class"""
    #
    ####################################################################################
    #
    # Class variables
    #

    #
    ####################################################################################
    #
    # __init__()
    #
    def __init__(self, debug=False, gallery_url=None):
        if None in [gallery_url]:
            raise RuntimeError("Need gallery_url to proceed!")

        parsed = urlparse(gallery_url)
        site_url = '://'.join([parsed.scheme, parsed.netloc])
        # this is bad form, but need the site_url for the super constructor
        super(SmugRssGalleryUrl, self).__init__(debug=False, site_url=site_url, nickname="FOO")

        # extract the RSS URL from the page content
        self._gallery_url = ''.join([site_url, self._find_rss_feed_url(gallery_url)])
    #
    ####################################################################################
    #
    # _find_rss_feed_url()
    #
    def _find_rss_feed_url(self, gallery_url=None):
        '''
        Search the provided gallery page content for an RSS url

        Args:
            gallery_url (str): Gallery URL to search

        Returns:
            str: URL for RSS feed or None
        '''
        result = None

        if None not in [gallery_url]:
            response = requests.get(gallery_url)

            self._logger.info("Response code was '%s'", response.status_code)

            for line in response.text.split("\n"):

                if '<link rel="alternate" type="application/rss+xml"' in line:
                    match = re.search(r'href="([^"]*)"', line, re.I)
                    if match:
                        result = match.group(1)
                        break
        return result
    #
    ####################################################################################
    #
    # _find_rss_feed_url()
    #
    def get_recent(self, category=None, year=None):
        raise NotImplementedError("Does not apply to a gallery!")
#
####################################################################################
#
# pylint: disable=too-many-instance-attributes
class Slideshow(SmugBase):
    '''
    SlideShow - gather up the slideshow stuff
    '''
    #
    ####################################################################################
    #
    # Class variables
    #
    # Maximum size of images to cache (in bytes)
    MAX_CACHE_SIZE = 128 * 1024 * 1024
    #
    ##############################################################################
    #
    # __init__()
    #
    # pylint: disable=too-many-arguments
    def __init__(self, debug=False, downscale=False, gallery_id=None, gallery_url=None, height=None,
                 width=None):
        '''
        Args:
            debug (bool): Enable debug mode
            downscale (bool): Find images larger than display and downscale them
            gallery_id (str): SmugMug gallery id
            gallery_url (str): SmugMug gallery URL
            height (int): Height of target display
            width (int): Width of target display
        '''
        super(Slideshow, self).__init__(debug=debug)

        self._cache = {}
        self._cache_size = 0

        self._downscale = downscale

        self._height = height
        self.__width = width

        self._loop_pos = 0

        # load the gallery RSS - do this last
        self._gallery = None
        self._gallery_id = gallery_id
        self._gallery_url = gallery_url
        self._logger.info("Setting URL to '%s'", gallery_url)
        self.load_gallery()
    #
    ##############################################################################
    #
    # _cache_get()
    #
    def _cache_get(self, key=None, url=None):

        result = None
        if None not in [key, url]:

            # do we already have the data?
            if None in [self._cache.get(key)]:
                result = self.load_image(image_url=url)
                # cache the image for re-use
                self._cache_size += sys.getsizeof(result)
                self._cache[key] = result
            else:
                result = self._cache[key]
        return result
    #
    ##############################################################################
    #
    # _cache_size_check()
    #
    def _cache_size_check(self):

        # is the cache too large?
        self._logger.debug("Cache is %fMb", (self._cache_size / 1024 / 1024))
        while self._cache_size >= self.MAX_CACHE_SIZE:
            key = random.choice(list(self._cache.keys()))
            self._logger.warning("Clearing '%s' from cache!", key)
            # pylint: disable=bare-except
            try:
                self._cache_size -= sys.getsizeof(self._cache[key])
                del self._cache[key]
            except:
                pass
            self._logger.warning("Cache is %fMb", (self._cache_size / 1024 /1024))

    #
    ##############################################################################
    #
    ##############################################################################
    #
    # find_best_image_size()
    #
    def find_best_image_size(self):
        '''
        Choose the best size image for the set W x H

        Returns:
            str: URL to image
        '''
        img = None
        media_content = self._gallery[self._loop_pos].get('media_content')
        if self._downscale:
            # search from large to small
            media_content = list(reversed(media_content))

        self._logger.info("Searching for an image...")
        if None not in [media_content]:
            # which dimension do we care about more?
            horizontal = False
            closest = 10000000

            for image in media_content:
                self._logger.debug(self._json_dump(image, True))
                horizontal = int(image.get('width')) >= int(image.get('height'))

                if horizontal:
                    diff = self.__width - int(image.get('width'))
                else:
                    diff = self._height - int(image.get('height'))

                # NOTE: a positive diff indicates an image smaller than the display, end search if
                # in downscale mode
                if self._downscale and diff > 0:
                    self._logger.info("Image is smaller than display. Skipping...")
                    break

                diff = abs(diff)

                if diff < closest:
                    closest = diff
                    self._logger.debug("Found a new match: %s", self._json_dump(image, True))
                    img = image

                if closest == 0:
                    self._logger.debug("Found a perfect match: %s", self._json_dump(image, True))
                    break

        if None in [img]:
            self._logger.error("No image size match found in: %s",
                               self._json_dump(media_content, True))

        return img
    #
    ##############################################################################
    #
    # load_gallery()
    #
    def load_gallery(self, gallery_id=None, gallery_url=None, shuffle=True):
        '''
        Load the feed for the provided Gallery id

        Args:
            gallery_id (str): SmugMug gallery id to load
            gallery_url (str): SmugMug gallery URL to load
            shuffle (bool): Shuffle the gallery entries. Default: True
        '''
        self._gallery = None

        gallery_id = gallery_id if gallery_id else self._gallery_id
        gallery_url = gallery_url if gallery_url else self._gallery_url
        self._logger.info("Setting URL to '%s'", gallery_url)

        if None not in [gallery_id]:
            self._logger.info("Loading gallery with id '%s'", gallery_id)
            smugmug = SmugRss(site_url='www.azriel.photo', nickname='azriel')
            self._gallery = smugmug.get_gallery_feed(gallery=gallery_id)

        if None not in [gallery_url]:
            self._logger.info("Loading gallery with URL '%s'", gallery_url)
            smugmug = SmugRssGalleryUrl(gallery_url=gallery_url)
            self._gallery = smugmug.get_gallery_feed()

        if self._gallery and shuffle:
            self._logger.info("Shuffling gallery...")
            self._gallery = random.sample(self._gallery, k=len(self._gallery))
    #
    ##############################################################################
    #
    # load_image()
    #
    def load_image(self, image_url=None):
        '''
        Load image data from the provided URL

        Args:
            image_url (str): Valid URL to an image file

        Returns:
            str: Binary string data for loaded content
        '''
        result = None
        if None not in [image_url]:
            self._logger.info("Loading image '%s'", image_url)
            # Download the image
            img_data = requests.get(image_url)

            result = img_data.content

        return result

    #
    ##############################################################################
    #
    # current()
    #
    def current(self):
        '''
        Return the data for the current image

        Returns:
            str: Binary string data for current image
        '''

        result = None

        img = self.find_best_image_size()

        if None not in [img]:

            file_name = os.path.basename(img.get('url'))
            self._logger.debug(self._json_dump(img, True))

            result = self._cache_get(file_name, img.get('url'))
            self._cache_size_check()

        return result
    #
    ##############################################################################
    #
    # next()
    #
    def next(self):
        '''
        Return the data for the next image

        Returns:
            str: Binary string data for next image
        '''
        self._loop_pos += 1

        # do we need to reset the loop?
        if self._loop_pos >= len(self._gallery):
            # re-load the gallery (on the off chance it has been updated while we were running)
            self.load_gallery()
            self._loop_pos = 0

        return self.current()
    #
    ##############################################################################
    #
    # previous()
    #
    def previous(self):
        '''
        Return the data for the previous image

        Returns:
            str: Binary string data for previous image
        '''
        self._loop_pos -= 1

        # have we looped around?
        if self._loop_pos <= 0:
            self._loop_pos = len(self._gallery)

        return self.current()
    # Return Exif tags
    # try:
    #     tags = exifread.process_file(BytesIO(img_data.content), details=False)
    # except (Exception) as err:
    #     raise err
    #
    # print(tags)

    # Display some image info
    # displayText = "Matt Test"
    # text = largefont.render(displayText, 1, (255, 255, 255))
    # main_surface.blit(text, (main_surface.get_rect().centerx,main_surface.get_rect().centery))
