# Sev Finances

A local dashboard for personal finance. Right now it has a Canadian tax calculator.

## Run it

    ./run.sh

It opens at http://localhost:8501. Stop it with Ctrl+C.

## Tax calculator

Enter an annual salary and pick a province or territory. It shows federal tax,
provincial tax, CPP/QPP, EI, take-home pay (yearly, monthly, biweekly), average and
marginal rates, and compares take-home across all 13 provinces and territories.

## Compare countries tab

Converts your CAD salary at editable exchange rates (sidebar), applies each country's
income tax and social contributions, and compares take-home in CAD for the United States (New York and California),
England (which also covers Wales and Northern Ireland), Scotland, Germany, France and China, alongside your
Canadian province. Rules live in `countries.py`; the tab is `world_tab.py`.

Tax parameters (2025 tax year) live in `tax_data.py`; the math is in `calc.py`.
It's an estimate for a single employee with salary income only.
