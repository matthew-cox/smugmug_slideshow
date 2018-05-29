#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
'''
SlideShow - control the image slideshow
'''
#
# Standard Imports
#
from __future__ import absolute_import, division, print_function, unicode_literals
# import argparse
from datetime import date, datetime
import json
import logging
import os
import random
import sys
#
# Non-standard imports
#
# import exifread
import requests
#
# Ensure . is in the lib path for local includes
#
sys.path.append(os.path.realpath('.'))
#
# pylint: disable=wrong-import-position
# local directory imports here
#
from smug import SmugRss
#
####################################################################################
#
# pylint: disable=too-many-instance-attributes
class SlideShow(object):
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
    def __init__(self, gallery_id=None, height=None, width=None):
        super(SlideShow, self).__init__()

        self._logger = logging.getLogger(type(self).__name__)

        self._cache = {}
        self._cache_size = 0

        self._height = height
        self.__width = width

        self._loop_pos = 0

        # load the gallery RSS - do this last
        self._gallery = None
        self._gallery_id = gallery_id
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
    ##############################################################################
    #
    # find_best_image_size()
    #
    def find_best_image_size(self):
        '''
        find_best_image_size() - Choose the best size image for the set W x H
        '''
        img = None
        media_content = self._gallery[self._loop_pos].get('media_content')
        self._logger.info("Searching for an image...")
        if None not in [media_content]:

            for image in media_content:
                self._logger.debug(self._json_dump(image, True))

                # sometimes the crop sizes aren't quite even in both dimensions -
                # check +/- 15 pixels
                if (
                        (self.__width - 15) <= int(image.get('width')) <= (self.__width + 15) or
                        (self._height - 15) <= int(image.get('height')) <= (self._height + 15)
                    ):
                    img = image
                    self._logger.debug("Found a match: %s", self._json_dump(image, True))
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
    def load_gallery(self, gallery_id=None, shuffle=True):
        '''
        load_gallery(gallery_id, shuffle) - Load the feed for the provided Gallery id
        '''
        self._gallery = None

        gallery_id = gallery_id if gallery_id else self._gallery_id

        if None not in [gallery_id]:
            self._logger.info("Loading gallery with id '%s'", gallery_id)
            smugmug = SmugRss(site_url='www.azriel.photo', nickname='azriel')
            self._gallery = smugmug.get_gallery_feed(gallery=gallery_id)

            if shuffle:
                random.shuffle(self._gallery)
    #
    ##############################################################################
    #
    # load_image()
    #
    def load_image(self, image_url=None):
        '''
        load_image(image_url) - Load image data from the provided URL
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
        current() - return the data for the current image
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
        next() - return the data for the next image
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
        previous() - return the data for the next image
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
