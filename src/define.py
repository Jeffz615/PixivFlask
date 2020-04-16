# -*- coding: utf-8 -*-
from os import path

PATHDIR = path.dirname(path.dirname(path.abspath(__file__)))
STATICPATH = path.join(PATHDIR, "static")

MODELIST = ["day", "week", "month", "day_male", "day_female",
            "week_original", "week_rookie", "day_manga", "day_r18", "day_male_r18",
            "day_female_r18", "week_r18", "week_r18g"]
NORMALMODE = ["day", "week", "month", "day_male", "day_female",
              "week_original", "week_rookie", "day_manga"]
R18MODE = ["day_r18", "day_male_r18",
           "day_female_r18", "week_r18", "week_r18g"]

PIXIVCAT = "i.pixiv.cat"
