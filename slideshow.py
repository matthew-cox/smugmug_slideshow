#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
'''
Run a SmugMug Slideshow
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
# from pygame.locals import *
#
# Ensure . is in the lib path for local includes
#
sys.path.append(os.path.realpath('.'))
#
# pylint: disable=wrong-import-position
# local directory imports here
#
from smug import Slideshow
#
##############################################################################
#
# Global Variables
#
DEFAULT_LOG_LEVEL = 'WARNING'

# How long to display each image (in seconds)
DISPLAY_TIME = 45 * 1000

GALLERY_ID = '159365802_Wp7NDr'

STARTUP_TEXT = """

SmugMug Slideshow

[Escape]    Stop the show
[  <-  ]    Previous image
[  ->  ]    Next image

"""
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
    max_y = info.current_h
    max_x = info.current_w

    _get_logger().info(info)

    # pylint: disable=no-member
    display.set_mode((max_x, max_y), pygame.NOFRAME)
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
    fonts = {}
    fonts['font_path'] = pygame.font.match_font(u'arial')
    _get_logger().info(fonts['font_path'])
    fonts['small'] = pygame.font.Font(fonts['font_path'], 20)
    fonts['medium'] = pygame.font.Font(fonts['font_path'], 30)
    fonts['large'] = pygame.font.Font(fonts['font_path'], 60)

    return fonts
#
##############################################################################
#
# draw_image()
#
def draw_image(image_file=None):
    '''
    draw_image(display, image_file) - Draw the provided image on the global display
    '''
    update_display = False

    if None not in [display, image_file]:

        # pylint: disable=bare-except
        try:
            picture = image.load(image_file)

            main_surface = display.get_surface()
            imagepos = picture.get_rect()
            imagepos.centerx = main_surface.get_rect().centerx
            imagepos.centery = main_surface.get_rect().centery
            main_surface.blit(picture, imagepos)
            update_display = True
        except:
            update_display = False
    return update_display
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

    # pylint: disable=no-member
    pygame.init()

    # init the pygame dislay (Sloooooow)
    init_display()

    info = display.Info()

    slide_show = Slideshow(gallery_id=GALLERY_ID, height=info.current_h, width=info.current_w)

    # init fonts
    # fonts = init_fonts()

    # Load main display area
    # main_surface = pygame.display.get_surface()
    #
    # center_x = main_surface.get_rect().centerx
    # center_y = main_surface.get_rect().centery

    # Display startup message for 5 seconds
    # text = fonts['large'].render(STARTUP_TEXT, 1, (0, 0, 0))
    # main_surface.blit(text, (center_x, center_y))
    # display.flip()
    # pygame.time.delay(5000)

    # Start by drawing the first image
    draw_image(image_file=BytesIO(slide_show.current()))

    # draw an image every so often by sending an event on an interval
    # pylint: disable=no-member
    time.set_timer(pygame.USEREVENT, DISPLAY_TIME)

    # the event loop
    while 1:

        update = True
        try:
            for event in pygame.event.get():

                # pylint: disable=no-member
                if event.type == pygame.QUIT:
                    sys.exit(0)

                # keypresses
                # pylint: disable=no-member
                if event.type == pygame.KEYUP:
                    # look for escape key
                    # pylint: disable=no-member
                    if event.key == pygame.K_ESCAPE:
                        sys.exit(0)

                    # left arrow - display the previous image
                    # pylint: disable=no-member
                    if event.key == pygame.K_LEFT:
                        # Draw the image
                        update = draw_image(image_file=BytesIO(slide_show.previous()))

                    # right arrow - display the next image
                    # pylint: disable=no-member
                    if event.key == pygame.K_RIGHT:
                        # Draw the image
                        update = draw_image(image_file=BytesIO(slide_show.next()))

                # image display events
                # pylint: disable=no-member
                if event.type == pygame.USEREVENT:
                    # Draw the image
                    update = draw_image(image_file=BytesIO(slide_show.next()))

                # Update the display - sometimes can't find a good image size match
                if update:
                    display.flip()
        except KeyboardInterrupt:
            sys.exit(0)

if __name__ == '__main__':
    main()
