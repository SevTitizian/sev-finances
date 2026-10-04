"""The "Compare countries" tab: take-home pay for the same salary abroad."""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import countries as ct
from calc import calculate
from tax_data import PROVINCES

# name -> (currency, calculator taking gross in local currency)
def _places(nyc: bool) -> dict:
    places = {
        "United States (New York)": ("USD", lambda g: ct.united_states(g, "New York", nyc)),
        "United States (California)": ("USD", lambda g: ct.united_states(g, "California")),
        "Germany": ("EUR", ct.germany),
        "France": ("EUR", ct.france),
        "China": ("CNY", ct.china),
    }
    for region in ct.UK_REGIONS:
        places[region + " (UK)"] = ("GBP", lambda g, r=region: ct.united_kingdom(g, r))
    return places


def money(x: float, sym: str = "$") -> str:
    return f"{sym}{x:,.0f}"


# One colour per line. England, Wales and Northern Ireland have identical tax, so their
# lines overlap; Wales and Northern Ireland are dashed so all three stay visible.
COLORS = ["#e34948", "#2a78d6", "#eda100", "#2a9d8f", "#7a5ad6", "#d6459b", "#8a5a2b", "#444444",
          "#7fb800", "#00a6d6"]
MAX_INCOME = 800_000
DASHES = {"Wales (UK)": "dash", "Northern Ireland (UK)": "dot"}


def income_curves(province: str, fx: dict, nyc: bool, max_income: int, salary: int) -> go.Figure:
    """Take-home (CAD) against gross income (CAD) for every country."""
    incomes = sorted({*range(0, max_income + 1, 5_000), salary})
    series = {f"Canada ({PROVINCES[province]})": [calculate(i, province)["net"] for i in incomes]}
    for name, (cur, fn) in _places(nyc).items():
        series[name] = [fn(i * fx[cur])["net"] / fx[cur] for i in incomes]
    fig = go.Figure()
    for n, (name, ys) in enumerate(series.items()):
        fig.add_trace(go.Scatter(x=incomes, y=ys, name=name, mode="lines",
                                 line=dict(color=COLORS[n % len(COLORS)], width=3 if n == 0 else 2,
                                           dash=DASHES.get(name, "solid"))))
        if salary <= max_income:
            fig.add_trace(go.Scatter(x=[salary], y=[ys[incomes.index(salary)]], mode="markers",
                                     marker=dict(color=COLORS[n % len(COLORS)], size=9, line=dict(color="white", width=1)),
                                     showlegend=False, hoverinfo="skip"))
    fig.update_layout(margin=dict(t=10, b=10), hovermode="x unified", legend_title_text="",
                      xaxis=dict(title="Gross income (CAD)", tickprefix="$"),
                      yaxis=dict(title="Take-home pay (CAD)", tickprefix="$"))
    return fig


