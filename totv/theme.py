# -*- coding: utf-8 -*-
"""
Simple theme support for the bot to keep message output uniform across the various
modules in use.

Basic usage, create a theme based on BaseTheme and load it:

>>> class MyTheme(BaseTheme):
>>>     title = RED_LT
>>>
>>> load_theme(MyTheme())
>>>

"""
from __future__ import unicode_literals, absolute_import
import abc
import random


# Special chars
IP_CHAR = "π"
NUKE = "☢"
UNNUKE = "☮"

# Colour codes
WHITE = 0
BLACK = 1
BLUE = 2
GREEN = 3
RED_LT = 4
BROWN = 5
PURPLE = 6
ORANGE = 7
YELLOW = 8
GREEN_LT = 9
CYAN = 10
CYAN_LT = 11
BLUE_LT = 12
PINK = 13
GREY = 14
GREY_LT = 15

# mirc only?
TRANS = 99

# Control characters
BOLD_CODE = "\002"
COLOUR_CODE = "\003"
NORMAL = "\017"
REVERSE = "\026"
UNDERLINE = "\037"


def colourize(fg: int=None, bg: int=None, message: str="", auto_end: bool=True) -> str:
    """ Generate a colour coded IRC message

    :param fg: Foreground colour code
    :type fg: int
    :param bg: Background colour code
    :type bg: int, None
    :param message: optional message to colourise
    :type message: unicode, int
    :param auto_end: Reset the colours at the end of the message
    :type auto_end: bool
    :return: Colour coded message
    :rtype: unicode
    """
    if not fg and not bg:
        # Reset colouring
        code = NORMAL
    elif fg and not bg:
        code = "{0}{1:02d}".format(COLOUR_CODE, fg)
    else:
        code = "{0}{1:02d},{2:02d}".format(COLOUR_CODE, fg, bg)
    return "".join([code, message, NORMAL if auto_end else ""])


class BaseTheme(object):
    name = "base_theme"

    # Used as separator between KeyValue/other pair elements in the message
    sep_char = colourize(fg=BLUE_LT, message=" :: ")

    sep_char_alt = "☆"

    group_sep_char = " / "

    pair_sep = " :: "

    value_sep = ": "

    # Used to apply wrapping characters around entities
    wrap_chars_start = colourize(fg=BLUE_LT, message="[")

    wrap_chars_end = colourize(fg=BLUE_LT, message="]")

    # Title/Subject of the message eg: "New PM"
    title = YELLOW

    # Separator between entities
    sep = GREEN_LT

    # Key in KeyValue pair
    key = GREEN

    # Value in KeyValue pair
    value = ORANGE

    def error(self, message: str, command: str=""):
        title = "Error/{}".format(command) if command else "Error"
        return render(items=[
            EntityGroup([Entity(title)]),
            EntityGroup([Entity(message)])
        ])


_theme = BaseTheme()


def random_colour(min_colour=2, max_colour=15):
    """ Generate a random colour code

    :param min_colour: Minimum colour code
    :type min_colour: int
    :param max_colour: Maximum colour code
    :type max_colour: int
    :return: Colour code within specified range
    :rtype: int
    """
    return random.randint(min_colour, max_colour)


class Renderable(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def render(self):
        """ Renders the object for display on IRC """
        return


class Entity(Renderable):
    """ A simple renderable entity that can accommodate a key->value pair used in messages. Eg:

    >>> Entity("Uploaded", "169").render()
    "\x0302Uploaded: \x0303169"

    Or, If the value is omitted, only the key will be output. Eg:

    >>> Entity("Uploaded").render()
    "\x0302Uploaded"

    """

    def __init__(self, key, value=None):
        self.key = str(key)
        self.value = str(value) if value is not None else ""

    def render(self):
        if self.value:
            return "".join([
                colourize(fg=_theme.key, message=self.key),
                _theme.value_sep,
                colourize(fg=_theme.value, message=self.value)
            ])
        else:
            return colourize(fg=_theme.key, message=self.key)

    def __unicode__(self):
        return self.render()

    def __str__(self):
        return self.render()


class EntityGroup(list, Renderable):
    def render(self):
        return wrap(_theme.group_sep_char.join([item.render() for item in self if item]))


def wrap(message, spacing=1):
    """ Wraps a string in the wrap characters defined in the theme. Supports any spacing
    level.

    :param message: message to wrap
    :type message: str
    :param spacing: number of spaces to put between the message and wrap characeter
    :type spacing: int
    :return: wrapped message
    :rtype: str
    """
    return (" " * spacing).join([_theme.wrap_chars_start, message, _theme.wrap_chars_end])


def load_theme(theme_instance):
    """ Sets a new theme instance as the currently active theme

    :param theme_instance: Theme class instance
    :type theme_instance: BaseTheme
    :raises TypeError:
    :return:
    :rtype:
    """
    global _theme
    if not isinstance(theme_instance, BaseTheme):
        raise TypeError("Theme must be subclass of theme.BaseTheme")
    _theme = theme_instance


def get_value(key):
    """ Get a value from the loaded theme

    :param key:
    :type key:
    :return:
    :rtype:
    """
    return getattr(_theme, key)


def render(title=None, items=None):
    if not items:
        items = []
    output = []
    if title:
        output.append(colourize(fg=_theme.title, message=title))
    output.extend(i.render() for i in items if i)
    output_str = _theme.sep_char.join(output)
    return output_str


def render_error(message, command=None):
    """ Returns a error message in a standardized format

    :param message: Error message to wrap
    :type message: str
    :param command: Optional command name that caused the error
    :type command: str
    :return: Themed/encoded error message
    :rtype: str
    """
    return _theme.error(message, command=command)
