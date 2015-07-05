# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import
import logging
from datetime import datetime, timedelta
from collections import OrderedDict
from lxml import objectify
from urllib.parse import urlencode
from pytz import timezone, utc
from dateutil import parser as date_parser
import requests


logger = logging.getLogger(__name__)
base_url = "http://services.tvrage.com/myfeeds/"
NO_NEXT_EPISODE = 80085

zone = timezone("US/Eastern")


def schedule(key, offset=0):
    resp_xml = requests.get("{}{}".format(base_url, "fullschedule.php"), params=urlencode({'key': key}))
    resp = objectify.fromstring(bytes(resp_xml.text.encode('utf8', 'replace')))
    schedule_data = {}
    cur_time = datetime.now(tz=utc).astimezone(zone)
    # Stupid fix for tvrage returning single digit months
    today_date_fmt = datetime.now(tz=utc).astimezone(timezone("US/Pacific")).strftime("%Y-{}-%-d")
    date = int(datetime.now(tz=utc).astimezone(timezone("US/Pacific")).strftime("%m")) + offset
    today_date = today_date_fmt.format()
    for i, day in enumerate(resp.DAY):
        if day.attrib['attr'] == today_date:
            schedule_data['date'] = day.attrib['attr']
            schedule_data['hours'] = OrderedDict()
            for j, hour in enumerate(resp.DAY[i].getchildren()):
                hour_name = hour.attrib['attr']
                schedule_data['hours'][hour_name] = list()

                for show in hour[j].getchildren():
                    show_time = parse_hour(hour_name)
                    airs_in = (show_time - cur_time) + timedelta(hours=3)
                    schedule_data['hours'][hour_name].append({
                        'showid': show.sid.pyval,
                        'title': show.title.pyval,
                        'link': show.link.pyval,
                        'network': show.network.pyval,
                        'ep': show.ep.pyval,
                        'name': show.attrib['name'],
                        'airs_in': airs_in
                    })
            break
    return schedule_data


def tz(dt=None, fmt="%Y-%m-%d"):

    if not dt:
        dt = datetime.now(tz=utc)
    #= zone.localize(dt if dt else datetime.now())
    zone_time = dt.astimezone(zone)
    zone_time_fmt = zone_time.strftime(fmt)
    return zone_time_fmt


def _parse_tvrage_date(date_str):
    return date_parser.parse(date_str)


def parse_hour(hr):
    time, ampm = hr.split(" ")
    hr, mn = map(int, time.split(":"))
    t = datetime.now(tz=timezone("US/Pacific"))
    if ampm == "pm":
        hr += 11
    parsed_time = datetime(t.year, t.month, t.day, hour=hr, minute=mn, tzinfo=zone)
    return parsed_time
