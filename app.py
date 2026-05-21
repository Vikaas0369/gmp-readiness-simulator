import gradio as gr

# ============================================================================
# OpenLine Readiness Simulator
# Phase 4D: Readiness Score + ROI + Risk Heatmap + Next-Steps Recommendations
# ============================================================================
#
# Every assumption is sourced and visible at the top of this file. Readiness
# weightings follow mainstream pharma operations literature; ROI assumptions
# use conservative midpoints of publicly available industry ranges; risk
# rules and recommendations are based on standard pharma project remediation
# sequences and Catalyx's own 2025 Line Clearance Benchmark Report.
#
# ============================================================================


# ============================================================================
# READINESS SCORING TABLES (unchanged)
# ============================================================================

WEIGHTS = {
    "process":        0.30,
    "organizational": 0.30,
    "regulatory":     0.25,
    "technical":      0.15,
}

SCORE_CURRENT_METHOD = {
    "Fully paper-based":                 10,
    "Hybrid (some digital, some paper)": 40,
    "Partially digitized":               70,
    "Mostly digital":                    95,
}

SCORE_CLEARANCE_DURATION = {
    "Under 30 minutes":  90,
    "30–60 minutes":     70,
    "1–2 hours":         45,
    "Over 2 hours":      20,
}

SCORE_DEVIATION_FREQUENCY = {
    "None":      100,
    "1–2":        75,
    "3–5":        45,
    "6 or more":  15,
}

SCORE_OPERATOR_FAMILIARITY = {
    "High":   90,
    "Medium": 60,
    "Low":    25,
}

SCORE_PRIOR_ATTEMPT = {
    "Yes — successful":        95,
    "No — first attempt":      60,
    "Yes — stalled or failed": 25,
}

SCORE_INSPECTION_OUTCOME = {
    "Clean (no observations)":          95,
    "Minor observations":               70,
    "Major observations":               25,
    "Not applicable / never inspected": 55,
}

SCORE_VALIDATION_MATURITY = {
    "Mature (templates, dedicated team)": 95,
    "Functional but ad-hoc":              55,
    "Underdeveloped":                     20,
}

SCORE_MES_SYSTEM = {
    "SAP":            80,
    "Werum PAS-X":    90,
    "Rockwell":       75,
    "Tulip":          70,
    "Other / Custom": 40,
    "None":           25,
}

SCORE_EBR_SYSTEM = {
    "Yes":     90,
    "Partial": 55,
    "No":      25,
}

