"""
STEP 3 (Excel) - Build the Retention ROI Simulator workbook.

Run:  python build_excel_model.py      ->  creates Retention_ROI_Simulator.xlsx in this folder

The workbook is built with LIVE FORMULAS: change a yellow cell on 'Assumptions' and every number
on 'Summary' and 'Targeting' recalculates. After building, YOU add PivotTables on 'Data_All'
(see STEP_BY_STEP_GUIDE.md, Step 3) - that is the part that shows your Excel skills.
"""
from pathlib import Path
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.worksheet.table import Table, TableStyleInfo
from openpyxl.chart import BarChart, LineChart, Reference
from openpyxl.comments import Comment

HERE = Path(__file__).resolve().parent
df = pd.read_csv(HERE.parent / "data" / "clean" / "customer_scored.csv")

# ---------- styles ----------
F = "Arial"
f_norm, f_bold = Font(name=F, size=10), Font(name=F, size=10, bold=True)
f_input = Font(name=F, size=10, color="0000FF", bold=True)          # blue = typed-in input
f_link = Font(name=F, size=10, color="008000")                      # green = pulled from another sheet
f_head = Font(name=F, size=10, bold=True, color="FFFFFF")
f_title = Font(name=F, size=16, bold=True, color="1F3A5F")
fill_head = PatternFill("solid", fgColor="1F3A5F")
fill_input = PatternFill("solid", fgColor="FFFF00")                 # yellow = cell you may edit
fill_kpi = PatternFill("solid", fgColor="E8F0FA")
thin = Side(style="thin", color="BBBBBB")
box = Border(left=thin, right=thin, top=thin, bottom=thin)
RS, PCT, INT = '#,##0;(#,##0);"-"', "0.0%", "#,##0"

def style_header(ws, row, c1, c2):
    for c in range(c1, c2 + 1):
        cell = ws.cell(row=row, column=c); cell.font, cell.fill = f_head, fill_head
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

wb = Workbook()

# =====================================================================
# README
# =====================================================================
ws = wb.active; ws.title = "README"
ws["B2"], ws["B2"].font = "Bank Retention ROI Simulator", f_title
lines = [
    "PURPOSE: A retention team has a limited budget. Who should it spend on, and what is the payoff?",
    "",
    "HOW TO USE",
    "1) Go to 'Assumptions'. Edit ONLY the yellow cells (budget, cost per action, save rate per action).",
    "2) 'Summary' shows the campaign result for your budget and a table of results for other budgets.",
    "3) 'Targeting' ranks every flagged customer by return per rupee and marks who is selected (Selected = 1).",
    "4) 'Data_All' holds all 10,000 customers - build your PivotTables / slicers here (see the guide).",
    "",
    "COLOUR LEGEND:  Blue bold text on yellow = input you can change | Black = formula | Green = pulled from another sheet",
    "",
    "KEY LOGIC",
    "Expected value saved  = churn probability x save rate of the action x 3-year customer value",
    "Net benefit           = expected value saved - cost of the action",
    "Customers are ranked by net benefit per rupee spent (ROI); the campaign funds them top-down until the budget runs out.",
    "",
    "DATA NOTE: Synthetic dataset (10,000 customers) modelled on an Indian retail bank. Costs and save rates are ASSUMPTIONS, not facts.",
]
for i, t in enumerate(lines, start=4):
    ws.cell(row=i, column=2, value=t).font = f_bold if t in ("HOW TO USE", "KEY LOGIC") else f_norm
ws.column_dimensions["A"].width = 3; ws.column_dimensions["B"].width = 120
ws.sheet_view.showGridLines = False

# =====================================================================
# ASSUMPTIONS
# =====================================================================
wa = wb.create_sheet("Assumptions")
wa["B2"], wa["B2"].font = "Assumptions (edit the yellow cells)", f_title
wa["B4"], wa["B4"].font = "Campaign budget (Rs)", f_bold
wa["C4"] = 500000
wa["C4"].font, wa["C4"].fill, wa["C4"].number_format, wa["C4"].border = f_input, fill_input, RS, box
wa["D4"] = "Total money the retention team can spend this quarter"; wa["D4"].font = f_norm

