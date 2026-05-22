import gradio as gr
import plotly.graph_objects as go

# ============================================================================
# OpenLine Readiness Simulator
# Phase 5C: Risk Heatmap as visual grid
# ============================================================================

COLORS = {
    "primary":      "#1a2b4a",
    "accent":       "#2c8a8a",
    "secondary":    "#d68910",
    "risk_high":    "#a94442",
    "risk_medium":  "#d68910",
    "risk_low":     "#1e7e34",
    "panel_bg":     "#f8f9fb",
    "text_primary": "#1a2b4a",
    "text_muted":   "#5a6478",
    "border":       "#dde2ec",
}

CUSTOM_CSS = f"""
.gradio-container {{
    max-width: 1100px !important;
    margin: 0 auto !important;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
}}
#header-banner {{
    background: linear-gradient(135deg, {COLORS['primary']} 0%, #2a4070 100%);
    color: white;
    padding: 32px 36px;
    border-radius: 8px;
    margin-bottom: 24px;
}}
#header-banner h1 {{
    color: white !important;
    font-size: 28px !important;
    font-weight: 600 !important;
    margin: 0 0 8px 0 !important;
}}
#header-banner p {{
    color: #c8d2e6 !important;
    font-size: 15px !important;
    margin: 0 !important;
    line-height: 1.5 !important;
}}
#headline-card {{
    background: white;
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    padding: 28px 36px;
    margin: 16px 0 24px 0;
    box-shadow: 0 1px 3px rgba(26, 43, 74, 0.06);
}}
.results-section {{
    background: white;
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    padding: 24px 32px;
    margin-bottom: 16px;
}}
.results-section h2 {{
    color: {COLORS['primary']} !important;
    font-size: 20px !important;
    font-weight: 600 !important;
    margin-top: 0 !important;
    padding-bottom: 12px !important;
    border-bottom: 2px solid {COLORS['accent']} !important;
}}
.results-section h3 {{
    color: {COLORS['primary']} !important;
    font-size: 16px !important;
    font-weight: 600 !important;
    margin-top: 20px !important;
}}
table {{
    width: 100% !important;
    border-collapse: collapse !important;
    margin: 12px 0 !important;
}}
th {{
    background: {COLORS['panel_bg']} !important;
    color: {COLORS['primary']} !important;
    font-weight: 600 !important;
    text-align: left !important;
    padding: 10px 14px !important;
    border-bottom: 2px solid {COLORS['border']} !important;
    font-size: 13px !important;
}}
td {{
    padding: 10px 14px !important;
    border-bottom: 1px solid {COLORS['border']} !important;
    font-size: 14px !important;
    color: {COLORS['text_primary']} !important;
    vertical-align: top !important;
}}
button.primary {{
    background: {COLORS['primary']} !important;
    border-color: {COLORS['primary']} !important;
}}
button.primary:hover {{
    background: #2a4070 !important;
}}
"""


WEIGHTS = {"process": 0.30, "organizational": 0.30, "regulatory": 0.25, "technical": 0.15}

SCORE_CURRENT_METHOD = {
    "Fully paper-based": 10, "Hybrid (some digital, some paper)": 40,
    "Partially digitized": 70, "Mostly digital": 95,
}
SCORE_CLEARANCE_DURATION = {
    "Under 30 minutes": 90, "30–60 minutes": 70, "1–2 hours": 45, "Over 2 hours": 20,
}
SCORE_DEVIATION_FREQUENCY = {"None": 100, "1–2": 75, "3–5": 45, "6 or more": 15}
SCORE_OPERATOR_FAMILIARITY = {"High": 90, "Medium": 60, "Low": 25}
SCORE_PRIOR_ATTEMPT = {
    "Yes — successful": 95, "No — first attempt": 60, "Yes — stalled or failed": 25,
}
SCORE_INSPECTION_OUTCOME = {
    "Clean (no observations)": 95, "Minor observations": 70,
    "Major observations": 25, "Not applicable / never inspected": 55,
}
SCORE_VALIDATION_MATURITY = {
    "Mature (templates, dedicated team)": 95, "Functional but ad-hoc": 55, "Underdeveloped": 20,
}
SCORE_MES_SYSTEM = {
    "SAP": 80, "Werum PAS-X": 90, "Rockwell": 75, "Tulip": 70,
    "Other / Custom": 40, "None": 25,
}
SCORE_EBR_SYSTEM = {"Yes": 90, "Partial": 55, "No": 25}
SCORE_EQUIPMENT_AGE = {
    "Mostly under 5 years": 90, "Mixed (some new, some old)": 60, "Mostly over 10 years": 30,
}

VERDICT_BANDS = [
    (80, 100, "Ready to scale",
     "Proceed with full rollout planning. Risks are manageable; ROI is defensible."),
    (65, 79, "Ready with caveats",
     "Address the flagged risks before committing to a full rollout. "
     "Most readiness gaps are closeable in 1–3 months."),
    (45, 64, "Not yet ready",
     "Significant gaps to close first. A premature rollout is likely to stall. "
     "Focus on the lowest-scoring sub-category before reassessing."),
    (0, 44, "High risk",
     "Recommend additional limited pilot scope rather than a full rollout. "
     "Foundational gaps in process, organization, or regulation need attention first."),
]

DEFAULT_LABOR_RATE_USD_PER_HOUR = 65
DEFAULT_TIME_SAVINGS_PCT = 45
DEFAULT_FIRST_LINE_COST_USD = 90_000
DEFAULT_ADDITIONAL_LINE_COST_USD = 55_000
NUM_OPERATORS_PER_CLEARANCE = 2
WEEKS_PER_YEAR = 48

