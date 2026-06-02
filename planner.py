import gurobipy as gp
from gurobipy import GRB
from scipy.stats import norm

from dawgpath import add_predictions, parse_courses
from requirements import (
    candidate_limit,
    degree_requirements,
    initial_sequence_prereqs,
    iter_one_of_branches,
    prepare_plan,
    prereq_met,
)
from risk import risk_data, risk_terms
from student_profile import majors, transcript

seasons = ("A", "W", "Sp")
data = "dawgpath.json"
max_quarters = 9
start_year = 2026
min_credits = 12
max_credits = 30
wgpa = 1.0
wtime = 10.0
wrisk = 500.0
time_limit = 210
gpa_threshold = 3.5
confidence = 0.90
ideal_credits = 16
vi_rate = 0.65
target_GPA = 3.5


def build_quarters(num_quarters, yr):
    quarters = []
    year = yr
    for i in range(num_quarters):
        season = seasons[i % 3]
        if season == "A":
            label = f"A{year}"
        elif season == "W":
            label = f"W{year + 1}"
        else:
            label = f"Sp{year + 1}"
            year += 1
        quarters.append({"label": label, "season": season, "index": i})
    return quarters


def build_result(model, x, overload_vars, inflation_vars, o, risk, candidates, courses, quarters, threshold, conf, wgpa, wtime, wrisk):
    plan = {q["label"]: [c for c in sorted(candidates) if x[c, q["label"]].X > 0.5] for q in quarters}
    per_quarter_credits = {q["label"]: sum(courses[c]["credits"] for c in plan[q["label"]]) for q in quarters}
    per_quarter_overload = {q["label"]: overload_vars[q["label"]].X for q in quarters}
    per_quarter_inflation = {q["label"]: inflation_vars[q["label"]].X for q in quarters}

    scheduled = list({c for qcourses in plan.values() for c in qcourses})
    total_credits = sum(courses[c]["credits"] for c in scheduled)
    weighted_mean = sum(courses[c]["credits"] * courses[c]["predicted_mean"] for c in scheduled)
    weighted_var = sum(
        courses[c]["credits"]**2 * courses[c]["predicted_variance"] * (1 + per_quarter_inflation[q])
        for q, qcourses in plan.items()
        for c in qcourses
    )
    plan_mean = weighted_mean / total_credits
    plan_sd = (weighted_var / total_credits**2) ** 0.5
    achieved_conf = norm.cdf((plan_mean - threshold) / plan_sd) if plan_sd > 0 else 1.0
    active_quarters = sum(1 for qcourses in plan.values() if qcourses)
    Roverload_expr, Rgateway_expr, Risk_expr = risk_terms(x, o, risk, candidates, quarters)
    Roverload, Rgateway, Risk = Roverload_expr.getValue(), Rgateway_expr.getValue(), Risk_expr.getValue()
    objective = wgpa * weighted_mean - wtime * active_quarters - wrisk * Risk

    return {
        "status": model.Status, "objective": objective,
        "courses": courses, "threshold": threshold, "confidence": conf,
        "plan": plan, "plan_mean": plan_mean, "plan_sd": plan_sd,
        "achieved_confidence": achieved_conf, "total_credits": total_credits,
        "Roverload": Roverload, "Rgateway": Rgateway, "Risk": Risk,
        "per_quarter_credits": per_quarter_credits,
        "per_quarter_overload": per_quarter_overload,
        "per_quarter_inflation": per_quarter_inflation,
    }