heads = ["Recommended action", "Cost per customer (Rs)", "Save rate (%)", "Why this assumption"]
for j, h in enumerate(heads):
    wa.cell(row=7, column=2 + j, value=h)
style_header(wa, 7, 2, 5)
actions = [
    ("RM Personal Call", 1500, 0.35, "Relationship-manager time (~45 min) for Premium customers; personal contact works best"),
    ("Proactive Check-in", 600, 0.20, "Short call / WhatsApp check-in for Premium customers at medium risk"),
    ("Fee Waiver + Cashback Offer", 400, 0.25, "Cost of waived fees + 1 month cashback; targets 'hidden charges' complaints"),
    ("Targeted App Nudge", 50, 0.08, "In-app offer + push notification; low cost, low response"),
    ("Automated SMS / App Nudge", 10, 0.05, "Bulk SMS / push; almost free, very low response"),
]
for i, (a, cst, sv, why) in enumerate(actions, start=8):
    wa.cell(row=i, column=2, value=a).font = f_norm
    c = wa.cell(row=i, column=3, value=cst); c.number_format = RS
    s = wa.cell(row=i, column=4, value=sv); s.number_format = PCT
    for cell in (c, s): cell.font, cell.fill, cell.border = f_input, fill_input, box
    wa.cell(row=i, column=5, value=why).font = f_norm
wa["B14"], wa["B14"].font = "ALL cost and save-rate numbers are ASSUMPTIONS made for this project (no source). Replace them with real bank figures if you have them.", Font(name=F, size=9, italic=True)
wa["B15"], wa["B15"].font = "3-year value in the data = annual revenue x 2.487 (3 years discounted at 10%); revenue = 3% of balance + 3.5% of loan + Rs1,500 card + Rs300 per product.", Font(name=F, size=9, italic=True)
for col, w in zip("ABCDE", (3, 34, 24, 16, 90)): wa.column_dimensions[col].width = w
wa.sheet_view.showGridLines = False

# =====================================================================
# DATA_ALL  (values only - for your PivotTables)
# =====================================================================
wd = wb.create_sheet("Data_All")
cols = ["customer_id", "age", "gender", "city", "city_tier", "account_type", "tenure_years", "products_held",
        "uses_mobile_app", "churned_next_90d", "complaints", "unresolved_complaints", "txn_change_pct",
        "churn_probability", "est_annual_revenue", "value_3yr", "revenue_at_risk", "value_segment",
        "risk_band", "recommended_action", "risk_decile"]
for j, c in enumerate(cols, start=1):
    wd.cell(row=1, column=j, value=c)
style_header(wd, 1, 1, len(cols))
for i, row in enumerate(df[cols].itertuples(index=False), start=2):
    for j, v in enumerate(row, start=1):
        wd.cell(row=i, column=j, value=v.item() if hasattr(v, "item") else v).font = f_norm
tbl = Table(displayName="tblCustomers", ref=f"A1:{wd.cell(row=len(df) + 1, column=len(cols)).coordinate}")
tbl.tableStyleInfo = TableStyleInfo(name="TableStyleLight9", showRowStripes=True)
wd.add_table(tbl); wd.freeze_panes = "B2"
for j in range(1, len(cols) + 1): wd.column_dimensions[wd.cell(row=1, column=j).column_letter].width = 17

# =====================================================================
# TARGETING  (only customers with a real action; every number is a formula)
# =====================================================================
wt = wb.create_sheet("Targeting")
tdf = df[df["recommended_action"] != "Monitor Only"].sort_values("revenue_at_risk", ascending=False).reset_index(drop=True)
n = len(tdf); first, last = 2, n + 1
heads = ["customer_id", "city", "value_segment", "risk_band", "recommended_action", "churn_probability",
         "value_3yr (Rs)", "revenue_at_risk (Rs)", "cost_per_customer (Rs)", "save_rate", "expected_value_saved (Rs)",
         "expected_customers_saved", "net_benefit (Rs)", "roi (net / cost)", "rank_by_roi", "cumulative_cost (Rs)", "selected (1/0)"]