SCORE_EQUIPMENT_AGE = {
    "Mostly under 5 years":       90,
    "Mixed (some new, some old)": 60,
    "Mostly over 10 years":       30,
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


# ============================================================================
# ROI ASSUMPTIONS (unchanged)
# ============================================================================

DEFAULT_LABOR_RATE_USD_PER_HOUR = 65
DEFAULT_TIME_SAVINGS_PCT = 45
DEFAULT_FIRST_LINE_COST_USD = 90_000
DEFAULT_ADDITIONAL_LINE_COST_USD = 55_000
NUM_OPERATORS_PER_CLEARANCE = 2
WEEKS_PER_YEAR = 48

DURATION_TO_HOURS = {
    "Under 30 minutes": 0.4,
    "30–60 minutes":    0.75,
    "1–2 hours":        1.5,
    "Over 2 hours":     2.5,
}


# ============================================================================
# RISK HEATMAP RULES (unchanged)
# ============================================================================

def risk_legacy_integration(mes_system, ebr_system, equipment_age, **_):
    if mes_system == "None" and ebr_system == "No":
        return "High", (
            "No MES and no eBR in place — OpenLine integration would require "
            "building both upstream systems first, adding 6–12 months and "
            "significant cost before the deployment can begin."
        )
    if mes_system in ("None", "Other / Custom") or ebr_system == "No":
        return "Medium", (
            f"MES setup ({mes_system}) and eBR coverage ({ebr_system}) will "
            "require additional integration work — plan 2–4 months of IT effort."
        )
    if equipment_age == "Mostly over 10 years":
        return "Medium", (
            "Equipment is mostly over 10 years old; PLC and sensor compatibility "
            "checks will likely surface integration edge cases."
        )
    return "Low", (
        f"Modern MES ({mes_system}) and strong eBR coverage ({ebr_system}) "
        "make integration straightforward."
    )


def risk_validation_backlog(validation_maturity, num_lines, num_facilities, **_):
    total_lines = num_lines
    multi_site = num_facilities > 1

    if validation_maturity == "Underdeveloped":
        return "High", (
            "Computer system validation maturity is underdeveloped — IQ/OQ/PQ "
            f"authoring for {total_lines} lines will become the rollout "
            "bottleneck. Recommend building validation templates first."
        )
    if validation_maturity == "Functional but ad-hoc" and total_lines > 15:
        return "High", (
            f"Validation is functional but ad-hoc, and rollout scope is "
            f"{total_lines} lines. Ad-hoc validation does not scale; expect "
            "documentation to slip behind deployment by 2–3 lines."
        )
    if validation_maturity == "Functional but ad-hoc":
        return "Medium", (
            "Validation is functional but ad-hoc — manageable at this scale, "
            "but build templates before further expansion."
        )
    if multi_site:
        return "Medium", (
            "Validation maturity is strong, but multi-site rollout requires "
            "harmonizing templates across sites — coordinate early."
        )
    return "Low", (
        "Mature validation function with templates can absorb the rollout "
        "workload without becoming a bottleneck."
    )


def risk_operator_adoption(operator_familiarity, current_method, **_):
    if operator_familiarity == "Low" and current_method == "Fully paper-based":
        return "High", (
            "Operators have low digital tool familiarity and currently work "
            "fully on paper. Expect significant resistance; budget 2–3 months "
            "of training and shadow operation before go-live."
        )
    if operator_familiarity == "Low":
        return "High", (
            "Operator digital tool familiarity is low — adoption will require "
            "deliberate training, change agents on each shift, and visible "
            "leadership support."
        )
    if operator_familiarity == "Medium":
        return "Medium", (
            "Mixed operator familiarity — identify and train change-champion "
            "operators first to lead by example."
        )
    return "Low", (
        "High operator digital familiarity — adoption is unlikely to be a "
        "blocker. Standard training program should suffice."
    )


def risk_multi_site_coordination(num_facilities, num_lines, **_):
    if num_facilities == 1:
        return "Low", "Single-site rollout — no inter-site coordination overhead."
    if num_facilities <= 3:
        return "Medium", (
            f"{int(num_facilities)} facilities involved — establish a "
            "central program management function before kickoff."
        )
    return "High", (
        f"{int(num_facilities)} facilities involved — multi-site rollouts at "
        "this scale require dedicated PMO, harmonized templates, and "
        "sequenced site-by-site go-live. Without these, the rollout will "
        "fragment."
    )


def risk_sponsorship(prior_attempt, operator_familiarity, **_):
    if prior_attempt == "Yes — stalled or failed":
        return "High", (
            "A prior digitization attempt stalled or failed at this facility. "
            "This typically indicates either thin executive sponsorship or "
            "sponsorship that fades under pressure. Re-engaging sponsors "
            "with a clear remit is critical before restarting."
        )
    if prior_attempt == "No — first attempt" and operator_familiarity == "Low":
        return "Medium", (
            "First attempt at line clearance digitization combined with low "
            "operator familiarity — sponsorship will be tested when the "
            "rollout hits friction. Confirm and document sponsor commitment "
            "before kickoff."
        )
    if prior_attempt == "Yes — successful":
        return "Low", (
            "A previous successful digitization attempt implies established "
            "executive sponsorship and an organization that knows how to "
            "deliver these projects."
        )
    return "Medium", (
        "First-time attempt — sponsorship strength is unproven. Secure "
        "explicit, written commitment from a named executive before kickoff."
    )


def risk_change_control(validation_maturity, deviation_frequency, **_):
    if (
        validation_maturity == "Underdeveloped"
        and deviation_frequency in ("3–5", "6 or more")
    ):
        return "High", (
            f"QA is already absorbing {deviation_frequency} line clearance "
            "deviations per year against an underdeveloped validation "
            "function. Change-control submissions for OpenLine will queue "
            "behind existing deviations. Address QA capacity first."
        )
    if deviation_frequency == "6 or more":
        return "High", (
            "Six or more deviations in the past year indicate the quality "
            "system is overloaded. New change-control submissions will "
            "compete for the same QA bandwidth."
        )
    if (
        validation_maturity == "Functional but ad-hoc"
        and deviation_frequency in ("3–5", "6 or more")
    ):
        return "Medium", (
            "Ad-hoc validation combined with elevated deviation count — "
            "QA bandwidth will be tight. Schedule the OpenLine change-control "
            "review during a quieter deviation window."
        )
    return "Low", (
        "Quality system has the bandwidth to handle the change-control "
        "submission alongside business as usual."
    )


def risk_pilot_fatigue(prior_attempt, **_):
    if prior_attempt == "Yes — stalled or failed":
        return "High", (
            "A prior line clearance digitization attempt stalled or failed. "
            "Without a clear post-mortem and visible changes to what's "
            "different this time, organizational skepticism will undermine "
            "the next attempt."
        )
    if prior_attempt == "No — first attempt":
        return "Low", (
            "First attempt — no historical baggage. Use this clean slate to "
            "establish a track record."
        )
    return "Low", (
        "A previous successful attempt creates positive momentum and "
        "internal advocates."
    )


def risk_equipment_compatibility(equipment_age, mes_system, **_):
    if equipment_age == "Mostly over 10 years":
        return "High", (
            "Equipment is mostly over 10 years old — expect PLC firmware "
            "mismatches, missing data outputs, and sensor compatibility "
            "issues. Plan a site survey before scoping."
        )
    if equipment_age == "Mixed (some new, some old)" and mes_system in ("None", "Other / Custom"):
        return "Medium", (
            "Mixed-age equipment combined with no standard MES — line-level "
            "data extraction will vary across lines. Catalog by line before "
            "committing to a rollout sequence."
        )
    if equipment_age == "Mixed (some new, some old)":
        return "Medium", (
            "Mixed-age equipment — newer lines will go live faster; older "
            "lines may need targeted upgrades."
        )
    return "Low", (
        "Modern equipment fleet — sensor and PLC integration should be "
        "straightforward."
    )


RISK_RULES = [
    ("Legacy MES/ERP integration complexity", risk_legacy_integration),
    ("Validation documentation backlog",      risk_validation_backlog),
    ("Operator adoption and training risk",   risk_operator_adoption),
    ("Multi-site coordination risk",          risk_multi_site_coordination),
    ("Executive sponsorship fragility",       risk_sponsorship),
    ("Change-control / quality system bottleneck", risk_change_control),
    ("Past-failure / pilot-fatigue risk",     risk_pilot_fatigue),
    ("Equipment age and PLC compatibility",   risk_equipment_compatibility),
]


# ============================================================================
# RECOMMENDATIONS LIBRARY (new in Phase 4D)
# ============================================================================
#
# Each recommendation is a function that takes the inputs and the risk
# results, and returns either None (don't recommend) or a string (do).
#
# Recommendations are then sorted by PRIORITY:
#   1 = Regulatory blocker (must address before doing anything else)
#   2 = Past-failure remediation (must address before restarting)
#   3 = Foundational technical gap (must address before rollout)
#   4 = Process / change-management improvement
#   5 = Tactical / sequencing improvement
#
# The output to the user is the top 5–7 recommendations, sorted by priority.
# ============================================================================


def rec_regulatory_observations(inspection_outcome, **_):
    if inspection_outcome == "Major observations":
        return (
            1,
            "**Resolve outstanding regulatory observations first.** Adding "
            "new validation scope while major inspection observations are "
            "open creates regulatory exposure. Close the existing CAPA "
            "actions before initiating any OpenLine work."
        )
    return None


def rec_validation_capacity(validation_maturity, num_lines, **_):
    if validation_maturity == "Underdeveloped":
        return (
            1,
            f"**Build validation templates before scoping.** Validation "
            f"maturity is underdeveloped, and you're targeting {num_lines} "
            "lines. Without reusable IQ/OQ/PQ templates, the documentation "
            "effort will consume your QA team. Invest in templates and "
            "training before kickoff."
        )
    return None


def rec_prior_attempt_postmortem(prior_attempt, **_):
    if prior_attempt == "Yes — stalled or failed":
        return (
            2,
            "**Conduct a post-mortem on the previous attempt before "
            "restarting.** A prior stalled attempt creates organizational "
            "skepticism. Identify what failed (sponsorship, tech, change "
            "management, scope), document it, and explicitly state what's "
            "different this time. Without this, the new attempt will face "
            "the same skepticism."
        )
    return None


def rec_sponsorship(prior_attempt, operator_familiarity, **_):
    if prior_attempt == "Yes — stalled or failed":
        return (
            2,
            "**Re-engage executive sponsorship with a documented remit.** "
            "Given the prior failure, sponsor commitment must be explicit, "
            "named, and documented — verbal endorsement won't survive the "
            "first friction. Define decision rights and escalation paths "
            "upfront."
        )
    if prior_attempt == "No — first attempt" and operator_familiarity == "Low":
        return (
            4,
            "**Confirm and document executive sponsorship before kickoff.** "
            "First attempts combined with low operator familiarity will "
            "test sponsor commitment. Get written commitment from a named "
            "executive with budget authority."
        )
    return None


def rec_ebr_first(ebr_system, mes_system, **_):
    if ebr_system == "No":
        return (
            3,
            "**Establish electronic batch record coverage before OpenLine.** "
            "Without eBR, OpenLine integration must build the batch-record "
            "interface from scratch, which adds months and creates a single "
            "point of failure. Implement at least partial eBR coverage first."
        )
    return None


def rec_mes_strategy(mes_system, **_):
    if mes_system == "None":
        return (
            3,
            "**Define an MES strategy before scoping OpenLine.** With no "
            "MES, OpenLine has nothing to receive batch context from or "
            "send completion signals to. Choose whether to deploy a "
            "pharma-grade MES (Werum, SAP, Rockwell) in parallel or to "
            "scope OpenLine as a standalone solution with manual MES "
            "interfaces."
        )
    return None


def rec_qa_capacity(validation_maturity, deviation_frequency, **_):
    if (
        validation_maturity == "Underdeveloped"
        and deviation_frequency in ("3–5", "6 or more")
    ):
        return (
            1,
            "**Address QA capacity before adding new change-control "
            f"submissions.** You have {deviation_frequency} deviations per "
            "year against an underdeveloped validation function. New "
            "submissions will queue behind existing CAPAs. Either expand "
            "QA capacity or sequence OpenLine behind the deviation backlog."
        )
    if deviation_frequency == "6 or more":
        return (
            4,
            "**Run a deviation-reduction sprint before adding scope.** "
            "Six or more deviations per year suggests the underlying "
            "process is unstable. Stabilize first; otherwise OpenLine will "
            "inherit the same instability post-deployment."
        )
    return None


def rec_operator_training(operator_familiarity, current_method, **_):
    if operator_familiarity == "Low" and current_method == "Fully paper-based":
        return (
            4,
            "**Build operator readiness before go-live.** Operators moving "
            "from fully paper-based to AI-assisted line clearance need "
            "structured training, change champions on each shift, and "
            "shadow-operation periods before cutover. Budget 2–3 months."
        )
    if operator_familiarity == "Low":
        return (
            4,
            "**Identify and train change-champion operators on each shift.** "
            "Low overall familiarity is overcome by visible peer adoption. "
            "Train the highest-aptitude operators first and let them lead."
        )
    return None


def rec_equipment_audit(equipment_age, **_):
    if equipment_age == "Mostly over 10 years":
        return (
            3,
            "**Conduct a line-by-line equipment audit before scoping.** "
            "With equipment mostly over 10 years old, expect PLC firmware "
            "mismatches and missing data outputs. Some lines may need "
            "upgrades before OpenLine can be deployed; the audit determines "
            "which."
        )
    return None


def rec_multi_site_pmo(num_facilities, **_):
    if num_facilities >= 4:
        return (
            5,
            f"**Establish a dedicated PMO for the {int(num_facilities)}-site "
            "rollout.** At this scale, central program management, "
            "harmonized validation templates, and a sequenced site-by-site "
            "go-live plan are non-negotiable. Without them, sites diverge."
        )
    if num_facilities in (2, 3):
        return (
            5,
            f"**Designate a central rollout lead across the "
            f"{int(num_facilities)} facilities.** Even at small multi-site "
            "scale, one accountable owner prevents the sites from "
            "diverging on validation approach or operational practice."
        )
    return None


def rec_pilot_scope(prior_attempt, num_lines, **_):
    if prior_attempt == "Yes — stalled or failed" and num_lines > 5:
        return (
            5,
            f"**Reduce initial scope from {num_lines} lines to 2–3 lines "
            "for the restart.** A focused restart with visible early wins "
            "rebuilds organizational confidence faster than a broad "
            "rollout. Expand only after the restart proves stable."
        )
    return None


RECOMMENDATION_RULES = [
    rec_regulatory_observations,
    rec_validation_capacity,
    rec_prior_attempt_postmortem,
    rec_sponsorship,
    rec_ebr_first,
    rec_mes_strategy,
    rec_qa_capacity,
    rec_operator_training,
    rec_equipment_audit,
    rec_multi_site_pmo,
    rec_pilot_scope,
]


# ============================================================================
# ENGINES
# ============================================================================

def compute_readiness_score(
    current_method, clearance_duration, deviation_frequency,
    operator_familiarity, prior_attempt,
    inspection_outcome, validation_maturity,
    mes_system, ebr_system, equipment_age,
):
    process_inputs = [
        SCORE_CURRENT_METHOD[current_method],
        SCORE_CLEARANCE_DURATION[clearance_duration],
        SCORE_DEVIATION_FREQUENCY[deviation_frequency],
    ]
    process_score = sum(process_inputs) / len(process_inputs)

    org_inputs = [
        SCORE_OPERATOR_FAMILIARITY[operator_familiarity],
        SCORE_PRIOR_ATTEMPT[prior_attempt],
    ]
    org_score = sum(org_inputs) / len(org_inputs)

    reg_inputs = [
        SCORE_INSPECTION_OUTCOME[inspection_outcome],
        SCORE_VALIDATION_MATURITY[validation_maturity],
    ]
    reg_score = sum(reg_inputs) / len(reg_inputs)

    tech_inputs = [
        SCORE_MES_SYSTEM[mes_system],
        SCORE_EBR_SYSTEM[ebr_system],
        SCORE_EQUIPMENT_AGE[equipment_age],
    ]
    tech_score = sum(tech_inputs) / len(tech_inputs)

    total = (
        process_score * WEIGHTS["process"]
        + org_score * WEIGHTS["organizational"]
        + reg_score * WEIGHTS["regulatory"]
        + tech_score * WEIGHTS["technical"]
    )

    verdict_label = ""
    verdict_message = ""
    for low, high, label, message in VERDICT_BANDS:
        if low <= total <= high:
            verdict_label = label
            verdict_message = message
            break

    return {
        "total":           round(total, 1),
        "process":         round(process_score, 1),
        "organizational":  round(org_score, 1),
        "regulatory":      round(reg_score, 1),
        "technical":       round(tech_score, 1),
        "verdict_label":   verdict_label,
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
    deployment_cost = (
        num_facilities * first_line_cost
        + num_facilities * (lines_per_facility - 1) * additional_line_cost
    )

    payback_months = (
        (deployment_cost / annual_savings) * 12 if annual_savings > 0 else None
    )

    return {
        "annual_events":       int(annual_clearance_events),
        "current_annual_cost": current_annual_cost,
        "post_rollout_cost":   post_rollout_cost,
        "annual_savings":      annual_savings,
        "deployment_cost":     deployment_cost,
        "payback_months":      payback_months,
    }


def compute_risk_heatmap(**inputs):
    results = []
    for name, rule_fn in RISK_RULES:
        rating, explanation = rule_fn(**inputs)
        results.append((name, rating, explanation))
    return results


def compute_recommendations(**inputs):
    """
    Run every recommendation rule. Collect non-None results.
    Sort by priority (lower number = higher priority).
    Return top 7 recommendations.
    """
    candidates = []
    for rule_fn in RECOMMENDATION_RULES:
        result = rule_fn(**inputs)
        if result is not None:
            priority, text = result
            candidates.append((priority, text))

    # Stable sort by priority
    candidates.sort(key=lambda x: x[0])

    # If we have fewer than 3 high-priority recommendations, the factory is
    # in good shape and only needs tactical advice. In that case, return
    # whatever we have. Otherwise cap at 7.
    return [text for _, text in candidates[:7]]


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
        num_lines=num_lines,
        num_facilities=num_facilities,
        current_method=current_method,
        clearance_duration=clearance_duration,
        deviation_frequency=deviation_frequency,
        mes_system=mes_system,
        ebr_system=ebr_system,
        equipment_age=equipment_age,
        inspection_outcome=inspection_outcome,
        validation_maturity=validation_maturity,
        operator_familiarity=operator_familiarity,
        prior_attempt=prior_attempt,
    )

    risks = compute_risk_heatmap(**common_inputs)
    recommendations = compute_recommendations(**common_inputs)

    payback_text = (
        f"**{roi['payback_months']:.1f} months**"
        if roi["payback_months"] is not None
        else "Not applicable (no projected savings)"
    )

    risk_table_rows = "\n".join(
        f"| {name} | {RATING_ICON[rating]} | {explanation} |"
        for name, rating, explanation in risks
    )

    high_count = sum(1 for _, r, _ in risks if r == "High")
    med_count  = sum(1 for _, r, _ in risks if r == "Medium")
    low_count  = sum(1 for _, r, _ in risks if r == "Low")

    # Build recommendation list
    if recommendations:
        rec_block = "\n\n".join(
            f"{i+1}. {text}"
            for i, text in enumerate(recommendations)
        )
    else:
        rec_block = (
            "**No critical remediation needed.** Your readiness score and "
            "risk profile suggest you can proceed directly to rollout planning. "
            "Standard project hygiene applies: secure budget, set milestones, "
            "and define success metrics before kickoff."
        )

    summary = f"""
## Readiness Assessment

### Overall Readiness Score: **{score['total']} / 100**

### Verdict: **{score['verdict_label']}**
{score['verdict_message']}

---

### Sub-score Breakdown

| Category | Weight | Score |
|---|---|---|
| Process readiness | 30% | **{score['process']}** / 100 |
| Organizational readiness | 30% | **{score['organizational']}** / 100 |
| Regulatory readiness | 25% | **{score['regulatory']}** / 100 |
| Technical readiness | 15% | **{score['technical']}** / 100 |

---

## Financial Projection (ROI)

| Metric | Value |
|---|---|
| Annual line clearance events | **{roi['annual_events']:,}** |
| Current annual line clearance cost | **{_fmt_money(roi['current_annual_cost'])}** |
| Projected post-rollout annual cost | **{_fmt_money(roi['post_rollout_cost'])}** |
| **Annual savings** | **{_fmt_money(roi['annual_savings'])}** |
| Estimated deployment cost | **{_fmt_money(roi['deployment_cost'])}** |
| **Payback period** | {payback_text} |

### How this was calculated

- **Annual clearance events:** {num_lines} lines × {changeovers_per_week} changeovers/week × 48 production weeks/year
- **Labor hours per event:** {DURATION_TO_HOURS[clearance_duration]} hours × 2 operators (operator + QA witness, per GMP)
- **Labor rate used:** {_fmt_money(labor_rate)}/hour (fully-loaded — adjustable in Advanced)
- **Time savings applied:** {time_savings_pct}% (Catalyx publishes 85%; default conservatively halved)
- **Deployment cost:** {_fmt_money(first_line_cost)} per first line across {num_facilities} facilities, plus {_fmt_money(additional_line_cost)} per additional line

---

## Risk Heatmap

**Summary:** 🔴 {high_count} High · 🟡 {med_count} Medium · 🟢 {low_count} Low

| Risk | Rating | Why this rating |
|---|---|---|
{risk_table_rows}

---

## Next-Steps Recommendation

Based on your inputs, these are the actions to take *before* committing to a
full OpenLine rollout, ordered by priority:

{rec_block}

---

*Phase 4 complete. The simulator now produces all four spec outputs: readiness
score, ROI projection, risk heatmap, and tailored next-steps. Phase 5 will add
visual charts (readiness gauge, ROI timeline, risk heatmap visual). Phase 6
adds a downloadable PDF executive summary.*
"""
    return summary


# ============================================================================
# UI
# ============================================================================

INTRO_TEXT = """
# OpenLine Readiness Simulator

A free assessment tool that helps pharma manufacturing leaders evaluate whether
their factories are ready to roll out AI-powered line clearance — *before*
committing budget to a full deployment.

**Why this exists:**
Catalyx's own 2025 Line Clearance Benchmark Report shows that roughly half the
pharma industry piloted digital line clearance tools in 2023, but by 2025 only
**11% had actually rolled them out**. Most pilots succeed technically — and
then stall before becoming production deployments.

*Currently in development. Phase 4D — full assessment engine. Visual charts
and PDF export coming in Phases 5 and 6.*

---

### Instructions
Answer the 15 questions below. All fields have sensible defaults — adjust
those that apply to your situation. Optionally expand "Advanced assumptions"
to override the financial inputs. Click **Submit** to see your full assessment.
"""

with gr.Blocks(title="OpenLine Readiness Simulator") as demo:
    gr.Markdown(INTRO_TEXT)

    with gr.Accordion("Section 1: Factory Profile", open=True):
        num_lines = gr.Slider(label="Number of production lines in scope for rollout",
                              minimum=1, maximum=100, value=10, step=1)
        num_facilities = gr.Slider(label="Number of facilities involved",
                                   minimum=1, maximum=20, value=2, step=1)
        annual_volume = gr.Radio(
            label="Approximate annual production volume",
            choices=["Under 1 million units", "1–10 million units",
                     "10–100 million units", "Over 100 million units"],
            value="1–10 million units",
        )
        product_type = gr.Radio(
            label="Primary product type",
            choices=["Oral solid dose", "Injectable", "Biologic", "Medical device", "Other"],
            value="Oral solid dose",
        )

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
            value="No — first attempt",
        )

    with gr.Accordion("Advanced assumptions (optional — override defaults)", open=False):
        gr.Markdown("These defaults come from publicly available industry data. "
                    "Adjust any of them to reflect your own assumptions, then re-run.")
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

    submit_btn = gr.Button("Submit", variant="primary", size="lg")
    output = gr.Markdown()

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
        outputs=output,
    )


if __name__ == "__main__":
    demo.launch()