DURATION_TO_HOURS = {
    "Under 30 minutes": 0.4, "30–60 minutes": 0.75, "1–2 hours": 1.5, "Over 2 hours": 2.5,
}


# ============================================================================
# RISK RULES
# ============================================================================

def risk_legacy_integration(mes_system, ebr_system, equipment_age, **_):
    if mes_system == "None" and ebr_system == "No":
        return "High", ("No MES and no eBR in place — OpenLine integration would require "
            "building both upstream systems first, adding 6–12 months before deployment.")
    if mes_system in ("None", "Other / Custom") or ebr_system == "No":
        return "Medium", (f"MES setup ({mes_system}) and eBR coverage ({ebr_system}) will "
            "require additional integration work — plan 2–4 months of IT effort.")
    if equipment_age == "Mostly over 10 years":
        return "Medium", ("Equipment is mostly over 10 years old; PLC and sensor "
            "compatibility checks will likely surface integration edge cases.")
    return "Low", (f"Modern MES ({mes_system}) and strong eBR coverage ({ebr_system}) "
        "make integration straightforward.")


def risk_validation_backlog(validation_maturity, num_lines, num_facilities, **_):
    if validation_maturity == "Underdeveloped":
        return "High", ("CSV maturity is underdeveloped — IQ/OQ/PQ authoring for "
            f"{num_lines} lines will become the rollout bottleneck.")
    if validation_maturity == "Functional but ad-hoc" and num_lines > 15:
        return "High", (f"Validation is ad-hoc, and rollout scope is {num_lines} "
            "lines. Documentation will slip behind deployment.")
    if validation_maturity == "Functional but ad-hoc":
        return "Medium", ("Validation is functional but ad-hoc — manageable at "
            "this scale, but build templates before further expansion.")
    if num_facilities > 1:
        return "Medium", ("Strong validation, but multi-site rollout requires "
            "harmonizing templates across sites — coordinate early.")
    return "Low", ("Mature validation function can absorb the rollout workload "
        "without becoming a bottleneck.")


def risk_operator_adoption(operator_familiarity, current_method, **_):
    if operator_familiarity == "Low" and current_method == "Fully paper-based":
        return "High", ("Operators have low digital familiarity and work fully "
            "on paper. Budget 2–3 months of training before go-live.")
    if operator_familiarity == "Low":
        return "High", ("Operator digital familiarity is low — adoption needs "
            "deliberate training, change agents, and visible leadership support.")
    if operator_familiarity == "Medium":
        return "Medium", ("Mixed operator familiarity — identify and train "
            "change-champion operators first to lead by example.")
    return "Low", ("High operator digital familiarity — adoption is unlikely "
        "to be a blocker. Standard training program should suffice.")


def risk_multi_site_coordination(num_facilities, num_lines, **_):
    if num_facilities == 1:
        return "Low", "Single-site rollout — no inter-site coordination overhead."
    if num_facilities <= 3:
        return "Medium", (f"{int(num_facilities)} facilities involved — "
            "establish central program management before kickoff.")
    return "High", (f"{int(num_facilities)} facilities — multi-site rollouts "
        "at this scale need PMO, harmonized templates, and sequenced go-live.")


def risk_sponsorship(prior_attempt, operator_familiarity, **_):
    if prior_attempt == "Yes — stalled or failed":
        return "High", ("Prior attempt stalled or failed — sponsorship is likely "
            "thin or fades under pressure. Re-engage sponsors with clear remit.")
    if prior_attempt == "No — first attempt" and operator_familiarity == "Low":
        return "Medium", ("First attempt with low operator familiarity — "
            "sponsorship will be tested under friction. Document commitment.")
    if prior_attempt == "Yes — successful":
        return "Low", ("Previous success implies established sponsorship and "
            "an organization that knows how to deliver these projects.")
    return "Medium", ("First-time attempt — sponsorship strength unproven. "
        "Secure explicit, named, written commitment before kickoff.")


def risk_change_control(validation_maturity, deviation_frequency, **_):
    if validation_maturity == "Underdeveloped" and deviation_frequency in ("3–5", "6 or more"):
        return "High", (f"QA absorbing {deviation_frequency} deviations/year "
            "against underdeveloped validation. New submissions will queue.")
    if deviation_frequency == "6 or more":
        return "High", ("Six or more deviations per year — quality system "
            "overloaded. New change-control will compete for QA bandwidth.")
    if validation_maturity == "Functional but ad-hoc" and deviation_frequency in ("3–5", "6 or more"):
        return "Medium", ("Ad-hoc validation + elevated deviations — QA "
            "bandwidth tight. Schedule change-control during quieter windows.")
    return "Low", ("Quality system has bandwidth to handle the change-control "
        "submission alongside business as usual.")


def risk_pilot_fatigue(prior_attempt, **_):
    if prior_attempt == "Yes — stalled or failed":
        return "High", ("Prior digitization attempt stalled or failed. Without "
            "clear post-mortem, organizational skepticism will undermine restart.")
    if prior_attempt == "No — first attempt":
        return "Low", ("First attempt — no historical baggage. Use clean slate "
            "to establish a track record.")
    return "Low", ("Previous successful attempt creates positive momentum and "
        "internal advocates.")


