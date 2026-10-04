"""Income tax and social contribution estimates for countries outside Canada.

Each function takes a gross annual salary in that country's currency and
returns {"items": [(label, amount), ...], "net": ...}. Figures are the 2025
tax year (UK 2025/26) for a single employee with salary income only.
"""

from calc import bracket_tax

INF = float("inf")

# Local currency units per 1 CAD. Approximate; editable in the app sidebar.
DEFAULT_FX = {"USD": 0.72, "GBP": 0.54, "EUR": 0.63, "CNY": 5.20}

# Country -> (currency, calculator args). Calculators are defined below.
UK_REGIONS = ["England", "Scotland", "Wales", "Northern Ireland"]


def _result(items: list, gross: float) -> dict:
    return {"items": items, "net": gross - sum(v for _, v in items)}


# ---------- United States ----------

US_BRACKETS = [(11_925, .10), (48_475, .12), (103_350, .22), (197_300, .24),
               (250_525, .32), (626_350, .35), (INF, .37)]


# State income tax (single filer, 2025). NYC resident tax is added on top for New York.
US_STATES = {
    "California": {
        "std_deduction": 5_706, "exemption_credit": 153,
        "brackets": [(11_079, .01), (26_264, .02), (41_452, .04), (57_542, .06), (72_724, .08),
                     (371_479, .093), (445_771, .103), (742_953, .113), (INF, .123)],
        "mental_health": (1_000_000, .01),
    },
    "New York": {
        "std_deduction": 8_000, "exemption_credit": 0,
        "brackets": [(8_500, .04), (11_700, .045), (13_900, .0525), (80_650, .055), (215_400, .06),
                     (1_077_550, .0685), (5_000_000, .0965), (25_000_000, .103), (INF, .109)],
    },
}
NYC_BRACKETS = [(12_000, .03078), (25_000, .03762), (50_000, .03819), (INF, .03876)]


def united_states(gross: float, state: str, nyc: bool = False) -> dict:
    taxable = max(0.0, gross - 15_750)  # federal standard deduction, single
    fed = bracket_tax(taxable, US_BRACKETS)
    ss = min(gross, 176_100) * .062
    medicare = gross * .0145 + max(0.0, gross - 200_000) * .009

    st = US_STATES[state]
    state_taxable = max(0.0, gross - st["std_deduction"])
    state_tax = max(0.0, bracket_tax(state_taxable, st["brackets"]) - st["exemption_credit"])
    if "mental_health" in st:
        over, rate = st["mental_health"]
        state_tax += max(0.0, state_taxable - over) * rate
    items = [("Federal income tax", fed), (f"{state} income tax", state_tax)]
    if nyc and state == "New York":
        items.append(("New York City income tax", bracket_tax(state_taxable, NYC_BRACKETS)))
    items += [("Social Security", ss), ("Medicare", medicare)]
    if state == "California":
        items.append(("California SDI", gross * .012))
    else:
        items.append(("NY disability + paid family leave", 31.20 + min(gross * .00388, 354.53)))
    return _result(items, gross)


# ---------- United Kingdom ----------

UK_BANDS = {  # on taxable income (after personal allowance)
    "rest": [(37_700, .20), (125_140, .40), (INF, .45)],
    "Scotland": [(2_827, .19), (14_921, .20), (31_092, .21), (62_430, .42), (125_140, .45), (INF, .48)],
}


def united_kingdom(gross: float, region: str = "England") -> dict:
    allowance = max(0.0, 12_570 - max(0.0, gross - 100_000) / 2)
    bands = UK_BANDS["Scotland" if region == "Scotland" else "rest"]
    tax = bracket_tax(max(0.0, gross - allowance), bands)
    ni = max(0, min(gross, 50_270) - 12_570) * .08 + max(0, gross - 50_270) * .02
    return _result([("Income tax", tax), ("National Insurance", ni)], gross)


# ---------- Germany ----------

def _german_tax(zve: float) -> float:
    zve = int(zve)
    if zve <= 12_096:
        return 0.0
    if zve <= 17_443:
        y = (zve - 12_096) / 10_000
        return (932.30 * y + 1_400) * y
    if zve <= 68_480:
        z = (zve - 17_443) / 10_000
        return (176.64 * z + 2_397) * z + 1_015.13
    if zve <= 277_825:
        return 0.42 * zve - 10_911.92
    return 0.45 * zve - 19_246.67


def germany(gross: float) -> dict:
    pension = min(gross, 96_600) * (.093 + .013)   # pension + unemployment
    health = min(gross, 66_150) * (.073 + .0125 + .018 + .006)  # health, avg add-on, care (childless)
    social = pension + health
    tax = _german_tax(max(0.0, gross - 1_230 - 36 - social))
    soli = 0.0
    if tax > 19_950:
        soli = min(.055 * tax, .119 * (tax - 19_950))
    return _result([("Income tax", tax), ("Solidarity surcharge", soli),
                    ("Pension + unemployment insurance", pension),
                    ("Health + care insurance", health)], gross)


# ---------- France ----------

FR_BRACKETS = [(11_497, 0), (29_315, .11), (83_823, .30), (180_294, .41), (INF, .45)]


def france(gross: float) -> dict:
    social = gross * .225  # approx. employee charges (pension, CSG/CRDS, unemployment, health)
    deductible_social = social - gross * .9825 * .029  # part of CSG/CRDS isn't deductible
    base = gross - deductible_social
    base -= min(max(base * .10, 495), 14_171)  # 10% flat work-expense deduction
    tax = bracket_tax(max(0.0, base), FR_BRACKETS)
    if tax < 1_929:  # décote for single filers
        tax = max(0.0, tax - (873 - .4525 * tax))
    return _result([("Income tax", tax), ("Social contributions (approx.)", social)], gross)


# ---------- China ----------

CN_BRACKETS = [(36_000, .03), (144_000, .10), (300_000, .20), (420_000, .25),
               (660_000, .30), (960_000, .35), (INF, .45)]


def china(gross: float) -> dict:
    base = min(gross, 36_000 * 12)  # contribution base is capped
    social = base * (.08 + .02 + .005)  # pension, medical, unemployment
    housing = base * .07  # housing fund; 5-12% depending on city
    tax = bracket_tax(max(0.0, gross - 60_000 - social - housing), CN_BRACKETS)
    return _result([("Individual income tax", tax), ("Pension, medical, unemployment", social),
                    ("Housing fund", housing)], gross)
