"""Sev Finances: Canadian income tax calculator.

Enter an annual salary and a province to see federal tax, provincial tax,
CPP/QPP and EI, and the take-home pay that is left.

Run with:  ./run.sh
"""

import pandas as pd
import plotly.express as px
import streamlit as st

from calc import all_provinces, calculate, marginal_rate
from countries import DEFAULT_FX
from tax_data import PROVINCES
from world_tab import render_world

st.set_page_config(page_title="Sev Finances", page_icon="💰", layout="wide")

COLORS = {"Take-home": "#2a78d6", "Federal tax": "#e34948", "Provincial tax": "#eda100",
          "CPP/QPP": "#7a5ad6", "EI": "#2a9d8f"}


def money(x: float) -> str:
    return f"${x:,.0f}"


st.title("Sev Finances")
st.caption("Tax calculator for employment income, 2025 tax year: every Canadian province, plus an international comparison.")

with st.sidebar:
    salary = st.number_input("Annual salary (CAD)", min_value=0, max_value=5_000_000,
                             value=85_000, step=1_000)
    province = st.selectbox("Province / territory", list(PROVINCES), index=list(PROVINCES).index("ON"),
                            format_func=lambda c: PROVINCES[c])
    st.caption("Assumes a single employee with no other income, deductions or credits "
               "(no RRSP, tuition, dependants, etc.).")
    with st.expander("Compare countries settings"):
        st.caption("Units of local currency per 1 CAD")
        fx = {cur: st.number_input(cur, value=rate, min_value=0.01, step=0.01, format="%.2f")
              for cur, rate in DEFAULT_FX.items()}
        nyc = st.checkbox("New York: include NYC resident tax")

def render_canada(salary: int, province: str) -> None:
    if salary == 0:
        st.info("Enter a salary to see the breakdown.")
        return

    r = calculate(salary, province)
    pen_label = "QPP" if province == "QC" else "CPP"
    pen = r["payroll"][pen_label]
    pen2 = r["payroll"][pen_label + "2"]
    ei = r["payroll"]["EI"] + r["payroll"].get("QPIP", 0)
    ei_label = "EI + QPIP" if province == "QC" else "EI"

    c = st.columns(4)
    c[0].metric("Take-home (year)", money(r["net"]))
    c[1].metric("Take-home (month)", money(r["net"] / 12))
    c[2].metric("Total tax & deductions", money(r["total_tax"]))
    c[3].metric("Average rate", f"{r['avg_rate']:.1%}",
                help=f"Marginal rate on your next dollar: {marginal_rate(salary, province):.1%}")
    st.caption(f"Marginal rate on your next dollar: **{marginal_rate(salary, province):.1%}**")

    left, right = st.columns([3, 2])

    with left:
        st.subheader(f"Where your {money(salary)} goes in {PROVINCES[province]}")
        rows = [
            ("Federal income tax", r["federal"]),
            (f"{PROVINCES[province]} income tax" + (" (incl. surtax & health premium)" if province == "ON" else ""),
             r["provincial"]),
            (f"{pen_label}", pen),
            (f"{pen_label}2 (second tier)", pen2),
            (ei_label, ei),
        ]
        df = pd.DataFrame(rows, columns=["Item", "Annual"])
        df["Monthly"] = df["Annual"] / 12
        df["Biweekly"] = df["Annual"] / 26
        df["% of salary"] = df["Annual"] / salary
        total = pd.DataFrame([["Total deductions", r["total_tax"], r["total_tax"] / 12,
                               r["total_tax"] / 26, r["total_tax"] / salary],
                              ["Take-home pay", r["net"], r["net"] / 12, r["net"] / 26, r["net"] / salary]],
                             columns=df.columns)
        st.dataframe(
            pd.concat([df, total]), hide_index=True, width='stretch',
            column_config={
                "Annual": st.column_config.NumberColumn(format="$%,.0f"),
                "Monthly": st.column_config.NumberColumn(format="$%,.0f"),
                "Biweekly": st.column_config.NumberColumn(format="$%,.0f"),
                "% of salary": st.column_config.NumberColumn(format="percent"),
            },
        )

    with right:
        pie = pd.DataFrame({
            "Part": ["Take-home", "Federal tax", "Provincial tax", "CPP/QPP", "EI"],
            "Amount": [r["net"], r["federal"], r["provincial"], pen + pen2, ei],
        })
        fig = px.pie(pie, names="Part", values="Amount", hole=.55, color="Part",
                     color_discrete_map=COLORS)
        fig.update_traces(textinfo="percent", sort=False)
        fig.update_layout(margin=dict(t=10, b=10, l=10, r=10), legend=dict(orientation="h", y=-.1))
        st.plotly_chart(fig, width='stretch')

    st.subheader("Compare every province at this salary")
    cmp = pd.DataFrame(all_provinces(salary))
    bar = px.bar(cmp, x="Code", y="Take-home", color_discrete_sequence=["#2a78d6"],
                 hover_data=["Province", "Total tax"])
    bar.update_traces(marker_color=["#e34948" if c == province else "#2a78d6" for c in cmp["Code"]])
    bar.update_layout(margin=dict(t=10, b=10), yaxis_tickprefix="$", xaxis_title=None, yaxis_title=None)
    st.plotly_chart(bar, width='stretch')
    st.dataframe(
        cmp.drop(columns="Code"), hide_index=True, width='stretch',
        column_config={
            **{k: st.column_config.NumberColumn(format="$%,.0f")
               for k in ["Income tax", "CPP/QPP + EI", "Total tax", "Take-home"]},
            "Average rate": st.column_config.NumberColumn(format="percent"),
            "Marginal rate": st.column_config.NumberColumn(format="percent"),
        },
    )

    with st.expander("What's included and what isn't"):
        st.markdown("""
    - Federal and provincial/territorial brackets, basic personal amounts, Canada employment amount,
      and CPP/QPP and EI credits.
    - Ontario surtax and Ontario Health Premium. Quebec's federal abatement, QPP, QPIP and Quebec EI rate.
    - **Not included:** small provincial credits and reductions (e.g. Ontario's low-income reduction),
      employer-side contributions, RRSP/FHSA deductions, benefits, and non-employment income.
    - Rates are for the 2025 tax year; edit `tax_data.py` to update them. Treat results as an estimate,
      and check against the CRA's official figures before relying on them.
    """)


tab_ca, tab_world = st.tabs(["Canada by province", "Compare countries"])
with tab_ca:
    render_canada(salary, province)
with tab_world:
    render_world(salary, province, fx, nyc)