def risk_equipment_compatibility(equipment_age, mes_system, **_):
    if equipment_age == "Mostly over 10 years":
        return "High", ("Equipment mostly over 10 years old — expect PLC "
            "firmware mismatches and sensor compatibility issues.")
    if equipment_age == "Mixed (some new, some old)" and mes_system in ("None", "Other / Custom"):
        return "Medium", ("Mixed-age equipment + no standard MES — line-level "
            "data extraction will vary. Catalog by line before committing.")
    if equipment_age == "Mixed (some new, some old)":
        return "Medium", ("Mixed-age equipment — newer lines will go live "
            "faster; older lines may need targeted upgrades.")
    return "Low", ("Modern equipment fleet — sensor and PLC integration "
        "should be straightforward.")


RISK_RULES = [
    ("Legacy MES/ERP integration", risk_legacy_integration),
    ("Validation documentation backlog", risk_validation_backlog),
    ("Operator adoption & training", risk_operator_adoption),
    ("Multi-site coordination", risk_multi_site_coordination),
    ("Executive sponsorship fragility", risk_sponsorship),
    ("Change-control / QA bottleneck", risk_change_control),
    ("Past-failure / pilot fatigue", risk_pilot_fatigue),
    ("Equipment age & PLC compatibility", risk_equipment_compatibility),
]


# ============================================================================
# RECOMMENDATIONS
# ============================================================================

def rec_regulatory_observations(inspection_outcome, **_):
    if inspection_outcome == "Major observations":
        return (1, "**Resolve outstanding regulatory observations first.** Adding "
            "new validation scope while major observations are open creates regulatory "
            "exposure. Close CAPA actions before initiating OpenLine work.")
    return None


def rec_validation_capacity(validation_maturity, num_lines, **_):
    if validation_maturity == "Underdeveloped":
        return (1, f"**Build validation templates before scoping.** Validation maturity "
            f"is underdeveloped, targeting {num_lines} lines. Without reusable IQ/OQ/PQ "
            "templates, documentation will consume your QA team.")
    return None


def rec_prior_attempt_postmortem(prior_attempt, **_):
    if prior_attempt == "Yes — stalled or failed":
        return (2, "**Conduct a post-mortem on the previous attempt before restarting.** "
            "Identify what failed (sponsorship, tech, change management), document it, "
            "and explicitly state what's different this time.")
    return None


def rec_sponsorship(prior_attempt, operator_familiarity, **_):
    if prior_attempt == "Yes — stalled or failed":
        return (2, "**Re-engage executive sponsorship with a documented remit.** "
            "Sponsor commitment must be explicit, named, and documented — verbal "
            "endorsement won't survive the first friction.")
    if prior_attempt == "No — first attempt" and operator_familiarity == "Low":
        return (4, "**Confirm and document executive sponsorship before kickoff.** "
            "Get written commitment from a named executive with budget authority.")
    return None


def rec_ebr_first(ebr_system, mes_system, **_):
    if ebr_system == "No":
        return (3, "**Establish electronic batch record coverage before OpenLine.** "
            "Without eBR, OpenLine integration must build the batch-record interface "
            "from scratch, adding months and creating a single point of failure.")
    return None


def rec_mes_strategy(mes_system, **_):
    if mes_system == "None":
        return (3, "**Define an MES strategy before scoping OpenLine.** With no MES, "
            "OpenLine has nothing to receive batch context from. Choose whether to "
            "deploy a pharma-grade MES in parallel or scope OpenLine as standalone.")
    return None


def rec_qa_capacity(validation_maturity, deviation_frequency, **_):
    if validation_maturity == "Underdeveloped" and deviation_frequency in ("3–5", "6 or more"):
        return (1, f"**Address QA capacity before adding new change-control "
            f"submissions.** You have {deviation_frequency} deviations/year against "
            "underdeveloped validation. New submissions will queue behind existing CAPAs.")
    if deviation_frequency == "6 or more":
        return (4, "**Run a deviation-reduction sprint before adding scope.** Six or "
            "more deviations per year suggests the underlying process is unstable.")
    return None


def rec_operator_training(operator_familiarity, current_method, **_):
    if operator_familiarity == "Low" and current_method == "Fully paper-based":
        return (4, "**Build operator readiness before go-live.** Operators moving from "
            "fully paper-based to AI-assisted need structured training, change champions, "
            "and shadow-operation periods. Budget 2–3 months.")
    if operator_familiarity == "Low":
        return (4, "**Identify and train change-champion operators on each shift.** "
            "Low overall familiarity is overcome by visible peer adoption.")
    return None


def rec_equipment_audit(equipment_age, **_):
    if equipment_age == "Mostly over 10 years":
        return (3, "**Conduct a line-by-line equipment audit before scoping.** With "
            "equipment mostly over 10 years old, expect PLC firmware mismatches. "
            "Some lines may need upgrades before OpenLine can be deployed.")
    return None


def rec_multi_site_pmo(num_facilities, **_):
    if num_facilities >= 4:
        return (5, f"**Establish a dedicated PMO for the {int(num_facilities)}-site "
            "rollout.** Central program management, harmonized templates, and "
            "sequenced site-by-site go-live are non-negotiable at this scale.")
    if num_facilities in (2, 3):
        return (5, f"**Designate a central rollout lead across the "
            f"{int(num_facilities)} facilities.** Even at small multi-site scale, "
            "one accountable owner prevents divergence.")
    return None


def rec_pilot_scope(prior_attempt, num_lines, **_):
    if prior_attempt == "Yes — stalled or failed" and num_lines > 5:
        return (5, f"**Reduce initial scope from {num_lines} lines to 2–3 lines for "
            "the restart.** A focused restart with visible early wins rebuilds "
            "organizational confidence faster than a broad rollout.")
    return None


