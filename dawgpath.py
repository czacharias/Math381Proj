import json
import re
import numpy as np
from gpa_prediction import predict_course, subject_z_scores

grade_pts = np.array([i / 10.0 for i in range(41)])
gen_ed_tags = {"A&H", "SSc", "NSc", "DIV", "RSN", "C", "sA&H"}
seminar_keywords = (
    "study", "special", "internship",
    "thesis", "thesis", "reading",
    "tutorial", "research",  "seminar", "capstone", "project"
)

def skip_catalog_course(title, number):
    if number in (495, 496, 497, 498, 499):
        return True
    return number >= 400 and any(kw in title.lower() for kw in seminar_keywords)


def gpa_stats(gpa_distro):
    counts = np.array([b["count"] for b in gpa_distro], dtype=float)
    total = counts.sum()
    if total == 0:
        return 0.0, 0.0
    probs = counts / total
    mean = np.sum(probs * grade_pts)
    variance = np.sum(probs * (grade_pts - mean) ** 2)
    return float(mean), float(variance)


def prereq_groups(course_id, prereq_graph):
    if not prereq_graph:
        return []
    edges = prereq_graph["x"]["edges"]
    relevant = [eid for eid, target in edges["to"].items() if target == course_id]
    if not relevant:
        return []
    groups = {}
    for edge_id in relevant:
        groups.setdefault(int(edges["pr_group_no"][edge_id]), []).append({
            "course": edges["from"][edge_id],
            "concurrent": edges["pr_concurrency"][edge_id] == "Y",
            "min_grade": float(edges["pr_grade_min"][edge_id].strip() or "0") / 10.0,
        })
    return [groups[k] for k in sorted(groups)]

def parse_gen_ed(entry):
    codes = list(entry["gen_ed_codes"])
    for token in re.split(r"\s*,\s*|\s+or\s+", entry["gen_ed_display"] or ""):
        token = token.strip()
        if token in gen_ed_tags and token not in codes:
            codes.append(token)
    return codes

def parse_courses(path):
    with open(path) as f:
        courses_blob = json.load(f)["courses"]
    courses = {}
    for course_id, entry in courses_blob.items():
        data = entry["data"]
        mean, variance = gpa_stats(data["gpa_distro"])
        if mean == 0.0 and variance == 0.0:
            continue
        credits = float(str(data["course_credits"]).split("-")[0])
        if credits <= 0:
            continue
        title = data["course_title"]
        number = int(course_id.rsplit(" ", 1)[1])
        if skip_catalog_course(title, number):
            continue
        courses[course_id] = {
            "mean": mean, "variance": variance,
            "credits": credits,
            "offered": {"Sp" if q == "p" else q for q in (data["course_offered"] or "AWSp").replace(".", "").replace("Sp", "p").replace("S", "")},
            "prereqs": prereq_groups(course_id, data["prereq_graph"]),
            "department": data["department_abbrev"],
            "title": title, "number": number,
            "gen_ed": parse_gen_ed(entry),
            "is_gateway": data["is_gateway"],
        }
    return courses

def add_predictions(courses, transcript, course_ids):
    student_subjects = subject_z_scores(transcript, courses)
    for course_id in course_ids:
        course = courses[course_id]
        pred = predict_course(course_id, student_subjects, courses)
        course["predicted_mean"] = pred["mean"]
        course["predicted_variance"] = pred["variance"]
        course["predicted_z"] = pred["predicted_z"]
        course["R2"] = pred["R2"]
    return courses
