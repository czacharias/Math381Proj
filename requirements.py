import json
from itertools import product

tag_cap = 80
candidate_limit = 600
upper_div_pool = 120

major_files = {
    "cse": "CSE_REQ.json",
    "math": "MATH_REQ.json",
}

def load_file(filename):
    with open("/Users/connorzacharias/Documents/math381/finalProj/requirements/" + filename) as f:
        return json.load(f)


def initial_sequence_prereqs(transcript, courses):
    taken = {entry["course_id"] for entry in transcript}
    sequence_prereqs = set()
    frontier = set(taken)
    while frontier:
        new_frontier = set()
        for cid in frontier:
            course = courses[cid]
            for group in courses[cid]["prereqs"]:
                for prereq in group:
                    pid = prereq["course"]
                    if pid in courses and pid not in taken and pid not in sequence_prereqs and (course["department"], courses[pid]["number"]) == (courses[pid]["department"], course["number"] - 1):
                        new_frontier.add(pid)
                        sequence_prereqs.add(pid)
        frontier = new_frontier
    return sequence_prereqs


def apply_exclude_from(rules):
    by_id = {rule["id"]: rule for rule in rules}
    for rule in rules:
        if "exclude_from" not in rule:
            continue
        excluded = list(rule.get("exclude_courses", []))
        for other_id in rule["exclude_from"]:
            other = by_id[other_id]
            if other.get("type") == "k_of_n":
                excluded.extend(c for group in other.get("courses", []) for c in group)
            else:
                excluded.extend(other.get("courses", []))
        rule["exclude_courses"] = excluded
        del rule["exclude_from"]

def degree_requirements(majors, transcript):
    taken = {entry["course_id"] for entry in transcript}
    rules = []
    seen = set()
    def add(rule):
        rule = dict(rule)
        if rule["id"] in seen:
            return
        if "unless_taken" in rule and set(rule["unless_taken"]) & taken:
            return
        rule.pop("unless_taken", None)
        seen.add(rule["id"])
        rules.append(rule)
    for rule in load_file("GEN_REQ.json")["rules"]:
        add(rule)
    for major in majors:
        for rule in load_file(major_files[major])["rules"]:
            add(rule)
    apply_exclude_from(rules)
    return {"majors": majors, "rules": rules}


def matching_courses(rule, courses, exclude, cap):
    blocked = exclude | set(rule.get("exclude_courses", []))
    if rule["type"] == "one_of":
        out = []
        for option in rule["options"]:
            out.extend(matching_courses(option, courses, exclude, cap=cap))
        return out
    if "courses" in rule:
        if rule.get("type") == "k_of_n":
            return [c for group in rule["courses"] for c in group if c not in blocked]
        return [c for c in rule["courses"] if c not in blocked]
    if "any" in rule:
        return []
    if "tag" in rule:
        min_number = rule.get("min_number", 0)
        max_number = rule.get("max_number", float("inf"))
        out = []
        for cid, course in courses.items():
            if cid in blocked or rule["tag"] not in course["gen_ed"]:
                continue
            if min_number <= course["number"] <= max_number:
                out.append(cid)
        if cap > 0:
            out.sort(key=lambda c: courses[c].get("predicted_mean", courses[c]["mean"]), reverse=True)
            out = out[:cap]
        return out
    if "depts" in rule:
        min_number = rule.get("min_number", 0)
        max_number = rule.get("max_number", float('inf'))
        out = [c for c in rule.get("also", []) if c not in blocked]
        for cid, course in courses.items():
            if cid in blocked or cid in set(rule.get("exclude", [])):
                continue
            if course["department"].upper() not in rule["depts"]:
                continue
            if min_number <= course["number"] <= max_number:
                out.append(cid)
        return out
    return []

def credits_done(rule, courses, taken):
    if "any" in rule:
        pool = {c for c in courses if courses[c]["number"] >= rule.get("min_number", 0)}
    else:
        pool = set(matching_courses(rule, courses, set(), 0))
    return sum(courses[c]["credits"] for c in taken if c in pool)


def top_up_by_tag(requirements, courses, completed, candidate_ids, limit):
    rules = [r for r in requirements["rules"] if "tag" in r]
    if not rules or len(candidate_ids) >= limit:
        return
    extra_per_tag = (limit - len(candidate_ids)) // len(rules)
    if extra_per_tag <= 0:
        return
    for rule in rules:
        candidate_ids.update(matching_courses(rule, courses, completed | candidate_ids, cap=extra_per_tag))

def top_up_upper_division(courses, completed, candidate_ids, limit, min_pool):
    if len(candidate_ids) >= limit:
        return
    upper_in_pool = sum(1 for c in candidate_ids if courses[c]["number"] >= 300)
    if upper_in_pool >= min_pool:
        return
    for c in sorted(
        (c for c in courses if c not in completed and courses[c]["number"] >= 300),
        key=lambda c: courses[c].get("predicted_mean", courses[c]["mean"]), reverse=True,
    ):
        if c not in candidate_ids:
            candidate_ids.add(c)
            upper_in_pool += 1
        if upper_in_pool >= min_pool or len(candidate_ids) >= limit:
            return