RECOMMENDATION_RULES = [
    rec_regulatory_observations, rec_validation_capacity, rec_prior_attempt_postmortem,
    rec_sponsorship, rec_ebr_first, rec_mes_strategy, rec_qa_capacity,
    rec_operator_training, rec_equipment_audit, rec_multi_site_pmo, rec_pilot_scope,
]


# ============================================================================
# ENGINES
# ============================================================================

def compute_readiness_score(
    current_method, clearance_duration, deviation_frequency,
    operator_familiarity, prior_attempt, inspection_outcome, validation_maturity,
    mes_system, ebr_system, equipment_age,
):
    process_score = (SCORE_CURRENT_METHOD[current_method]
        + SCORE_CLEARANCE_DURATION[clearance_duration]
        + SCORE_DEVIATION_FREQUENCY[deviation_frequency]) / 3
    org_score = (SCORE_OPERATOR_FAMILIARITY[operator_familiarity]
        + SCORE_PRIOR_ATTEMPT[prior_attempt]) / 2
    reg_score = (SCORE_INSPECTION_OUTCOME[inspection_outcome]
        + SCORE_VALIDATION_MATURITY[validation_maturity]) / 2
    tech_score = (SCORE_MES_SYSTEM[mes_system]
        + SCORE_EBR_SYSTEM[ebr_system]
        + SCORE_EQUIPMENT_AGE[equipment_age]) / 3
    total = (process_score * WEIGHTS["process"]
        + org_score * WEIGHTS["organizational"]
        + reg_score * WEIGHTS["regulatory"]
        + tech_score * WEIGHTS["technical"])

    verdict_label, verdict_message = "", ""
    for low, high, label, message in VERDICT_BANDS:
        if low <= total <= high:
            verdict_label, verdict_message = label, message
            break

    return {
        "total": round(total, 1),
        "process": round(process_score, 1),
        "organizational": round(org_score, 1),
        "regulatory": round(reg_score, 1),
        "technical": round(tech_score, 1),
        "verdict_label": verdict_label,
        "verdict_message": verdict_message,
    }


def compute_roi(
    num_lines, num_facilities, changeovers_per_week, clearance_duration,
    labor_rate, time_savings_pct, first_line_cost, additional_line_cost,
):
    hours_per_clearance = DURATION_TO_HOURS[clearance_duration]
    annual_clearance_events = num_lines * changeovers_per_week * WEEKS_PER_YEAR
    labor_hours_per_event = hours_per_clearance * NUM_OPERATORS_PER_CLEARANCE
    current_annual_cost = annual_clearance_events * labor_hours_per_event * labor_rate
    post_rollout_cost = current_annual_cost * (1 - time_savings_pct / 100)
    annual_savings = current_annual_cost - post_rollout_cost
    lines_per_facility = max(1, num_lines / num_facilities)
    deployment_cost = (num_facilities * first_line_cost
        + num_facilities * (lines_per_facility - 1) * additional_line_cost)
    payback_months = (deployment_cost / annual_savings) * 12 if annual_savings > 0 else None
    return {
        "annual_events": int(annual_clearance_events),
        "current_annual_cost": current_annual_cost,
        "post_rollout_cost": post_rollout_cost,
        "annual_savings": annual_savings,
        "deployment_cost": deployment_cost,
        "payback_months": payback_months,
    }


def compute_risk_heatmap(**inputs):
    return [(name, *rule_fn(**inputs)) for name, rule_fn in RISK_RULES]


def compute_recommendations(**inputs):
    candidates = []
    for rule_fn in RECOMMENDATION_RULES:
        result = rule_fn(**inputs)
        if result is not None:
            candidates.append(result)
    candidates.sort(key=lambda x: x[0])
    return [text for _, text in candidates[:7]]


# ============================================================================
# CHART BUILDERS
# ============================================================================

def get_score_color(score):
    if score >= 80: return COLORS["risk_low"]
    if score >= 65: return COLORS["accent"]
    if score >= 45: return COLORS["secondary"]
    return COLORS["risk_high"]


def build_readiness_gauge(score):
    color = get_score_color(score)
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        number={
            "font": {"size": 56, "color": COLORS["primary"], "family": "system-ui"},
            "suffix": "<span style='font-size:18px;color:#5a6478'> / 100</span>",
        },
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 1,
                "tickcolor": COLORS["text_muted"],
                "tickfont": {"size": 11, "color": COLORS["text_muted"]},
                "tickvals": [0, 25, 50, 75, 100]},
            "bar": {"color": color, "thickness": 0.6},
            "bgcolor": COLORS["panel_bg"], "borderwidth": 0,
            "steps": [
                {"range": [0, 44], "color": "#fbe9e9"},
                {"range": [44, 64], "color": "#fdf1de"},
                {"range": [64, 79], "color": "#dfeff0"},
                {"range": [79, 100], "color": "#e2f0e6"},
            ],
            "threshold": {"line": {"color": COLORS["primary"], "width": 3},
                "thickness": 0.85, "value": score},
        },
        domain={"x": [0, 1], "y": [0, 1]},
    ))
    fig.update_layout(height=260, margin=dict(l=20, r=20, t=20, b=20),
        paper_bgcolor="white",
        font={"family": "system-ui", "color": COLORS["text_primary"]})
    return fig


