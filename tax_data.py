"""Canadian tax parameters for the 2025 tax year (employment income only).

Brackets are (upper limit, rate); the last bracket has an infinite limit.
Update this file each January; calc.py needs no changes.
"""

INF = float("inf")

PROVINCES = {
    "AB": "Alberta", "BC": "British Columbia", "MB": "Manitoba",
    "NB": "New Brunswick", "NL": "Newfoundland and Labrador",
    "NS": "Nova Scotia", "NT": "Northwest Territories", "NU": "Nunavut",
    "ON": "Ontario", "PE": "Prince Edward Island", "QC": "Quebec",
    "SK": "Saskatchewan", "YT": "Yukon",
}

# Federal: lowest rate is 14.5% for 2025 (15% cut to 14% on July 1, blended).
FEDERAL = {
    "brackets": [(57_375, .145), (114_750, .205), (177_882, .26), (253_414, .29), (INF, .33)],
    "credit_rate": .145,
    "bpa_max": 16_129, "bpa_min": 14_538,   # BPA shrinks between the 4th bracket's bounds
    "bpa_phase": (177_882, 253_414),
    "canada_employment": 1_471,
    "quebec_abatement": .165,
}

# Payroll contributions. Quebec has its own pension plan (QPP), EI rate and QPIP.
PAYROLL = {
    "cpp": {"rate": .0595, "ympe": 71_300, "exemption": 3_500, "base_share": 4.95 / 5.95},
    "cpp2": {"rate": .04, "yampe": 81_200},
    "ei": {"rate": .0164, "max_insurable": 65_700},
    "qpp": {"rate": .064, "ympe": 71_300, "exemption": 3_500, "base_share": 5.4 / 6.4},
    "qpp2": {"rate": .04, "yampe": 81_200},
    "ei_qc": {"rate": .0131, "max_insurable": 65_700},
    "qpip": {"rate": .00494, "max_insurable": 98_000},
}

# Provincial: brackets, basic personal amount, and credit rate (lowest bracket rate).
PROVINCIAL = {
    "AB": {"brackets": [(60_000, .08), (151_234, .10), (181_481, .12), (241_974, .13), (362_961, .14), (INF, .15)], "bpa": 22_323},
    "BC": {"brackets": [(49_279, .0506), (98_560, .077), (113_158, .105), (137_407, .1229), (186_306, .147), (259_829, .168), (INF, .205)], "bpa": 12_932},
    "MB": {"brackets": [(47_000, .108), (100_000, .1275), (INF, .174)], "bpa": 15_780},
    "NB": {"brackets": [(51_306, .094), (102_614, .14), (190_060, .16), (INF, .195)], "bpa": 13_396},
    "NL": {"brackets": [(44_192, .087), (88_382, .145), (157_792, .158), (220_910, .178), (282_214, .198), (564_429, .208), (1_128_858, .213), (INF, .218)], "bpa": 11_067},
    "NS": {"brackets": [(30_507, .0879), (61_015, .1495), (95_883, .1667), (154_650, .175), (INF, .21)], "bpa": 11_744},
    "NT": {"brackets": [(51_964, .059), (103_930, .086), (168_967, .122), (INF, .1405)], "bpa": 17_842},
    "NU": {"brackets": [(54_707, .04), (109_413, .07), (177_881, .09), (INF, .115)], "bpa": 19_274},
    "ON": {"brackets": [(52_886, .0505), (105_775, .0915), (150_000, .1116), (220_000, .1216), (INF, .1316)], "bpa": 12_747,
           "surtax": [(5_710, .20), (7_307, .36)]},
    "PE": {"brackets": [(33_328, .095), (64_656, .1347), (105_000, .166), (140_000, .1762), (INF, .19)], "bpa": 14_250},
    "QC": {"brackets": [(53_255, .14), (106_495, .19), (129_590, .24), (INF, .2575)], "bpa": 18_571},
    "SK": {"brackets": [(53_463, .105), (152_750, .125), (INF, .145)], "bpa": 18_491},
    "YT": {"brackets": [(57_375, .064), (114_750, .09), (177_882, .109), (500_000, .128), (INF, .15)], "bpa": 16_129},
}
