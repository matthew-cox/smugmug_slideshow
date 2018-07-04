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
import math
import os
try:
    from pathlib import Path
except ModuleNotFoundError:
    from pathlib2 import Path
import sys
#
# Non-standard imports
#
from io import BytesIO

import PIL
# pylint: disable=unused-import
from PIL import Image

import pygame
from pygame import display, image, time
# from pygame.locals import *

#
# Ensure ./lib is in the lib path for local includes
#
LIB_PATH = Path(__file__).resolve().parent / 'lib'
sys.path.append(str(LIB_PATH))
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
DEFAULT_LOG_LEVEL = 'WARNING' if not os.environ.get('PY_LOG_LEVEL') else os.environ['PY_LOG_LEVEL']

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
    '''
    Reusable code to get the correct logger by name of current file

    Returns:
        logging.logger: Instance of logger for name of current file
    '''
    return logging.getLogger(Path(__file__).resolve().name)
#
##############################################################################
#
# _json_dump() - Little output to DRY
#
def _json_dump(the_thing, pretty=False):
    '''
    Reusable JSON dumping code

    Returns:
        str: JSON string representation suitable for print'ing
    '''
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
# resize_contain()
#
def resize_contain(the_image=None, size=None):
    """
    Resize image according to size.

    Inspiration fron:
    https://github.com/charlesthk/python-resize-image/blob/master/resizeimage/resizeimage.py#L98

    Args:
        image (PIL.Image): A Pillow image instance
        size (list): A list of two integers [width, height]

    Returns:
        PIL.Image: Scaled image results
    """
    img_format = the_image.format
    img = the_image.copy()
    # NOTE: LANCZOS might be another good filter choice
    img.thumbnail(size, PIL.Image.HAMMING)

    # FIll with black. Non-alpha mode
    background = PIL.Image.new('RGB', size, (0, 0, 0))
    img_position = (
        int(math.ceil((size[0] - img.size[0]) / 2)),
        int(math.ceil((size[1] - img.size[1]) / 2))
    )
    background.paste(img, img_position)
    background.format = img_format
    return background
#
##############################################################################
#
# scale_image()
#
def scale_image(img=None, size=None):
    '''
    Take loaded image bytes and scale it to the max size that will fit in the width x height
        provided while preserving the aspect ratio of the original.

    Inspiration fron:
    https://github.com/charlesthk/python-resize-image/blob/master/resizeimage/resizeimage.py#L98

    Args:
        picture (BytesIO): The image data to scale
        size (set): Two member set of width and height

    Return:
        pygame.image: Image result (might be unchanged)

    Raises:
        RuntimeError: If any arguments are missing
    '''

    # Make a copy, which is stupid, but everything that touches img closes it
    tmp_img = BytesIO(img.getvalue())
    result = pygame.image.load(tmp_img)

    if None in [img, size]:
        raise RuntimeError("Missing an argument!")

    scaled = None
    # pylint: disable=broad-except
    try:
        with PIL.Image.open(img) as pil_image:
            scaled = resize_contain(pil_image, size)
    except Exception as err:
        _get_logger().error("Scaling failed: '%s'", err)

    try:
        result = pygame.image.fromstring(scaled.tobytes(), scaled.size, scaled.mode)
    except Exception as err:
        _get_logger().error("Loading failed: '%s'", err)

    return result
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
        bool: True or False indicating sucess and that the display should be updated
    '''
    update_display = False

    surface = display.get_surface() if None in [surface] else surface

    if None in [surface, image_file]:
        _get_logger().warning("Missing required argument. No-op.")

    else:
        _get_logger().info("Trying to scale the image...")
        # pylint: disable=bare-except
        try:
            picture = scale_image(img=image_file, size=surface.get_size())

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
                        help="Enable debug mode. Increases verbosity and shortens show time.")

    parser.add_argument('-d', '--downscale-only', action='store_true', required=False,
                        help=('Enable downscale mode. Prefer images larger than the display. '
                              'Default: False'), default=False)

    parser.add_argument('-l', '--log-level', action='store', required=False,
                        choices=["debug", "info", "warning", "error", "critical"],
                        default=DEFAULT_LOG_LEVEL.upper(),
                        help='Logging verbosity. Default: {}'.format(DEFAULT_LOG_LEVEL.upper()))

    parser.add_argument("--show-time", action='store', required=False, default=DISPLAY_TIME,
                        help="Time in milliseconds to show image. Default: {}".format(DISPLAY_TIME))

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
        # 5 seconds is too fast once images are cached: one cannot interupt easily
        args.show_time = 10 * 1000

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
    update = draw_image(image_file=BytesIO(slide_show.current()))
    # update = draw_image(image_file=slide_show.current())
    if update:
        display.flip()

    # draw an image at set intervals by sending an event on an interval
    # pylint: disable=no-member
    time.set_timer(pygame.USEREVENT, args.show_time)

    # the event loop
    while 1:

        update = True
        try:
            # pylint: disable=no-member
            for event in pygame.event.get():


                if event.type == pygame.QUIT:
                    sys.exit(0)

                # keypresses
                if event.type == pygame.KEYUP:
                    # look for escape key
                    if event.key == pygame.K_ESCAPE:
                        sys.exit(0)

                    # left arrow - display the previous image
                    if event.key == pygame.K_LEFT:
                        # Draw the image
                        update = draw_image(image_file=BytesIO(slide_show.previous()))

                    # right arrow - display the next image
                    if event.key == pygame.K_RIGHT:
                        # Draw the image
                        update = draw_image(image_file=BytesIO(slide_show.next()))

                # image display events
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