def prereq_met(prereq, grades, sequence_prereqs):
    pid = prereq["course"]
    if pid in sequence_prereqs:
        return True
    min_grade = prereq["min_grade"]
    return pid in grades and grades[pid] >= min_grade


def build_candidates(requirements, transcript, courses, completed, sequence_prereqs, limit):
    grades = {entry["course_id"]: entry["grade"] for entry in transcript}
    candidate_ids = set()
    for rule in requirements["rules"]:
        if "any" in rule:
            continue
        if rule["type"] == "one_of":
            for option in rule["options"]:
                candidate_ids.update(matching_courses(option, courses, completed, 0))
            continue
        candidate_ids.update(matching_courses(rule, courses, completed, tag_cap if "tag" in rule else 0))

    candidate_ids = {c for c in candidate_ids - completed if c in courses}

    changed = True
    while changed:
        changed = False
        for cid in list(candidate_ids):
            for group in courses[cid]["prereqs"]:
                if any(prereq_met(p, grades, sequence_prereqs) for p in group):
                    continue
                for prereq in group:
                    pid = prereq["course"]
                    if pid in completed or pid in candidate_ids:
                        continue
                    if pid in courses:
                        candidate_ids.add(pid)
                        changed = True

    top_up_by_tag(requirements, courses, completed, candidate_ids, limit)
    top_up_upper_division(courses, completed, candidate_ids, limit, upper_div_pool)
    return candidate_ids


def prepare_single_rule(rule, courses, candidate_ids, completed, taken):
    rule = dict(rule)
    if rule["type"] == "all":
        remaining = [c for c in rule["courses"] if c not in completed]
        if not remaining:
            return None
        rule["courses"] = [c for c in remaining if c in candidate_ids]
    elif rule["type"] == "k_of_n":
        prepared_groups = []
        required = []
        completed_groups = 0
        groups = rule["courses"] if "courses" in rule else [[c] for c in matching_courses(rule, courses, set(), 0)]
        for group in groups:
            if all(c in completed for c in group):
                completed_groups += 1
                continue
            remaining = [c for c in group if c not in completed and c in candidate_ids]
            if not remaining:
                continue
            if any(c in completed for c in group):
                required.append(len(prepared_groups))
            prepared_groups.append(remaining)
        remaining_k = rule["k"] - completed_groups
        if remaining_k <= 0 or not prepared_groups:
            return None
        rule["k"] = remaining_k
        rule["courses"] = prepared_groups
        if required:
            rule["required"] = required
    elif rule["type"] == "credits":
        remaining = rule["min_credits"] - credits_done(rule, courses, taken)
        if remaining <= 0:
            return None
        rule["min_credits"] = remaining
        if "any" not in rule:
            rule["courses"] = [c for c in matching_courses(rule, courses, completed, 0) if c in candidate_ids]
            if not rule["courses"]:
                return None
    for key in ("tag", "depts", "also", "exclude", "max_number"):
        rule.pop(key, None)
    return rule


def iter_one_of_branches(rules):
    one_ofs = [r for r in rules if r["type"] == "one_of"]
    if not one_ofs:
        yield None, rules
        return
    for picks in product(*(range(len(r["options"])) for r in one_ofs)):
        chosen = {r["id"]: r["options"][pick] for r, pick in zip(one_ofs, picks)}
        label = "+".join(opt["id"] for opt in chosen.values())
        expanded = []
        for rule in rules:
            if rule["type"] == "one_of":
                expanded.append(chosen[rule["id"]])
            else:
                expanded.append(rule)
        yield label, expanded


def prepare_rules(requirements, transcript, courses, candidate_ids, completed):
    taken = {entry["course_id"] for entry in transcript}
    prepared = []
    for rule in requirements["rules"]:
        if rule["type"] == "one_of":
            options = [prepare_single_rule(opt, courses, candidate_ids, completed, taken) for opt in rule["options"]]
            options = [opt for opt in options if opt is not None]
            if options:
                prepared.append({"id": rule["id"], "type": "one_of", "options": options})
            continue
        pr = prepare_single_rule(rule, courses, candidate_ids, completed, taken)
        if pr is not None:
            prepared.append(pr)
    return prepared

def prepare_plan(requirements, transcript, courses, limit):
    sequence_prereqs = initial_sequence_prereqs(transcript, courses)
    completed = {entry["course_id"] for entry in transcript} | sequence_prereqs
    candidate_ids = build_candidates(requirements, transcript, courses, completed, sequence_prereqs, limit)
    rules = prepare_rules(requirements, transcript, courses, candidate_ids, completed)
    return candidate_ids, rules