def render_world(salary: int, province: str, fx: dict, nyc: bool) -> None:
    if salary == 0:
        st.info("Enter a salary to compare countries.")
        return
    st.subheader("Same salary, different country")
    st.caption(f"Your {money(salary)} CAD salary is converted at the exchange rates in the sidebar, "
               "then taxed under each country's rules. Take-home is converted back to CAD. "
               "This compares nominal pay, not cost of living.")

    ca = calculate(salary, province)
    rows = [{"Country": f"Canada ({PROVINCES[province]})", "Currency": "CAD", "Gross (local)": salary,
             "Total tax": ca["total_tax"], "Take-home (local)": ca["net"], "Take-home (CAD)": ca["net"],
             "Effective rate": ca["avg_rate"], "items": [("Federal income tax", ca["federal"]),
             ("Provincial income tax", ca["provincial"]), ("CPP/QPP", sum(v for k, v in ca["payroll"].items() if "PP" in k)),
             ("EI/QPIP", sum(v for k, v in ca["payroll"].items() if "PP" not in k))]}]
    for name, (cur, fn) in _places(nyc).items():
        gross = salary * fx[cur]
        r = fn(gross)
        tax = gross - r["net"]
        rows.append({"Country": name, "Currency": cur, "Gross (local)": gross, "Total tax": tax / fx[cur],
                     "Take-home (local)": r["net"], "Take-home (CAD)": r["net"] / fx[cur],
                     "Effective rate": tax / gross, "items": r["items"], "fx": fx[cur]})
    df = pd.DataFrame(rows).sort_values("Take-home (CAD)", ascending=False)

    best, worst = df.iloc[0], df.iloc[-1]
    c = st.columns(3)
    c[0].metric("Highest take-home", best["Country"], money(best["Take-home (CAD)"]) + " CAD")
    c[1].metric("Lowest take-home", worst["Country"], money(worst["Take-home (CAD)"]) + " CAD")
    c[2].metric("Spread", money(best["Take-home (CAD)"] - worst["Take-home (CAD)"]) + " CAD")

    fig = px.bar(df, x="Country", y="Take-home (CAD)", hover_data=["Effective rate"])
    fig.update_traces(marker_color=["#e34948" if c.startswith("Canada") else "#2a78d6" for c in df["Country"]])
    fig.update_layout(margin=dict(t=10, b=10), yaxis_tickprefix="$", xaxis_title=None, yaxis_title="Take-home (CAD)")
    st.plotly_chart(fig, width="stretch")

    st.dataframe(
        df[["Country", "Currency", "Gross (local)", "Take-home (local)", "Take-home (CAD)", "Total tax", "Effective rate"]]
        .rename(columns={"Total tax": "Total tax (CAD)"}),
        hide_index=True, width="stretch",
        column_config={
            **{k: st.column_config.NumberColumn(format="%,.0f")
               for k in ["Gross (local)", "Take-home (local)"]},
            "Take-home (CAD)": st.column_config.NumberColumn(format="$%,.0f"),
            "Total tax (CAD)": st.column_config.NumberColumn(format="$%,.0f"),
            "Effective rate": st.column_config.NumberColumn(format="percent"),
        },
    )

    st.subheader("Take-home pay across incomes")
    st.plotly_chart(income_curves(province, fx, nyc, MAX_INCOME, salary), width="stretch")
    st.caption("Each line is one country. Dots mark your current salary. England, Wales and Northern Ireland "
               "tax the same, so their lines sit on top of each other.")

    st.subheader("Breakdown for one country")
    pick = st.selectbox("Country", df["Country"].tolist(), key="world_pick")
    row = df[df["Country"] == pick].iloc[0]
    f = row.get("fx", 1.0)
    items = pd.DataFrame(row["items"], columns=["Item", "Local currency"])
    items["CAD"] = items["Local currency"] / (f if pd.notna(f) else 1.0)
    items["% of gross"] = items["Local currency"] / row["Gross (local)"]
    st.dataframe(items, hide_index=True, width="stretch", column_config={
        "Local currency": st.column_config.NumberColumn(format=f"%,.0f {row['Currency']}"),
        "CAD": st.column_config.NumberColumn(format="$%,.0f"),
        "% of gross": st.column_config.NumberColumn(format="percent"),
    })

    with st.expander("Assumptions"):
        st.markdown("""
- Single employee, salary income only, standard deductions, no dependants or other credits.
- **US:** federal brackets and standard deduction, Social Security, Medicare, and each state's income tax and payroll disability insurance (California SDI; New York SDI/PFL). New York City resident tax is optional in the sidebar.
- **UK:** 2025/26 rates. England, Wales and Northern Ireland share rates; Scotland has its own bands. National Insurance is the same for all four.
- **Germany:** tax class I, no church tax, average health-insurance add-on, childless care insurance rate.
- **France:** one tax share, employee charges approximated at 22.5% of gross.
- **China:** social insurance and housing fund at roughly Shanghai-style rates (housing fund 7%), 60,000 CNY annual threshold, no special deductions.
- Exchange rates are rough defaults. Update them in the sidebar; results are estimates only.
""")
