import gurobipy as gp


def downstream_counts(courses, candidates):
    children = {c: set() for c in candidates}
    for cid in candidates:
        for group in courses[cid]["prereqs"]:
            for prereq in group:
                if prereq["course"] in children:
                    children[prereq["course"]].add(cid)
    counts = {}
    for cid in candidates:
        seen = set()
        stack = list(children[cid])
        while stack:
            child = stack.pop()
            if child in seen:
                continue
            seen.add(child)
            stack.extend(children[child] - seen)
        counts[cid] = len(seen)
    return counts


def risk_data(candidates, courses, quarters, ideal_credits, target_GPA):
    L = {c: courses[c]["credits"] * (4 - courses[c]["predicted_mean"]) for c in candidates}
    succ = downstream_counts(courses, candidates)
    gateway = {c: (1 + succ[c]) * int(courses[c]["is_gateway"]) for c in candidates}
    B = ideal_credits * (4 - target_GPA)
    R0overload = max(0, 4 * (sum(L.values()) / len(L)) - B) * len(quarters)
    R0gateway = 4 * (sum(gateway.values()) / len(gateway)) * len(quarters)
    return {
        "L": L, "gateway": gateway, "B": B,
        # A baseline plan at ideal load produces no overload (R0overload == 0), so
        # the §5.4 normalization is degenerate for the overload term; fall back to 1.
        "alpha": 1 / R0overload if R0overload else 1.0,
        "beta": 1 / R0gateway if R0gateway else 1.0,
    }


def risk_terms(x, o, risk, candidates, quarters):
    Roverload = gp.quicksum(o[q["label"]] for q in quarters)
    Rgateway = gp.quicksum(risk["gateway"][c] * x[c, q["label"]] for c in candidates for q in quarters)
    Risk = risk["alpha"] * Roverload + risk["beta"] * Rgateway
    return Roverload, Rgateway, Risk
