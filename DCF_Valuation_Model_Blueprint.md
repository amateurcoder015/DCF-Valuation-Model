# DCF (DISCOUNTED CASH FLOW) VALUATION MODEL
### Project Blueprint • Third Finance + Technology Project

**Core objective:** Build a Python-based tool that values a company using a standard single-stage Discounted Cash Flow model — pulling real historical financials, projecting free cash flow forward, discounting at a properly-calculated WACC, and comparing the resulting intrinsic share price to the company's actual market price.

---

## 1. Project Vision

This project is about learning to build a genuine *financial model*, not a calculator or a dashboard. A DCF is the standard valuation method taught at CFA Level 1/2 and used (in more elaborate form) in real equity research and banking. The goal here is to build the correct, standard version of it — cleanly separated into pieces that can each be hand-validated — before any temptation toward sensitivity tables, multi-stage growth, or scenario analysis (all reasonable, but later, extensions).

Keep this project **single-company, single-scenario, non-financial-sector companies only** (DCF doesn't suit banks/insurers well due to how their balance sheets work — this is a stated, deliberate exclusion, not an oversight).

---

## 2. Final System Flow

```
Company Ticker
      ↓
Historical Financials (revenue, EBIT, D&A, CapEx, ΔNWC, debt, cash, shares, beta)
      ↓
WACC Engine (Cost of Equity via CAPM + Cost of Debt, weighted)
      ↓
FCFF Projection Engine (growth & margin assumptions → 5-year forecast)
      ↓
Terminal Value (Gordon Growth Model)
      ↓
Discount Everything to Present Value
      ↓
Enterprise Value → Equity Value → Intrinsic Share Price
      ↓
Compare to Actual Market Price → Over/Undervalued Verdict
```

---

## 3. Scope — Build in Four Steps

| Step | What to build | Finish condition |
|---|---|---|
| **1 — Core Math** | WACC calculator (CAPM cost of equity, cost of debt, weights), FCFF formula, Gordon Growth terminal value formula, present-value discounting | Every formula validated against at least one hand-calculated textbook-style example |
| **2 — Data Layer** | Pull real historical financials for a given ticker (revenue, EBIT, D&A, CapEx, working capital, total debt, cash, beta, shares outstanding, current share price) via yfinance, normalized into a clean, consistent structure | Can pull and correctly parse real data for at least 2–3 real companies |
| **3 — DCF Orchestration Engine** | Combine Step 1 + Step 2: given a ticker and a small set of user-provided assumptions (revenue growth rate, terminal growth rate, projection years), run the full pipeline end-to-end and produce Enterprise Value, Equity Value, Intrinsic Share Price, and a verdict vs. the actual market price | Produces a sensible, explainable valuation for a real company, with every intermediate number inspectable |
| **4 — Minimal Dashboard** | Single-page Streamlit app: pick a ticker, adjust the handful of assumptions, see the full DCF output and a simple waterfall/bar chart (PV of cash flows + PV of terminal value = Enterprise Value) | User can value a real company without touching code |

No Step 5 unless explicitly decided later.

---

## 4. Finance Modules

**A. Free Cash Flow to Firm (FCFF)**
```
FCFF = EBIT × (1 − Tax Rate) + D&A − CapEx − ΔNet Working Capital
```
This is the cash flow available to ALL capital providers (both debt and equity holders) — which is why it gets discounted at WACC (the blended cost of both), not just the cost of equity.

**B. Cost of Equity (CAPM)**
```
Cost of Equity = Risk-Free Rate + Beta × Equity Risk Premium
```
- Risk-free rate: a long-term government bond yield (e.g. 10-year US Treasury or 10-year Indian G-Sec, depending on which market the company trades in — state this choice explicitly).
- Beta: pull from yfinance's company info, or compute it yourself via regression against a market index (a good stretch addition, not required for v1).
- Equity Risk Premium: a standard assumed value (commonly cited ranges are ~4–6% for developed markets, higher for emerging markets) — treat this as a documented, overridable assumption, not a fetched fact.

**C. Cost of Debt**
```
Cost of Debt (after-tax) = (Interest Expense / Total Debt) × (1 − Tax Rate)
```
A simplified but standard approximation — a more precise version would use the yield-to-maturity on the company's actual outstanding bonds, which is out of scope for a basic version.

**D. WACC**
```
WACC = (E / (E+D)) × Cost of Equity + (D / (E+D)) × Cost of Debt (after-tax)
```
where E = market value of equity (market cap) and D = total debt (book value is an acceptable simplification for a basic model).

**E. FCFF Projection**
Given a base-year FCFF and a growth rate assumption (either user-provided, or derived from the company's own historical revenue CAGR as a starting suggestion), project FCFF forward for a fixed number of years (5 is standard for a basic model).

**F. Terminal Value (Gordon Growth Model)**
```
Terminal Value (at end of projection period) = FCFF_final_year × (1 + g) / (WACC − g)
```
where `g` is a terminal (perpetual) growth rate — must be strictly less than WACC, and conventionally should not exceed a long-run GDP-growth-like rate (e.g. 2–4%). Validate this constraint explicitly; a terminal growth rate close to or above WACC produces a nonsensical (or infinite/negative) valuation, and the tool should catch this rather than silently producing garbage.

**G. Discounting & Valuation**
```
PV of each year's FCFF = FCFF_year / (1 + WACC)^year
PV of Terminal Value = Terminal Value / (1 + WACC)^final_year
Enterprise Value = Σ PV(FCFF) + PV(Terminal Value)
Equity Value = Enterprise Value − Total Debt + Cash & Equivalents
Intrinsic Share Price = Equity Value / Diluted Shares Outstanding
```

**H. Verdict**
Compare Intrinsic Share Price to the company's actual current market price:
```
Margin of Safety (%) = (Intrinsic Price − Market Price) / Market Price
```
Positive → the model suggests the stock is undervalued; negative → overvalued. State prominently, in the README and any output, that this is a MODEL OUTPUT based on the chosen assumptions, not investment advice — small changes in growth/WACC/terminal-growth assumptions can swing this conclusion significantly (this is a genuinely important, realistic limitation of DCF models, not a disclaimer to bury).

---

## 5. Data Plan

| Data | Use | Source |
|---|---|---|
| Revenue, EBIT, D&A, CapEx history | FCFF base-year calculation and growth-rate estimation | yfinance (`Ticker.financials`, `Ticker.cashflow`) |
| Working capital components | ΔNWC calculation | yfinance (`Ticker.balance_sheet`) |
| Total debt, cash & equivalents | WACC weights, Equity Value bridge | yfinance (`Ticker.balance_sheet`) |
| Beta, market cap, shares outstanding, current price | Cost of equity, WACC weights, per-share valuation, market comparison | yfinance (`Ticker.info`) |
| Risk-free rate | CAPM | A current long-term government bond yield — document whether this is fetched (e.g. via a bond ETF/yield ticker on yfinance) or manually entered as an assumption; either is acceptable for a basic model as long as it's stated clearly |
| Equity risk premium | CAPM | A stated, documented, overridable assumption — not fetched data (there is no clean "live" source for this) |

Restrict v1 to non-financial-sector companies (banks/insurers have fundamentally different cash flow and balance sheet structures that make a standard FCFF-based DCF inappropriate) — check the company's sector via `Ticker.info` and warn/refuse clearly if a financial-sector ticker is entered, rather than silently producing a misleading valuation.

---

## 6. Recommended Tech Stack

- Python — core language
- NumPy / Pandas — calculations and financial statement handling
- yfinance — company financials and market data
- Streamlit — single-page dashboard (Step 4 only)
- pytest — testing
- Git + GitHub — version control

No FastAPI, no React, no database for this project — the same lesson from the previous two projects applies: this doesn't need it.

---

## 7. Engineering Architecture

```
dcf-valuation-model/
├── src/
│   ├── wacc.py                # Module B/C/D: CAPM, cost of debt, WACC
│   ├── fcff.py                 # Module A/E: FCFF formula + projection
│   ├── terminal_value.py       # Module F: Gordon Growth terminal value
│   ├── discounting.py          # Module G: PV calculations, EV/Equity/price bridge
│   ├── data_fetch.py           # Module: yfinance financials pulling + normalization
│   └── dcf_engine.py           # Step 3: orchestrates all of the above end-to-end
├── dashboard/
│   └── app.py                   # Step 4: single-page Streamlit app
├── tests/
│   ├── test_wacc.py
│   ├── test_fcff.py
│   ├── test_terminal_value.py
│   ├── test_discounting.py
│   ├── test_data_fetch.py
│   └── test_dcf_engine.py
├── requirements.txt
└── README.md
```

---

## 8. Development Roadmap

- **Week 1** — Implement and hand-validate WACC (CAPM + cost of debt + weighting) against a textbook-style example.
- **Week 2** — Implement FCFF formula, projection logic, and the Gordon Growth terminal value formula (with the WACC > g constraint enforced); hand-validate against a manually worked example.
- **Week 3** — Implement the data layer (yfinance financials pulling/normalization) and the discounting/valuation bridge (EV → Equity Value → per-share price); wire into `dcf_engine.py` as a full end-to-end pipeline for one real company.
- **Week 4** — Build the single-page Streamlit dashboard: ticker input, editable assumptions (growth rate, terminal growth rate, ERP, projection years), full output table, and a simple waterfall/bar chart of value composition.

---

## 9. Validation & Quality Checklist

- Validate WACC against a hand-calculated example with known inputs.
- Validate FCFF calculation against a simple hand-built income-statement/cash-flow example.
- Validate the Gordon Growth terminal value formula against a hand-calculated case, and confirm it correctly rejects/flags `terminal growth rate >= WACC`.
- Validate the full discounting bridge (PV sum → EV → Equity Value → per-share price) against a fully hand-worked 5-year example before trusting it on real company data.
- Test edge cases: negative FCFF in the base year, a company with zero debt (WACC should reduce to cost of equity), a terminal growth rate assumption that's too aggressive.
- Confirm the financial-sector exclusion check actually triggers on a real bank/insurer ticker.
- Keep valuation math (`src/`) completely separate from dashboard/UI code (`dashboard/`).
- Record the data retrieval date for every company pulled — DCF outputs age quickly as market prices and financials update.

---

## 10. What NOT to Build Initially

Do not build: multi-stage growth models (e.g. high-growth-then-fade two- or three-stage DCFs), sensitivity/data-table analysis (WACC × growth-rate grids), scenario/Monte Carlo simulation on the assumptions, comparable-company (multiples-based) valuation, LBO modeling, a full three-statement model (that's a separate, later project), sum-of-the-parts valuation, or support for financial-sector companies. All of these are reasonable, well-known extensions — just not v1 scope. If pursued later, scope each as its own clearly-bounded step.

---

## 11. Final Demonstration

Best demo question:

**"Based on [Company]'s own historical financials, a realistically-estimated cost of capital, and a stated growth assumption, is the stock currently trading above or below what a standard DCF says it's worth — and by how much?"**

The application should return the full chain: FCFF projection, WACC, terminal value, Enterprise Value, Equity Value, intrinsic share price, and the margin of safety versus the actual market price — with every assumption used clearly visible, not hidden inside the calculation.

---

## 12. MASTER PROMPT FOR ANY LLM

*Copy the prompt below into any LLM whenever you want it to understand this project before asking for code, explanations, debugging, or design help. It assumes no prior context.*

```
You are helping me build a finance + technology project:

PROJECT NAME:
DCF (Discounted Cash Flow) Valuation Model

PROJECT GOAL:
Build a Python-based tool that values a single non-financial-sector
company using a standard single-stage Discounted Cash Flow model:
pull the company's real historical financials, project its Free Cash
Flow to Firm (FCFF) forward using a stated growth assumption, discount
those cash flows plus a Gordon Growth terminal value at a properly
calculated WACC, derive an intrinsic per-share value, and compare it
to the company's actual current market price.

TARGET USER:
A student studying engineering alongside CFA Level 1, building a
focused, correct, portfolio-worthy project. This project is
deliberately scoped to a BASIC, single-company, single-scenario DCF —
not a multi-stage model, not a sensitivity-table tool, not a full
three-statement model. Depth of correctness on the standard method
matters more than breadth of features.

CORE MODULES (in this order):
1. WACC engine — Cost of Equity via CAPM (risk-free rate + beta ×
   equity risk premium), after-tax Cost of Debt (interest expense /
   total debt, tax-adjusted), and weighted WACC using market value of
   equity and book value of debt.
2. FCFF engine — FCFF = EBIT × (1 - tax rate) + D&A - CapEx - ΔNWC,
   plus a simple forward projection over a fixed number of years (5 is
   standard) using a stated growth rate assumption.
3. Terminal Value — Gordon Growth Model:
   TV = FCFF_final_year × (1+g) / (WACC - g). Must validate that
   g < WACC and flag/reject otherwise, since violating this produces a
   nonsensical valuation.
4. Discounting & valuation bridge — discount each projected year's
   FCFF and the terminal value back to present value at WACC, sum to
   get Enterprise Value, subtract total debt and add cash to get
   Equity Value, divide by diluted shares outstanding to get intrinsic
   share price.
5. Data layer — pull real historical financials (revenue, EBIT, D&A,
   CapEx, working capital components, total debt, cash, beta, market
   cap, shares outstanding, current share price) via yfinance,
   normalized into a clean structure. Explicitly exclude/warn on
   financial-sector companies (banks, insurers), since a standard FCFF
   DCF is not appropriate for them.
6. Orchestration engine — combine modules 1-5 end-to-end for a given
   ticker and a small set of user-provided assumptions (growth rate,
   terminal growth rate, equity risk premium, projection years),
   producing the full valuation output plus a margin-of-safety
   comparison against the actual market price.
7. A SINGLE-PAGE Streamlit dashboard (only once modules 1-6 are built
   and tested) — ticker input, editable assumptions, full output
   table, and a simple chart showing value composition (PV of
   projected cash flows vs. PV of terminal value). No multi-page
   router, no backend/frontend split, no database.

CORE FORMULAS:
FCFF = EBIT × (1 - tax rate) + D&A - CapEx - ΔNWC
Cost of Equity = Risk-Free Rate + Beta × Equity Risk Premium
Cost of Debt (after-tax) = (Interest Expense / Total Debt) × (1 - tax rate)
WACC = (E/(E+D)) × Cost of Equity + (D/(E+D)) × Cost of Debt (after-tax)
Terminal Value = FCFF_final_year × (1+g) / (WACC - g), requires g < WACC
Enterprise Value = Σ [FCFF_year / (1+WACC)^year] + [Terminal Value / (1+WACC)^final_year]
Equity Value = Enterprise Value - Total Debt + Cash & Equivalents
Intrinsic Share Price = Equity Value / Diluted Shares Outstanding
Margin of Safety = (Intrinsic Price - Market Price) / Market Price

TECH STACK:
Python, NumPy, Pandas, yfinance (all financial/market data), Streamlit
(single-page dashboard only, built last), pytest. Deliberately
excluded: FastAPI, React, any database, multi-page dashboards, and any
scenario/sensitivity/Monte Carlo layer — these are reasonable future
extensions, not v1 scope.

BUILD PHILOSOPHY:
Build one module at a time in the order listed above. Hand-validate
WACC, FCFF, and the terminal value formula against manually worked
examples BEFORE connecting to real company data. Only build the
dashboard once the full valuation pipeline is tested and produces
sensible output for at least 2-3 real companies. Explicitly reject or
warn on financial-sector tickers rather than silently producing a
misleading valuation for them. Do not add multi-stage growth,
sensitivity tables, comps-based valuation, or a full three-statement
model unless explicitly asked later.

IMPORTANT ENGINEERING RULES:
- Keep valuation math (src/) completely separate from dashboard/UI code.
- State every assumption explicitly and make it visible/overridable in
  the output — never bury an assumption inside a hardcoded constant
  without surfacing it.
- Validate the g < WACC constraint on terminal value and fail clearly,
  not silently, if violated.
- Never invent financial data; always fetch real historicals and
  record the retrieval date, since DCF outputs age as prices/financials
  update.
- State clearly, wherever a valuation result is shown, that this is a
  model output based on the stated assumptions, not investment advice
  — DCF outputs are highly sensitive to small assumption changes.
- When giving code, explain where the file belongs in the project
  structure above.

FINAL SUCCESS CRITERION:
The finished tool should answer: "Based on [Company]'s own historical
financials and a stated set of growth/WACC assumptions, what is its
intrinsic per-share value via a standard DCF, and how does that
compare to its actual current market price?" — with every intermediate
number (FCFF projection, WACC, terminal value, Enterprise Value,
Equity Value) inspectable, not just the final price.

WHEN I ASK FOR HELP:
First identify which of the core modules the request affects. Then
explain the underlying finance concept and any assumptions, and only
then provide implementation guidance or code. Keep the project at this
deliberately basic, single-stage, single-company scope unless I
explicitly ask to extend it.
```

---

## 13. Future Extensions (Not v1 — Only If Explicitly Requested Later)

After the core 4-step build is stable and correct: two- or three-stage growth models (high growth fading to terminal growth), sensitivity/data-table analysis (WACC × terminal growth grids, or growth × margin grids), Monte Carlo simulation over the key assumptions, comparable-company (trading multiples) valuation as a cross-check, a full three-statement model feeding into the DCF instead of simplified historical inputs, and support for financial-sector-appropriate valuation methods (e.g. dividend discount models for banks). None of these are part of the initial build.
