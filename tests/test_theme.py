# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals, absolute_import
from unittest import TestCase
from totv.theme import *


class TestTheme(BaseTheme):
    name = "test_theme"
    sep_char = " | "
    pair_sep = " = "
    group_sep_char = " / "
    value_sep = ": "
    wrap_chars_start = "["

    wrap_chars_end = "]"

    title = RED_LT

    # Separator between entities
    sep = GREEN_LT

    # Key in KeyValue pair
    key = GREEN

    # Value in KeyValue pair
    value = ORANGE


class ThemeTest(TestCase):

    def setUp(self):
        load_theme(TestTheme())

    def test_colourize(self):
        s = "hi"
        s_1 = colourize(fg=RED_LT, message=s)
        s_2 = colourize(fg=RED_LT, bg=BLUE, message=s)
        s_3 = colourize(fg=RED_LT, message=s, auto_end=False)
        s_4 = colourize(fg=RED_LT, bg=BLUE, message=s, auto_end=False)

        self.assertEqual(s_1, "\x0304hi\x0f")
        self.assertEqual(s_2, "\x0304,02hi\x0f")
        self.assertEqual(s_3, "\x0304hi")
        self.assertEqual(s_4, "\x0304,02hi")


    def test_load_theme(self):
        theme_a = TestTheme()
        theme_a.title = YELLOW
        load_theme(theme_a)
        a_value = get_value("title")
        self.assertEqual(a_value, YELLOW)

        theme_b = TestTheme()
        theme_b.title = RED_LT
        load_theme(theme_b)
        b_value = get_value("title")
        self.assertEqual(b_value, RED_LT)

    def test_entity_render(self):
        self.assertEqual(str(Entity("a", "b")), Entity("a", "b").render())
        self.assertEqual(Entity("a", "b").render(), "\x0303a\x0f: \x0307b\x0f")
        self.assertEqual(str(Entity("a", "b")), "\x0303a\x0f: \x0307b\x0f")
        self.assertEqual(str(Entity("a")), Entity("a").render())
        self.assertEqual(Entity("a").render(), "\x0303a\x0f")

    def test_group_render(self):
        r = EntityGroup([Entity("uploaded", "100 TB"), Entity("downloaded", "54 TB")]).render()
        self.assertEqual(r, "[ \x0303uploaded\x0f: \x0307100 TB\x0f / \x0303downloaded\x0f: \x030754 TB\x0f ]")

    def test_render(self):
        out = render(
            title="Test Title",
            items=[
                Entity("Key", "Value"),
                EntityGroup([
                    Entity("A", "AValue"),
                    Entity("B", "BValue"),
                    Entity("C")
                ])
            ]
        ).encode()
        self.assertEqual(b'\x0304Test Title\x0f | \x0303Key\x0f: \x0307Value\x0f | '
                         b'[ \x0303A\x0f: \x0307AValue\x0f / \x0303B\x0f: \x0307BVa'
                         b'lue\x0f / \x0303C\x0f ]', out)
