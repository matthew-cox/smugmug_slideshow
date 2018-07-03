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
import argparse
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

FONT = 'courier'

STARTUP_TEXT = """SmugMug Slideshow

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
    Initialize pygame display
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
    Initialize pygame fonts

    Returns:
        dict: Dictionary of font path and three loaded font sizes
    '''
    pygame.font.init()
    fonts = {}
    fonts['font_path'] = pygame.font.match_font(FONT)
    _get_logger().info(fonts['font_path'])
    fonts['small'] = pygame.font.Font(fonts['font_path'], 20)
    fonts['medium'] = pygame.font.Font(fonts['font_path'], 30)
    fonts['large'] = pygame.font.Font(fonts['font_path'], 60)

    return fonts
#
##############################################################################
#
# scale_picture()
#
def scale_image(img=None, size=None):
    '''
    Take a loaded image and scale it to the max size that will fit in the width x height provided
        while preserving the aspect ratio of the original.

    Inspiration fron: https://www.pygame.org/pcr/transform_scale/index.php

    Args:
        picture (pygame.image): The image to scale
        size (set): Two member set of width and height

    Return:
        pygame.image: Image result (might be unchanged)

    Raises:
        RuntimeError: If any arguments are missing
    '''

    if None in [img, size]:
        raise RuntimeError("Missing an argument!")

    img_w, img_h = img.get_size()
    target_w, target_h = size

    new_w = new_h = None

    new_image = img

    # pick which way to scale
    if img_w >= img_h:
        # fit to width
        scale_factor = img_w / float(target_w)
        _get_logger().debug("Width scale factor is '%i'", scale_factor)

        new_h = scale_factor * img_h
        _get_logger().debug("Height scaled from '%i' to '%i'", img_h, new_h)

        if new_h > target_h:
            _get_logger().debug("New height is too big ('%i' > '%i')", new_h, target_h)

            scale_factor = target_h / float(img_h)
            _get_logger().debug("Width scale factor is now '%i'", scale_factor)

            new_w = scale_factor * img_w
            _get_logger().debug("Width scaled from '%i' to '%i'", img_w, new_w)
            new_h = target_h
        else:
            _get_logger().info("Width scaled from '%i' to '%i'", img_w, target_w)
            new_w = target_w
    else:
        # fit to height
        scale_factor = img_h / float(target_h)
        _get_logger().debug("Height scale factor is '%i'", scale_factor)

        new_w = scale_factor * img_w
        _get_logger().debug("Width scaled from '%i' to '%i'", img_w, new_w)

        if new_w > target_w:
            _get_logger().debug("New width is too big ('%i' > '%i')", new_w, target_w)

            scale_factor = new_w / float(img_w)
            _get_logger().debug("Height scale factor is now '%i'", scale_factor)

            new_w = target_w
            new_h = scale_factor * img_h
            _get_logger().debug("Height scaled from '%i' to '%i'", img_h, new_h)
        else:
            _get_logger().debug("Height scaled from '%i' to '%i'", img_h, target_h)
            new_h = target_h

    if (new_h == img_h) or (new_w == img_w):
        _get_logger().info("No scale!")
    else:
        _get_logger().info("Scaling to new dimensions (%i, %i)", new_w, new_h)
        new_image = pygame.transform.scale(img, (int(new_w), int(new_h)))

    return new_image

#
##############################################################################
#
# draw_image()
#
def draw_image(surface=None, image_file=None):
    '''
    Draw the provided image on the global display

    Args:
        surface (pygame.display): On which display to draw.
        image_file (str or buffer): File path on disk or binary buffer

    Returns:
        True or False indicating sucess and that the display should be updated
    '''
    update_display = False

    surface = display.get_surface() if None in [surface] else surface

    if None not in [surface, image_file]:

        # pylint: disable=bare-except
        try:
            picture = image.load(image_file)

            picture = scale_image(img=picture, size=surface.get_size())

            # clear the previous displayed image
            surface.fill(pygame.Color('black'))
            imagepos = picture.get_rect()
            imagepos.centerx = surface.get_rect().centerx
            imagepos.centery = surface.get_rect().centery
            surface.blit(picture, imagepos)
            update_display = True
        except:
            update_display = False
    return update_display
#
##############################################################################
#
# draw_multiline_text()
#
def draw_multiline_text(surface=None, text=None, pos=None, font=None, color=pygame.Color('white')):
    '''
    Render multiple lines of text. Adapted from:
    https://stackoverflow.com/questions/42014195/rendering-text-with-multiple-lines-in-pygame

    Args:
        color (pygame.color): Default white
        font (pygame.font): Required
        pos (set): Two position set x and y where to start drawing the text
        surface (pygame.display): Required
        text (str): Required

    Raises:
        RuntimeError: For any missing argument
        Probably Pygame exception or something
    '''

    if None in [surface, text, pos, font]:
        raise RuntimeError("Missing a required argument!")

    # Create 2D array where each row is a list of words.
    words = [word.split(' ') for word in text.splitlines()]

    # The width of a space.
    space = font.size(' ')[0]

    max_width = surface.get_size()[0]

    current_x, current_y = pos
    for line in words:
        for word in line:
            word_surface = font.render(word, 0, color)
            word_width, word_height = word_surface.get_size()
            if current_x + word_width >= max_width:
                current_x = pos[0]  # Reset the x.
                current_y += word_height  # Start on new row.
            surface.blit(word_surface, (current_x, current_y))
            current_x += word_width + space
        current_x = pos[0]  # Reset the x.
        current_y += word_height  # Start on new row.
#
##############################################################################
#
# main()
#
def handle_arguments():
    '''
    Parse command line arguments

    Returns:
        argparse.Namespace: Representation of provided arguments
    '''
    #
    # Handle CLI args
    #
    parser = argparse.ArgumentParser(description='Run a slideshow of a SmugMug gallery')

    # add arguments
    group = parser.add_mutually_exclusive_group(required=True)

    group.add_argument('-g', '--gallery-id', action='store', help='Gallery Id to display')
    group.add_argument('-u', '--gallery-url', action='store', help='URL of Gallery to display')

    parser.add_argument("--debug", action='store_true', required=False, default=False,
                        help="Enable debug mode. Increases verbosity and shortens display time.")

    parser.add_argument("--display-time", action='store', required=False, default=DISPLAY_TIME,
                        help="Time in milliseconds to display image. Default: {}".format(DISPLAY_TIME))

    parser.add_argument('-d', '--downscale-only', action='store_true', required=False,
                        help='Do not upscale images.', default=False)

    parser.add_argument('-l', '--log-level', action='store', required=False,
                        choices=["debug", "info", "warning", "error", "critical"],
                        default=DEFAULT_LOG_LEVEL,
                        help='Logging verbosity. Default: {}'.format(DEFAULT_LOG_LEVEL))

    return parser.parse_args()
#
##############################################################################
#
# main()
#
def main():
    '''
    Run the slideshow
    '''

    args = handle_arguments()

    if args.debug:
        args.log_level = 'INFO'
        args.display_time = 5 * 1000

    # Configure logging
    logging.basicConfig(format='%(levelname)s:%(module)s.%(funcName)s:%(message)s',
                        level=getattr(logging, args.log_level.upper()))

    # pylint: disable=no-member
    pygame.init()

    # init the pygame dislay (Sloooooow)
    init_display()

    info = display.Info()

    slide_show = Slideshow(gallery_id=args.gallery_id, gallery_url=args.gallery_url,
                           downscale=args.downscale_only, height=info.current_h,
                           width=info.current_w)

    # init fonts
    fonts = init_fonts()

    # Load main display area
    main_surface = pygame.display.get_surface()
    main_surface.fill(pygame.Color('black'))

    center_x = main_surface.get_rect().centerx
    center_y = main_surface.get_rect().centery

    # Display startup message for 5 seconds
    draw_multiline_text(surface=main_surface, text=STARTUP_TEXT, pos=(center_x, center_y),
                        font=fonts['medium'])
    display.flip()
    pygame.time.delay(5000)

    # Start by drawing the first image
    draw_image(image_file=BytesIO(slide_show.current()))

    # draw an image every so often by sending an event on an interval
    # pylint: disable=no-member
    time.set_timer(pygame.USEREVENT, args.display_time)

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