def build_subscore_ladder(process, organizational, regulatory, technical):
    categories = ["Process", "Organizational", "Regulatory", "Technical"]
    weights = ["30%", "30%", "25%", "15%"]
    scores = [process, organizational, regulatory, technical]
    labels = [f"{c}  ·  {w} weight" for c, w in zip(categories, weights)]
    colors = [get_score_color(s) for s in scores]

    fig = go.Figure()
    fig.add_trace(go.Bar(y=labels, x=[100]*4, orientation="h",
        marker={"color": COLORS["panel_bg"]},
        hoverinfo="skip", showlegend=False, width=0.5))
    fig.add_trace(go.Bar(y=labels, x=scores, orientation="h",
        marker={"color": colors},
        text=[f"<b>{s:.0f}</b>" for s in scores],
        textposition="outside",
        textfont={"size": 14, "color": COLORS["primary"]},
        hovertemplate="<b>%{y}</b><br>Score: %{x:.1f}/100<extra></extra>",
        showlegend=False, width=0.4))

    fig.update_layout(
        barmode="overlay", height=260,
        margin=dict(l=30, r=60, t=10, b=20),
        paper_bgcolor="white", plot_bgcolor="white",
        xaxis={"range": [0, 110], "showgrid": False, "zeroline": False,
            "tickvals": [0, 25, 50, 75, 100],
            "tickfont": {"size": 11, "color": COLORS["text_muted"]}},
        yaxis={"showgrid": False,
            "tickfont": {"size": 13, "color": COLORS["primary"]},
            "autorange": "reversed"},
        font={"family": "system-ui"})
    return fig


def build_roi_comparison(current_cost, post_cost, savings):
    categories = ["Current annual cost<br>(manual line clearance)",
                  "Projected annual cost<br>(after OpenLine rollout)"]
    values = [current_cost, post_cost]
    colors = [COLORS["text_muted"], COLORS["accent"]]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=categories, y=values, marker={"color": colors},
        text=[f"<b>${v/1000:,.0f}K</b>" for v in values],
        textposition="outside",
        textfont={"size": 15, "color": COLORS["primary"]},
        hovertemplate="%{x}<br>%{y:$,.0f}<extra></extra>",
        width=0.5, showlegend=False))
    fig.add_annotation(x=0.5, y=max(values) * 1.08, xref="paper",
        text=f"<b>${savings/1000:,.0f}K saved/year</b>",
        showarrow=False,
        font={"size": 14, "color": COLORS["accent"]},
        bgcolor="white", bordercolor=COLORS["accent"],
        borderwidth=1.5, borderpad=8)
    fig.add_annotation(x=1, y=post_cost, ax=0, ay=current_cost,
        xref="x", yref="y", axref="x", ayref="y",
        showarrow=True, arrowhead=2, arrowsize=1.2,
        arrowwidth=2, arrowcolor=COLORS["accent"])
    fig.update_layout(height=340, margin=dict(l=40, r=40, t=70, b=60),
        paper_bgcolor="white", plot_bgcolor="white",
        xaxis={"showgrid": False,
            "tickfont": {"size": 12, "color": COLORS["primary"]}},
        yaxis={"showgrid": True, "gridcolor": COLORS["border"],
            "zeroline": False, "tickformat": "$,.0s",
            "tickfont": {"size": 11, "color": COLORS["text_muted"]},
            "range": [0, max(values) * 1.25]},
        font={"family": "system-ui"})
    return fig


def build_payback_timeline(payback_months):
    display_value = min(payback_months, 60) if payback_months else 60
    capped = payback_months and payback_months > 60

    if payback_months is None:
        bar_color = COLORS["risk_high"]
        verdict = "No projected payback"
    elif payback_months <= 24:
        bar_color = COLORS["risk_low"]
        verdict = "Within typical pharma capital approval threshold"
    elif payback_months <= 36:
        bar_color = COLORS["accent"]
        verdict = "Above 24-month threshold — defensible with strategic case"
    else:
        bar_color = COLORS["secondary"]
        verdict = "Long payback — strategic case required"

    fig = go.Figure()
    fig.add_trace(go.Bar(y=["Payback"], x=[60], orientation="h",
        marker={"color": COLORS["panel_bg"]},
        hoverinfo="skip", showlegend=False, width=0.5))
    fig.add_trace(go.Bar(y=["Payback"], x=[display_value], orientation="h",
        marker={"color": bar_color},
        hovertemplate=f"<b>{payback_months:.1f} months</b><extra></extra>"
            if payback_months else "<extra></extra>",
        showlegend=False, width=0.4))
    fig.add_shape(type="line", x0=24, x1=24, y0=-0.5, y1=0.5,
        line=dict(color=COLORS["primary"], width=2, dash="dash"))
    fig.add_annotation(x=24, y=0.5,
        text="24-month pharma capital threshold",
        showarrow=False, yshift=18,
        font={"size": 11, "color": COLORS["primary"]})
    label_text = (f"<b>{payback_months:.1f} months{' (capped)' if capped else ''}</b>"
        if payback_months else "<b>N/A</b>")
    fig.add_annotation(x=min(display_value + 2, 58), y=0,
        text=label_text, showarrow=False, xanchor="left",
        font={"size": 14, "color": COLORS["primary"]})
    fig.add_annotation(x=30, y=-0.7, text=f"<i>{verdict}</i>",
        showarrow=False,
        font={"size": 11, "color": COLORS["text_muted"]})
    fig.update_layout(barmode="overlay", height=180,
        margin=dict(l=20, r=20, t=40, b=40),
        paper_bgcolor="white", plot_bgcolor="white",
        xaxis={"range": [0, 62], "showgrid": False, "zeroline": False,
            "tickvals": [0, 12, 24, 36, 48, 60],
            "ticktext": ["0", "12 mo", "24 mo", "36 mo", "48 mo", "60+ mo"],
            "tickfont": {"size": 11, "color": COLORS["text_muted"]}},
        yaxis={"showticklabels": False, "showgrid": False, "zeroline": False,
            "range": [-1.2, 1.0]},
        font={"family": "system-ui"})
    return fig