def run_solver(courses, rules, candidates, quarters, transcript, min_credits, max_credits, wgpa, wtime, wrisk, time_limit, gpa_threshold, z_val, confidence, ideal_credits, vi_rate, risk):
    model = gp.Model("planner")
    model.Params.TimeLimit = time_limit
    model.Params.OutputFlag = 0

    # 4.2 Decision Variables
    labels = [q["label"] for q in quarters]
    cq = [(c, l) for c in sorted(candidates) for l in labels]
    x = model.addVars(cq, vtype=GRB.BINARY, name="x")                    # spec: x_{c,t} = 1 if course c is scheduled in quarter t
    y = model.addVars(labels, vtype=GRB.BINARY, name="y")                # spec: y_t   = 1 if quarter t has at least one course scheduled
    overload = model.addVars(labels, lb=0.0, name="overload")            # spec: overload_t >= 0, number of credits over ideal in quarter t
    inflation = model.addVars(labels, lb=0.0, name="inflation")          # spec: inflation_t >= 0, variance inflation factor in quarter t
    variance_factor = model.addVars(cq, lb=0.0, name="variance_factor")  # aux: equals (1 + inflation_t) when c is scheduled in t
    o = model.addVars(labels, lb=0.0, name="o")                          # aux: weighted-difficulty overload surrogate (spec 5.1)

    # 4.3 Objective
    # spec: max  w_gpa * sum_{c,t} Cr_c * mu_c * x_{c,t}  -  w_time * sum_t y_t   (minus w_risk * Risk, spec 5)
    gpa_term = gp.quicksum(courses[c]["credits"] * courses[c]["predicted_mean"] * x[c, q["label"]] for c in candidates for q in quarters)
    time_term = gp.quicksum(y[q["label"]] for q in quarters)
    _, _, Risk = risk_terms(x, o, risk, candidates, quarters)
    model.setObjective(wgpa * gpa_term - wtime * time_term - wrisk * Risk, GRB.MAXIMIZE)

    # 4.4 Structural Constraints
    for c in candidates:
        model.addConstr(gp.quicksum(x[c, q["label"]] for q in quarters) <= 1, name=f"once_{c}")  # spec: sum_t x_{c,t} <= 1 for all c
        for q in quarters:
            if q["season"] not in courses[c]["offered"]:                                          # spec: x_{c,t} = 0 for all t s.t. season(t) not in Q_c
                model.addConstr(x[c, q["label"]] == 0, name=f"offered_{c}_{q['label']}")
            model.addConstr(x[c, q["label"]] <= y[q["label"]], name=f"active_{c}_{q['label']}")    # spec: x_{c,t} <= y_t (quarters taken contain >= 1 class)
    for q in quarters:
        cr = gp.quicksum(courses[c]["credits"] * x[c, q["label"]] for c in candidates)
        model.addConstr(cr >= min_credits * y[q["label"]], name=f"min_cr_{q['label']}")            # spec: sum_c Cr_c * x_{c,t} >= min_credits
        model.addConstr(cr <= max_credits * y[q["label"]], name=f"max_cr_{q['label']}")            # max-credit bound (spec 5.1: UW caps a quarter at 30)
    for prev, cur in zip(quarters, quarters[1:]):
        model.addConstr(y[prev["label"]] >= y[cur["label"]], name=f"mono_{prev['label']}_{cur['label']}")  # spec: y_i >= y_{i+1} (quarters consecutive)

    # 4.5 Prerequisites
    # spec: (1 if exists p in P_g where p in L) + sum_{p in P_g} sum_{t'<t} x_{p,t'}  >=  x_{c,t}
    grades = {entry["course_id"]: entry["grade"] for entry in transcript}
    seq_prereqs = initial_sequence_prereqs(transcript, courses)
    for cid in sorted(candidates):
        for q in quarters:
            for gi, group in enumerate(courses[cid]["prereqs"]):
                if any(prereq_met(p, grades, seq_prereqs) for p in group):  # group already covered by the transcript -> left term is 1
                    continue
                terms = []
                for prereq in group:                                        # OR within a prerequisite group P_g
                    pid = prereq["course"]
                    if prereq_met(prereq, grades, seq_prereqs):
                        terms.append(1)
                    elif pid in candidates and courses[pid]["predicted_mean"] >= prereq["min_grade"]:
                        terms.append(gp.quicksum(                            # sum_{t'<t} x_{p,t'} (t'<=t when concurrency is allowed)
                            x[pid, q2["label"]] for q2 in quarters
                            if q2["index"] < q["index"] or (prereq["concurrent"] and q2["index"] == q["index"])
                        ))
                name = f"prereq_{cid}_{q['label']}_{gi}"
                if terms:
                    model.addConstr(gp.quicksum(terms) >= x[cid, q["label"]], name=name)
                else:
                    model.addConstr(x[cid, q["label"]] == 0, name=name)     # no way to satisfy the group -> course unavailable

    # 4.6 Degree Requirements (spec: one-of is handled outside the IP -- the solver branches per option, see solve)
    for req in rules:
        rid = req["id"]
        if req["type"] == "all":                                            # spec (all): sum_t x_{c,t} >= 1 for all c in M_r
            for c in req["courses"]:
                if c in candidates:
                    model.addConstr(gp.quicksum(x[c, q["label"]] for q in quarters) >= 1, name=f"req_{rid}_{c}")
            continue
        if req["type"] == "k_of_n":                                         # spec (k-of-n): sum_{g in G_r} z_g >= k_r, z_g in {0,1} marks a group as taken
            required = set(req.get("required", []))
            indicators = []
            for idx, group in enumerate(req.get("courses", [])):
                usable = [c for c in group if c in candidates]
                if not usable:
                    continue
                z = model.addVar(vtype=GRB.BINARY, name=f"seq_{rid}_{idx}")  # z_g: whole group taken together (s == z for each course), or not at all
                for c in usable:
                    s = gp.quicksum(x[c, q["label"]] for q in quarters)
                    model.addConstr(s >= z, name=f"seq_{rid}_{idx}_{c}_lb")
                    model.addConstr(s <= z, name=f"seq_{rid}_{idx}_{c}_ub")
                if idx in required:
                    model.addConstr(z == 1, name=f"seq_{rid}_{idx}_required")
                indicators.append(z)
            if indicators:
                model.addConstr(gp.quicksum(indicators) >= req["k"], name=f"req_{rid}")
            continue
        if "any" in req:                                                    # spec: rules with "any": true apply to the entire candidate pool
            usable = [c for c in candidates if courses[c]["number"] >= req.get("min_number", 0)]
        else:
            usable = [c for item in req.get("courses", []) for c in ([item] if isinstance(item, str) else item) if c in candidates]
        if req["type"] == "credits":                                        # spec (credits): sum_{c in M_r} sum_t Cr_c * x_{c,t} >= Cr_r
            model.addConstr(gp.quicksum(courses[c]["credits"] * x[c, q["label"]] for c in usable for q in quarters) >= req["min_credits"], name=f"req_{rid}")
        elif req["type"] == "at_most":                                      # spec (at-most): sum_{c in M_r} sum_t x_{c,t} <= k_r
            model.addConstr(gp.quicksum(x[c, q["label"]] for c in usable for q in quarters) <= req["k"], name=f"req_{rid}")

    # 4.7 Overload & its Contribution to Variance
    for q in quarters:
        l = q["label"]
        excess = model.addVar(lb=-GRB.INFINITY, name=f"excess_{l}")
        model.addConstr(excess == gp.quicksum(courses[c]["credits"] * x[c, l] for c in candidates) - ideal_credits, name=f"excess_def_{l}")
        model.addGenConstrMax(overload[l], [excess], constant=0.0, name=f"overload_{l}")              # spec: overload_t >= sum_c Cr_c*x_{c,t} - ideal_credits, overload_t >= 0
        model.addQConstr(inflation[l] >= vi_rate * overload[l] * overload[l], name=f"inflation_{l}")  # spec: inflation_t >= vi_rate * overload_t^2 (second-order cone)
        for c in candidates:                                                                          # apply inflation per quarter via variance_factor = (1 + inflation_t) when scheduled
            model.addGenConstrIndicator(x[c, l], False, variance_factor[c, l] == 0, name=f"vf_zero_{c}_{l}")
            model.addGenConstrIndicator(x[c, l], True, variance_factor[c, l] == 1 + inflation[l], name=f"vf_active_{c}_{l}")

    # 4.8 Cumulative Chance Constraint
    # spec: sum Cr_c*mu_c*x  -  Phi^-1(confidence) * sd'  >=  gpa_threshold * sum Cr_c*x
    mean_sum = gp.quicksum(courses[c]["credits"] * courses[c]["predicted_mean"] * x[c, q["label"]] for c in candidates for q in quarters)
    credits_sum = gp.quicksum(courses[c]["credits"] * x[c, q["label"]] for c in candidates for q in quarters)
    variance_sum = gp.quicksum(courses[c]["credits"]**2 * courses[c]["predicted_variance"] * variance_factor[c, q["label"]] for c in candidates for q in quarters)
    sd_var = model.addVar(lb=0.0, name="plan_sd")
    model.addConstr(sd_var * sd_var >= variance_sum, name="sd_definition")                            # spec: sd'^2 >= sum_{c,t} Cr_c^2 * sigma_c^2 * (1 + inflation_t) * x_{c,t}
    model.addConstr(mean_sum - z_val * sd_var >= gpa_threshold * credits_sum, name="chance_constraint")

    # 5 Risk Model -- 5.1 overload, linear surrogate
    # spec: o_t >= sum_c L_c * x_{c,t} - B * y_t, o_t >= 0, with L_c = Cr_c*(4 - mu_c) and B = ideal_credits*(4 - target_GPA)
    for q in quarters:
        l = q["label"]
        model.addConstr(o[l] >= gp.quicksum(risk["L"][c] * x[c, l] for c in candidates) - risk["B"] * y[l], name=f"risk_overload_{l}")

    model.optimize()
    if model.SolCount == 0:
        return None
    return build_result(model, x, overload, inflation, o, risk, candidates, courses, quarters, gpa_threshold, confidence, wgpa, wtime, wrisk)


