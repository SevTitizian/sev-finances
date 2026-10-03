"""Income tax and payroll deduction math. Pure functions, no UI."""

from tax_data import FEDERAL, PAYROLL, PROVINCIAL, PROVINCES


def bracket_tax(income: float, brackets) -> float:
    tax, lower = 0.0, 0.0
    for upper, rate in brackets:
        if income > lower:
            tax += (min(income, upper) - lower) * rate
        lower = upper
    return tax


def federal_bpa(income: float) -> float:
    lo, hi = FEDERAL["bpa_phase"]
    if income <= lo:
        return FEDERAL["bpa_max"]
    if income >= hi:
        return FEDERAL["bpa_min"]
    drop = FEDERAL["bpa_max"] - FEDERAL["bpa_min"]
    return FEDERAL["bpa_max"] - drop * (income - lo) / (hi - lo)


def ontario_health_premium(income: float) -> float:
    steps = [(20_000, 0, 0, 0), (36_000, .06, 0, 20_000), (48_000, 0, 300, 0),
             (48_600, .06, 300, 48_000), (72_000, 0, 450, 0), (72_600, .25, 450, 72_000),
             (200_000, 0, 600, 0), (200_600, .25, 600, 200_000)]
    for upper, rate, base, start in steps:
        if income <= upper:
            return base + rate * (income - start)
    return 900.0


def payroll(income: float, province: str) -> dict:
    p = PAYROLL
    if province == "QC":
        pension, pension2, ei = p["qpp"], p["qpp2"], p["ei_qc"]
    else:
        pension, pension2, ei = p["cpp"], p["cpp2"], p["ei"]
    pen = max(0, min(income, pension["ympe"]) - pension["exemption"]) * pension["rate"]
    pen2 = max(0, min(income, pension2["yampe"]) - pension["ympe"]) * pension2["rate"]
    out = {
        "QPP" if province == "QC" else "CPP": pen,
        "QPP2" if province == "QC" else "CPP2": pen2,
        "EI": min(income, ei["max_insurable"]) * ei["rate"],
    }
    if province == "QC":
        out["QPIP"] = min(income, p["qpip"]["max_insurable"]) * p["qpip"]["rate"]
    return out


def calculate(salary: float, province: str) -> dict:
    """Full breakdown of what is withheld from an annual salary."""
    pay = payroll(salary, province)
    pen = pay["QPP" if province == "QC" else "CPP"]
    pen2 = pay["QPP2" if province == "QC" else "CPP2"]
    base_share = PAYROLL["qpp" if province == "QC" else "cpp"]["base_share"]
    ei_total = pay["EI"]
    # Base pension contributions earn a credit; the enhanced part and CPP2 are deductions.
    credit_pen, ded_pen = pen * base_share, pen * (1 - base_share) + pen2
    taxable = max(0.0, salary - ded_pen)

    prov = PROVINCIAL[province]
    fed_credits = (federal_bpa(taxable) + credit_pen + ei_total
                   + min(FEDERAL["canada_employment"], salary)) * FEDERAL["credit_rate"]
    fed = max(0.0, bracket_tax(taxable, FEDERAL["brackets"]) - fed_credits)
    if province == "QC":
        fed *= 1 - FEDERAL["quebec_abatement"]

    credit_rate = prov["brackets"][0][1]
    prov_credits = (prov["bpa"] + credit_pen + ei_total
                    + (pay.get("QPIP", 0))) * credit_rate
    prov_tax = max(0.0, bracket_tax(taxable, prov["brackets"]) - prov_credits)
    extras = {}
    if "surtax" in prov:
        (t1, r1), (t2, r2) = prov["surtax"]
        surtax = max(0, prov_tax - t1) * r1 + max(0, prov_tax - t2) * r2
        prov_tax += surtax
        extras["Ontario surtax (included in provincial)"] = surtax
        prov_tax += ontario_health_premium(taxable)

    total_payroll = sum(pay.values())
    total = fed + prov_tax + total_payroll
    return {
        "federal": fed, "provincial": prov_tax, "payroll": pay,
        "total_payroll": total_payroll, "total_tax": total,
        "net": salary - total, "taxable": taxable, "extras": extras,
        "avg_rate": total / salary if salary else 0.0,
    }


def marginal_rate(salary: float, province: str, step: float = 100.0) -> float:
    return (calculate(salary + step, province)["total_tax"]
            - calculate(salary, province)["total_tax"]) / step


def all_provinces(salary: float) -> list[dict]:
    rows = []
    for code, name in PROVINCES.items():
        r = calculate(salary, code)
        rows.append({"Province": name, "Code": code, "Income tax": r["federal"] + r["provincial"],
                     "CPP/QPP + EI": r["total_payroll"], "Total tax": r["total_tax"],
                     "Take-home": r["net"], "Average rate": r["avg_rate"],
                     "Marginal rate": marginal_rate(salary, code)})
    return sorted(rows, key=lambda x: -x["Take-home"])