def build_risk_heatmap_grid(risks):
    """
    Render the 8 risks as a 2x4 grid of colored cards.
    Cards show: rating header, risk name, and a SHORT tagline.
    Full explanation appears below the grid in a styled table.
    """
    rating_color = {
        "High": COLORS["risk_high"],
        "Medium": COLORS["risk_medium"],
        "Low": COLORS["risk_low"],
    }
    rating_bg = {
        "High": "#f5e0e0",
        "Medium": "#fbeed3",
        "Low": "#dfe9e0",
    }

    rows, cols = 2, 4
    fig = go.Figure()

    for idx, (name, rating, explanation) in enumerate(risks):
        row = idx // cols
        col = idx % cols
        x0, x1 = col, col + 1
        y0, y1 = rows - row - 1, rows - row
        cx = (x0 + x1) / 2

        # Build a short tagline (first sentence, capped at 80 chars)
        tagline = _make_tagline(explanation)

        # Card background
        fig.add_shape(type="rect",
            x0=x0 + 0.05, x1=x1 - 0.05,
            y0=y0 + 0.05, y1=y1 - 0.05,
            fillcolor=rating_bg[rating],
            line=dict(color=rating_color[rating], width=2),
            layer="below")

        # Top color strip
        fig.add_shape(type="rect",
            x0=x0 + 0.05, x1=x1 - 0.05,
            y0=y1 - 0.18, y1=y1 - 0.05,
            fillcolor=rating_color[rating],
            line=dict(width=0), layer="below")

        # Rating text on strip
        fig.add_annotation(x=cx, y=y1 - 0.115,
            text=f"<b>{rating.upper()}</b>",
            showarrow=False,
            font=dict(size=12, color="white", family="system-ui"))

        # Risk name (wrapped on word boundaries, max 2 lines)
        wrapped_name = _wrap_text(name, max_chars=20, max_lines=2)
        fig.add_annotation(x=cx, y=y1 - 0.35,
            text=f"<b>{wrapped_name}</b>",
            showarrow=False,
            font=dict(size=12, color=COLORS["primary"], family="system-ui"),
            align="center")

        # Short tagline (max 3 lines)
        wrapped_tagline = _wrap_text(tagline, max_chars=24, max_lines=3)
        fig.add_annotation(x=cx, y=y0 + 0.32,
            text=wrapped_tagline,
            showarrow=False,
            font=dict(size=10, color=COLORS["text_muted"], family="system-ui"),
            align="center")

    fig.update_layout(height=520,
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor="white", plot_bgcolor="white",
        xaxis=dict(visible=False, range=[0, cols],
            showgrid=False, zeroline=False),
        yaxis=dict(visible=False, range=[0, rows],
            showgrid=False, zeroline=False),
        showlegend=False)
    return fig


def _make_tagline(explanation):
    """
    Distill a long explanation into a short tagline.
    Takes the first sentence; if still too long, truncates at a word boundary.
    """
    # First sentence
    for sep in [". ", " — ", " - ", ": "]:
        if sep in explanation:
            first = explanation.split(sep, 1)[0]
            if 10 < len(first) < 90:
                return first
    # Otherwise truncate to 75 chars at word boundary
    if len(explanation) <= 75:
        return explanation
    truncated = explanation[:75]
    last_space = truncated.rfind(" ")
    if last_space > 30:
        truncated = truncated[:last_space]
    return truncated + "…"


def _wrap_text(text, max_chars=24, max_lines=3):
    """
    Word-aware line wrap. Breaks on whitespace only — never mid-word.
    Caps the result at max_lines, appending '…' if truncated.
    """
    words = text.split()
    lines = []
    current = ""
    for word in words:
        # If a single word is longer than max_chars, force-break it
        if len(word) > max_chars:
            if current:
                lines.append(current)
                current = ""
            # break the long word into max_chars chunks
            while len(word) > max_chars:
                lines.append(word[:max_chars])
                word = word[max_chars:]
            current = word
            continue

        candidate = (current + " " + word).strip()
        if len(candidate) <= max_chars:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)

    if len(lines) > max_lines:
        lines = lines[:max_lines]
        last = lines[-1]
        if len(last) > max_chars - 1:
            last = last[:max_chars - 1].rstrip()
        lines[-1] = last + "…"

    return "<br>".join(lines)


# ============================================================================
# UI HANDLER
# ============================================================================

RATING_ICON = {
    "Low":    "🟢 Low",
    "Medium": "🟡 Medium",
    "High":   "🔴 High",
}

def _fmt_money(x):
    return f"${x:,.0f}"


