#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
'''
SmugMug Test
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
import sys
#
# Non-standard imports
#
from io import BytesIO
import pygame
from pygame import display, image, time
from pygame.locals import *
#
# Ensure . is in the lib path for local includes
#
sys.path.append(os.path.realpath('.'))
#
# pylint: disable=wrong-import-position
# local directory imports here
#
from slideshow import SlideShow
#
##############################################################################
#
# Global Variables
#
DEFAULT_LOG_LEVEL = 'WARNING'

DISPLAY_TIME = 45 * 1000

GALLERY_ID = '159365802_Wp7NDr'


#
##############################################################################
#
# _get_logger() - reusable code to get the correct logger by name
#
def _get_logger():
    '''_get_logger() - reuable code to get the correct logger by name'''
    return logging.getLogger(os.path.basename(__file__))
#
##############################################################################
#
# _json_dump() - Little output to DRY
#
def _json_dump(the_thing, pretty=False):
    '''_json_dump() - Little output to DRY'''
    output = None
    if pretty:
        output = json.dumps(the_thing, default=_json_serial, sort_keys=True, indent=4,
                            separators=(',', ': '))
    else:
        output = json.dumps(the_thing, default=_json_serial)
    return output

def _json_serial(obj):
    '''JSON serializer for objects not serializable by default json code'''

    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError("Type %s not serializable" % type(obj))
#
##############################################################################
#
# init_display()
#
def init_display():
    '''
    init_display() - init pygame display
    '''
    # Get the size of the display
    display.init()
    # Hide the mouse
    pygame.mouse.set_visible(0)
    info = display.Info()
    _get_logger().info(info)
#
##############################################################################
#
# init_fonts()
#
def init_fonts():
    '''
    init_fonts() - init pygame fonts
    '''
    pygame.font.init()
    font_path = pygame.font.match_font(u'arial')
    _get_logger().info(font_path)
    small_font = pygame.font.Font(font_path, 20)
    medium_font = pygame.font.Font(font_path, 30)
    large_font = pygame.font.Font(font_path, 60)

    return(small_font, medium_font, large_font)


#
##############################################################################
#
# draw_image()
#
def draw_image(image_file=None):
    '''
    draw_image(display, image_file) - Draw the provided image on the global display
    '''

    if None not in [display, image_file]:

        info = display.Info()
        max_y = info.current_h
        max_x = info.current_w

        picture = image.load(image_file)

        display.set_mode((max_x, max_y), pygame.NOFRAME)
        main_surface = display.get_surface()
        imagepos = picture.get_rect()
        imagepos.centerx = main_surface.get_rect().centerx
        imagepos.centery = main_surface.get_rect().centery
        main_surface.blit(picture, imagepos)




#
##############################################################################
#
# main()
#
def main():
    '''
    main() - Run the slide show
    '''
    # Configure logging
    logging.basicConfig(format='%(levelname)s:%(module)s.%(funcName)s:%(message)s',
                        level=getattr(logging, DEFAULT_LOG_LEVEL))

    pygame.init()

    # init the pygame dislay (Sloooooow)
    init_display()

    info = display.Info()

    slide_show = SlideShow(gallery_id=GALLERY_ID, height=info.current_h, width=info.current_w)

    # draw an image every so often by sending an event on an interval
    time.set_timer(pygame.USEREVENT, DISPLAY_TIME)

    # draw the first image
    image_data = slide_show.current()
    # Draw the image
    draw_image(image_file=BytesIO(image_data))

    # the event loop
    while 1:

        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                sys.exit(0)

            # keypresses
            if event.type == pygame.KEYUP:
                # look for escape key
                if event.key == pygame.K_ESCAPE:
                    sys.exit(0)

                # left arrow - display the previous image (can I do this better?)
                if event.key == pygame.K_LEFT:
                    image_data = slide_show.previous()
                    # Draw the image
                    draw_image(image_file=BytesIO(image_data))

                # right arrow - display the next image
                if event.key == pygame.K_RIGHT:
                    image_data = slide_show.next()
                    # Draw the image
                    draw_image(image_file=BytesIO(image_data))

            # image display events
            if event.type == pygame.USEREVENT:
                image_data = slide_show.next()
                # Draw the image
                draw_image(image_file=BytesIO(image_data))

            # Update the display
            display.flip()

if __name__ == '__main__':
    main()