def solve(data_path, transcript, majors, num_quarters, yr, min_credits, max_credits, wgpa, wtime, wrisk, time_limit, climit, gpa_threshold, confidence, ideal_credits, vi_rate, target_GPA):
    z_val = norm.ppf(confidence)
    courses = parse_courses(data_path)
    reqs = degree_requirements(majors, transcript)
    candidates, rules = prepare_plan(reqs, transcript, courses, limit=climit)
    add_predictions(courses, transcript, candidates)
    quarters = build_quarters(num_quarters, yr)
    risk = risk_data(candidates, courses, quarters, ideal_credits, target_GPA)

    best = None
    for _, branch_rules in iter_one_of_branches(rules):
        result = run_solver(courses, branch_rules, candidates, quarters, transcript, min_credits, max_credits, wgpa, wtime, wrisk, time_limit, gpa_threshold, z_val, confidence, ideal_credits, vi_rate, risk)
        if result is None or result["status"] not in (GRB.OPTIMAL, GRB.SUBOPTIMAL):
            continue
        if best is None or result["objective"] > best["objective"]:
            best = result
    return best


def print_plan(result):
    if result is None:
        print("no feasible plan found")
        return
    print(f"solver status: {result['status']}")
    print(f"objective: {result['objective']:.3f}")
    print(f"predicted plan GPA: {result['plan_mean']:.3f}")
    print(f"plan SD: {result['plan_sd']:.3f}")
    print(f"gpa threshold: {result['threshold']:.3f} at {100*result['confidence']:.1f}% confidence")
    print(f"achieved confidence: {100*result['achieved_confidence']:.2f}%")
    print(f"risk: {result['Risk']:.3f}  Roverload={result['Roverload']:.3f}  Rgateway={result['Rgateway']:.3f}")
    print(f"total planned credits: {result['total_credits']:.1f}")

    courses = result["courses"]
    overloads = result["per_quarter_overload"]
    inflations = result["per_quarter_inflation"]
    print()
    print("optimal course path")
    print("-------------------")
    for quarter, course_ids in result["plan"].items():
        if not course_ids:
            continue
        header = f"{quarter} ({sum(courses[c]['credits'] for c in course_ids):.1f} credits)"
        if overloads[quarter] > 1e-6:
            header += f"  [overload {overloads[quarter]:.1f}, variance x{1+inflations[quarter]:.2f}]"
        print(header)
        for c in course_ids:
            course = courses[c]
            print(f"  {c:<10} {course['credits']:>4.1f} cr  mu={course['predicted_mean']:.2f}  sd={course['predicted_variance']**0.5:.2f}  {course['title']}")
        print()

if __name__ == "__main__":
    print_plan(solve(data, transcript, majors, max_quarters, start_year, min_credits, max_credits, wgpa, wtime, wrisk, time_limit, candidate_limit, gpa_threshold, confidence, ideal_credits, vi_rate, target_GPA))