def process_form(
    num_lines, num_facilities, annual_volume, product_type,
    current_method, clearance_duration, changeovers_per_week, deviation_frequency,
    mes_system, ebr_system, equipment_age,
    inspection_outcome, validation_maturity,
    operator_familiarity, prior_attempt,
    labor_rate, time_savings_pct, first_line_cost, additional_line_cost,
):
    score = compute_readiness_score(
        current_method, clearance_duration, deviation_frequency,
        operator_familiarity, prior_attempt,
        inspection_outcome, validation_maturity,
        mes_system, ebr_system, equipment_age,
    )

    roi = compute_roi(
        num_lines, num_facilities, changeovers_per_week, clearance_duration,
        labor_rate, time_savings_pct, first_line_cost, additional_line_cost,
    )

    common_inputs = dict(
        num_lines=num_lines, num_facilities=num_facilities,
        current_method=current_method, clearance_duration=clearance_duration,
        deviation_frequency=deviation_frequency,
        mes_system=mes_system, ebr_system=ebr_system, equipment_age=equipment_age,
        inspection_outcome=inspection_outcome, validation_maturity=validation_maturity,
        operator_familiarity=operator_familiarity, prior_attempt=prior_attempt,
    )

    risks = compute_risk_heatmap(**common_inputs)
    recommendations = compute_recommendations(**common_inputs)

    payback_text = (f"{roi['payback_months']:.1f} months"
        if roi["payback_months"] is not None else "N/A")

    # Charts
    gauge_fig = build_readiness_gauge(score["total"])
    ladder_fig = build_subscore_ladder(
        score["process"], score["organizational"],
        score["regulatory"], score["technical"])
    roi_compare_fig = build_roi_comparison(
        roi["current_annual_cost"], roi["post_rollout_cost"], roi["annual_savings"])
    payback_fig = build_payback_timeline(roi["payback_months"])
    risk_grid_fig = build_risk_heatmap_grid(risks)

    # Headline card
    headline_html = f"""
<div id="headline-card">
  <div style="display:flex;align-items:center;justify-content:space-between;gap:32px;flex-wrap:wrap;">
    <div>
      <div style="font-size:13px;color:{COLORS['text_muted']};text-transform:uppercase;letter-spacing:1.5px;font-weight:600;margin-bottom:6px;">
        Readiness Verdict
      </div>
      <div style="font-size:28px;font-weight:700;color:{COLORS['primary']};line-height:1.2;margin-bottom:4px;">
        {score['verdict_label']}
      </div>
      <div style="font-size:14px;color:{COLORS['text_muted']};max-width:560px;line-height:1.5;">
        {score['verdict_message']}
      </div>
    </div>
    <div style="text-align:right;border-left:1px solid {COLORS['border']};padding-left:32px;">
      <div style="font-size:12px;color:{COLORS['text_muted']};text-transform:uppercase;letter-spacing:1.5px;font-weight:600;margin-bottom:4px;">
        Projected Payback
      </div>
      <div style="font-size:28px;font-weight:700;color:{COLORS['accent']};line-height:1.1;">
        {payback_text}
      </div>
      <div style="font-size:12px;color:{COLORS['text_muted']};margin-top:6px;">
        Estimated annual savings: <b>{_fmt_money(roi['annual_savings'])}</b>
      </div>
    </div>
  </div>
</div>
"""

    high_count = sum(1 for _, r, _ in risks if r == "High")
    med_count = sum(1 for _, r, _ in risks if r == "Medium")
    low_count = sum(1 for _, r, _ in risks if r == "Low")

    if recommendations:
        rec_block = "\n\n".join(f"{i+1}. {text}" for i, text in enumerate(recommendations))
    else:
        rec_block = ("**No critical remediation needed.** Your readiness score and "
            "risk profile suggest you can proceed directly to rollout planning.")

    roi_notes_md = f"""
<div class="results-section">

### How the financial projection was calculated

- **Annual clearance events:** {num_lines} lines × {changeovers_per_week} changeovers/week × 48 production weeks/year = **{roi['annual_events']:,} events**
- **Labor hours per event:** {DURATION_TO_HOURS[clearance_duration]} hours × 2 operators (operator + QA witness, per GMP)
- **Labor rate used:** {_fmt_money(labor_rate)}/hour fully-loaded
- **Time savings applied:** {time_savings_pct}% (Catalyx publishes 85%; default conservatively halved)
- **Deployment cost:** {_fmt_money(first_line_cost)} per first line across {num_facilities} facilities, plus {_fmt_money(additional_line_cost)} per additional line
- **Total deployment cost:** **{_fmt_money(roi['deployment_cost'])}**

</div>
"""

    risk_summary_md = f"""
<div class="results-section">

### Risk Summary

🔴 **{high_count} High** · 🟡 **{med_count} Medium** · 🟢 **{low_count} Low**

*Each tile is determined by specific rules based on your inputs.
High-rated risks should be addressed before committing to a full rollout.*

</div>
"""

    # Full risk detail table (shown below the grid)
    risk_detail_rows = "\n".join(
        f"| {RATING_ICON[rating]} | **{name}** | {explanation} |"
        for name, rating, explanation in risks
    )

    risk_detail_md = f"""
<div class="results-section">

### Full risk rationale

| Rating | Risk | Why this rating |
|---|---|---|
{risk_detail_rows}

</div>
"""

    recommendations_md = f"""
<div class="results-section">

## Next-Steps Recommendation

Actions to take *before* committing to a full OpenLine rollout, ordered by priority:

{rec_block}

</div>
"""

    return (
        headline_html, gauge_fig, ladder_fig,
        roi_compare_fig, payback_fig, roi_notes_md,
        risk_summary_md, risk_grid_fig, risk_detail_md, recommendations_md,
    )


# ============================================================================
# UI
# ============================================================================

HEADER_HTML = f"""
<div id="header-banner">
  <h1>OpenLine Readiness Simulator</h1>
  <p>An assessment tool for pharma manufacturing leaders. Estimate readiness to roll out AI-powered line clearance — before committing budget. Built on Catalyx's own 2025 industry benchmark research, which found that only 11% of factories that piloted digital line clearance in 2023 had rolled it out by 2025.</p>
</div>
"""