for j, h in enumerate(heads, start=1): wt.cell(row=1, column=j, value=h)
style_header(wt, 1, 1, len(heads)); wt.row_dimensions[1].height = 42
rng = lambda col: f"${col}${first}:${col}${last}"
for i, r in enumerate(tdf.itertuples(index=False), start=2):
    vals = [r.customer_id, r.city, r.value_segment, r.risk_band, r.recommended_action,
            float(r.churn_probability), float(r.value_3yr), float(r.revenue_at_risk)]
    for j, v in enumerate(vals, start=1): wt.cell(row=i, column=j, value=v).font = f_norm
    wt[f"F{i}"].number_format = "0.0%"; wt[f"G{i}"].number_format = RS; wt[f"H{i}"].number_format = RS
    wt[f"I{i}"] = f"=INDEX(Assumptions!$C$8:$C$12,MATCH(E{i},Assumptions!$B$8:$B$12,0))"
    wt[f"J{i}"] = f"=INDEX(Assumptions!$D$8:$D$12,MATCH(E{i},Assumptions!$B$8:$B$12,0))"
    wt[f"K{i}"] = f"=F{i}*J{i}*G{i}"
    wt[f"L{i}"] = f"=F{i}*J{i}"
    wt[f"M{i}"] = f"=K{i}-I{i}"
    wt[f"N{i}"] = f"=IF(I{i}=0,0,M{i}/I{i})"
    wt[f"O{i}"] = f"=RANK(N{i},{rng('N')},0)+COUNTIF($N${first}:N{i},N{i})-1"      # +COUNTIF breaks ties
    wt[f"P{i}"] = f"=SUMIFS({rng('I')},{rng('O')},\"<=\"&O{i})"
    wt[f"Q{i}"] = f"=IF(AND(M{i}>0,P{i}<=Assumptions!$C$4),1,0)"
    for col in "IJKLMNOPQ": wt[f"{col}{i}"].font = f_link if col in "IJ" else f_norm
    wt[f"I{i}"].number_format = RS; wt[f"J{i}"].number_format = PCT; wt[f"K{i}"].number_format = RS
    wt[f"L{i}"].number_format = "0.000"; wt[f"M{i}"].number_format = RS; wt[f"N{i}"].number_format = '0.0"x"'
    wt[f"O{i}"].number_format = INT; wt[f"P{i}"].number_format = RS
wt.freeze_panes = "B2"; wt.auto_filter.ref = f"A1:Q{last}"
for j, w in enumerate([12, 12, 14, 11, 28, 14, 14, 16, 16, 11, 18, 16, 15, 13, 12, 17, 12], start=1):
    wt.column_dimensions[wt.cell(row=1, column=j).column_letter].width = w
wt["I1"].comment = Comment("Looked up from the Assumptions sheet using the recommended action.", "Project")

# =====================================================================
# SUMMARY
# =====================================================================
wsu = wb.create_sheet("Summary")
wsu["B2"], wsu["B2"].font = "Campaign result for your budget", f_title
T = lambda col: f"Targeting!${col}${first}:${col}${last}"
kpis = [
    ("Budget (Rs)", "=Assumptions!C4", RS),
    ("Customers flagged for an action", f"=COUNTA({T('A')})", INT),
    ("Customers selected within budget", f"=SUM({T('Q')})", INT),
    ("Money actually spent (Rs)", f"=SUMIFS({T('I')},{T('Q')},1)", RS),
    ("Customers expected to be saved", f"=SUMIFS({T('L')},{T('Q')},1)", "0.0"),
    ("Expected 3-year value saved (Rs)", f"=SUMIFS({T('K')},{T('Q')},1)", RS),
    ("Net benefit (Rs)", "=C10-C8", RS),
    ("Return on spend (net benefit / spend)", "=IF(C8=0,0,C11/C8)", '0.0"x"'),
    ("Total 3-year value at risk, all customers (Rs)", "=SUM(Data_All!$Q$2:$Q$10001)", RS),
    ("Share of value at risk protected", "=IF(C13=0,0,C10/C13)", PCT),
]
for i, (lab, fm, nf) in enumerate(kpis, start=5):
    a = wsu.cell(row=i, column=2, value=lab); a.font, a.fill, a.border = f_bold, fill_kpi, box
    b = wsu.cell(row=i, column=3, value=fm); b.number_format, b.border, b.font = nf, box, (f_link if "Assumptions" in fm or "Data_All" in fm else f_norm)