with gr.Blocks(title="OpenLine Readiness Simulator", css=CUSTOM_CSS) as demo:
    gr.HTML(HEADER_HTML)

    gr.Markdown(
        "### Instructions  \n"
        "Answer the 15 questions below. Sensible defaults are pre-filled — "
        "adjust those that apply. Expand the *Advanced assumptions* section "
        "to override the financial inputs. Click **Submit** for your full assessment."
    )

    with gr.Accordion("Section 1: Factory Profile", open=True):
        num_lines = gr.Slider(label="Number of production lines in scope for rollout",
            minimum=1, maximum=100, value=10, step=1)
        num_facilities = gr.Slider(label="Number of facilities involved",
            minimum=1, maximum=20, value=2, step=1)
        annual_volume = gr.Radio(
            label="Approximate annual production volume",
            choices=["Under 1 million units", "1–10 million units",
                "10–100 million units", "Over 100 million units"],
            value="1–10 million units")
        product_type = gr.Radio(label="Primary product type",
            choices=["Oral solid dose", "Injectable", "Biologic", "Medical device", "Other"],
            value="Oral solid dose")

    with gr.Accordion("Section 2: Current Line Clearance Practice", open=True):
        current_method = gr.Radio(label="Current line clearance method",
            choices=list(SCORE_CURRENT_METHOD.keys()),
            value="Hybrid (some digital, some paper)")
        clearance_duration = gr.Radio(label="Average line clearance duration today",
            choices=list(SCORE_CLEARANCE_DURATION.keys()),
            value="1–2 hours")
        changeovers_per_week = gr.Slider(label="Average number of changeovers per line per week",
            minimum=1, maximum=30, value=5, step=1)
        deviation_frequency = gr.Radio(label="Line clearance deviations in the past 12 months",
            choices=list(SCORE_DEVIATION_FREQUENCY.keys()),
            value="3–5")

    with gr.Accordion("Section 3: IT and Integration Landscape", open=True):
        mes_system = gr.Radio(label="Existing Manufacturing Execution System (MES)",
            choices=list(SCORE_MES_SYSTEM.keys()), value="None")
        ebr_system = gr.Radio(label="Electronic batch record (eBR) system in place",
            choices=list(SCORE_EBR_SYSTEM.keys()), value="Partial")
        equipment_age = gr.Radio(label="Equipment and PLC age",
            choices=list(SCORE_EQUIPMENT_AGE.keys()),
            value="Mixed (some new, some old)")

    with gr.Accordion("Section 4: Regulatory and Quality Context", open=True):
        inspection_outcome = gr.Radio(label="Last regulatory inspection outcome",
            choices=list(SCORE_INSPECTION_OUTCOME.keys()),
            value="Minor observations")
        validation_maturity = gr.Radio(label="Computer system validation maturity",
            choices=list(SCORE_VALIDATION_MATURITY.keys()),
            value="Functional but ad-hoc")

    with gr.Accordion("Section 5: Workforce and Change-Management Context", open=True):
        operator_familiarity = gr.Radio(label="Operator digital tool familiarity",
            choices=list(SCORE_OPERATOR_FAMILIARITY.keys()),
            value="Medium")
        prior_attempt = gr.Radio(
            label="Has your facility ever attempted a line clearance digitization project before?",
            choices=list(SCORE_PRIOR_ATTEMPT.keys()),
            value="No — first attempt")

    with gr.Accordion("Advanced assumptions (optional — override defaults)", open=False):
        gr.Markdown("These defaults come from publicly available industry data. "
            "Adjust any of them to reflect your own assumptions.")
        labor_rate = gr.Slider(label="Fully-loaded operator labor rate (USD per hour)",
            minimum=20, maximum=150,
            value=DEFAULT_LABOR_RATE_USD_PER_HOUR, step=5)
        time_savings_pct = gr.Slider(label="Expected time savings from OpenLine (%)",
            minimum=10, maximum=85,
            value=DEFAULT_TIME_SAVINGS_PCT, step=5)
        first_line_cost = gr.Slider(label="First line deployment cost per facility (USD)",
            minimum=30_000, maximum=200_000,
            value=DEFAULT_FIRST_LINE_COST_USD, step=5_000)
        additional_line_cost = gr.Slider(label="Additional line deployment cost (same facility, USD)",
            minimum=20_000, maximum=150_000,
            value=DEFAULT_ADDITIONAL_LINE_COST_USD, step=5_000)

    submit_btn = gr.Button("Run Assessment", variant="primary", size="lg")

    headline_out = gr.HTML()
    with gr.Row():
        gauge_out = gr.Plot(label="Readiness Score")
        ladder_out = gr.Plot(label="Sub-score Breakdown")

    gr.Markdown("## Financial Projection (ROI)")
    with gr.Row():
        roi_compare_out = gr.Plot(label="Annual cost: before vs after")
        payback_out = gr.Plot(label="Payback period")
    roi_notes_out = gr.Markdown()

    gr.Markdown("## Risk Heatmap")
    risk_summary_out = gr.Markdown()
    risk_grid_out = gr.Plot(label="8-risk assessment grid")
    risk_detail_out = gr.Markdown()

    recommendations_out = gr.Markdown()

    submit_btn.click(
        fn=process_form,
        inputs=[
            num_lines, num_facilities, annual_volume, product_type,
            current_method, clearance_duration, changeovers_per_week, deviation_frequency,
            mes_system, ebr_system, equipment_age,
            inspection_outcome, validation_maturity,
            operator_familiarity, prior_attempt,
            labor_rate, time_savings_pct, first_line_cost, additional_line_cost,
        ],
        outputs=[
            headline_out, gauge_out, ladder_out,
            roi_compare_out, payback_out, roi_notes_out,
            risk_summary_out, risk_grid_out, risk_detail_out, recommendations_out,
        ],
    )


if __name__ == "__main__":
    demo.launch()