# budget sensitivity table
wsu["B18"], wsu["B18"].font = "What if the budget were different?  (budgets in yellow cells are editable)", f_bold
hd = ["Budget (Rs)", "Customers targeted", "Spend (Rs)", "Value saved (Rs)", "Net benefit (Rs)", "Return on spend"]
for j, h in enumerate(hd): wsu.cell(row=19, column=2 + j, value=h)
style_header(wsu, 19, 2, 7)
for i, b in enumerate([100000, 200000, 300000, 400000, 500000, 750000, 1000000, 1250000], start=20):
    c = wsu.cell(row=i, column=2, value=b); c.font, c.fill, c.number_format, c.border = f_input, fill_input, RS, box
    wsu[f"C{i}"] = f"=COUNTIFS({T('P')},\"<=\"&B{i},{T('M')},\">0\")"
    wsu[f"D{i}"] = f"=SUMIFS({T('I')},{T('P')},\"<=\"&B{i},{T('M')},\">0\")"
    wsu[f"E{i}"] = f"=SUMIFS({T('K')},{T('P')},\"<=\"&B{i},{T('M')},\">0\")"
    wsu[f"F{i}"] = f"=E{i}-D{i}"
    wsu[f"G{i}"] = f"=IF(D{i}=0,0,F{i}/D{i})"
    for col, nf in zip("CDEFG", (INT, RS, RS, RS, '0.0"x"')):
        wsu[f"{col}{i}"].number_format, wsu[f"{col}{i}"].font, wsu[f"{col}{i}"].border = nf, f_norm, box

# results by action
wsu["B30"], wsu["B30"].font = "Selected customers by action (for the budget on Assumptions)", f_bold
hd = ["Action", "Customers selected", "Spend (Rs)", "Value saved (Rs)", "Net benefit (Rs)"]
for j, h in enumerate(hd): wsu.cell(row=31, column=2 + j, value=h)
style_header(wsu, 31, 2, 6)
for i, (a, *_rest) in enumerate(actions, start=32):
    wsu.cell(row=i, column=2, value=a).font = f_norm
    wsu[f"C{i}"] = f"=COUNTIFS({T('E')},B{i},{T('Q')},1)"
    wsu[f"D{i}"] = f"=SUMIFS({T('I')},{T('E')},B{i},{T('Q')},1)"
    wsu[f"E{i}"] = f"=SUMIFS({T('K')},{T('E')},B{i},{T('Q')},1)"
    wsu[f"F{i}"] = f"=E{i}-D{i}"
    for col, nf in zip("CDEF", (INT, RS, RS, RS)):
        wsu[f"{col}{i}"].number_format, wsu[f"{col}{i}"].font, wsu[f"{col}{i}"].border = nf, f_norm, box
wsu["B37"], wsu["B37"].font = "Total", f_bold
for col in "CDEF":
    wsu[f"{col}37"] = f"=SUM({col}32:{col}36)"; wsu[f"{col}37"].font = f_bold
    wsu[f"{col}37"].number_format = INT if col == "C" else RS

# chart: net benefit vs budget
ch = BarChart(); ch.type = "col"; ch.title = "Net benefit by campaign budget (Rs)"
ch.add_data(Reference(wsu, min_col=6, min_row=19, max_row=27), titles_from_data=True)
ch.set_categories(Reference(wsu, min_col=2, min_row=20, max_row=27))
ch.y_axis.title, ch.x_axis.title = "Net benefit (Rs)", "Budget (Rs)"
ch.roundedCorners = False; ch.legend = None
ch.title.overlay = False; ch.x_axis.title.overlay = False; ch.y_axis.title.overlay = False
ch.x_axis.delete = False; ch.y_axis.delete = False
ch.height, ch.width = 8.5, 17
wsu.add_chart(ch, "I4")
for col, w in zip("ABCDEFG", (3, 46, 20, 18, 20, 18, 16)): wsu.column_dimensions[col].width = w
wsu.sheet_view.showGridLines = False

order = ["README", "Summary", "Assumptions", "Targeting", "Data_All"]
wb._sheets = [wb[name] for name in order]
wb.active = 1
wb.save(HERE / "Retention_ROI_Simulator.xlsx")
print(f"Saved Retention_ROI_Simulator.xlsx  ({n:,} customers on the Targeting sheet)")
