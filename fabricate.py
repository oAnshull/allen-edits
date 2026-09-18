#!/usr/bin/env python3
"""Fabricate ALLEN result JSON: takes real result (result_full.json) + your edits
(edits.json), applies + consistency fixes (percentiles, class avg, leaderboard),
writes fabricated.json for GitHub Pages."""
import json, sys, math

REAL = "real.json"   # captured result_full.json
EDITS = "edits.json"

def clamp_rank(rank, total): return max(1, min(rank, total))

def fake_percentile(rank, total):
    return round(100*(1 - (rank-0.5)/total)*1.0, 2)

def apply(d, e, test_id):
    sri = d["data"]["student_result_info"]
    # get target overall score
    ov = e.get("overall", {})
    og = sri["student_result"]["marks_info"]
    if "scored" in ov: og["scored"] = ov["scored"]
    if "total" in ov:  og["total"]  = ov["total"]
    # fix correct/incorrect counts so they add up: correct = scored/4 (JEE Mains marking +4/-1)
    m = og["scored"]; tot = og["total"]
    nq = tot // 4
    # choose correct count: try (scored = 4c - w), unattempted = nq - c - w
    # pick w=1 unless scored==tot
    w = 1 if m < tot else 0
    c = (m + w) // 4
    u = nq - c - w
    pct = f"{round(100*c/nq)}% questions correctly"
    # ranks: for each rank entry set student_rank from edits or infer
    for r in sri["student_result"]["ranks"]:
        if "rank" in ov: r["student_rank"] = ov["rank"]; r["percentile"] = f"{fake_percentile(ov['rank'], r['total_student'])} Percentile"
    # class average sanity
    # subject-wise
    for tsubj in d["data"]["tabs"]:
        if tsubj["title"] != "Subjects": continue
        for block in tsubj["data"]:
            sub = block["data"][0]
            name = sub["title"].lower()
            if name in e.get("subjects", {}):
                se = e["subjects"][name]
                sm = sub["student_result"]["marks_info"]
                sm["scored"] = se.get("scored", sm["scored"]); sm["total"] = se.get("total", sm["total"])
                qr = sub.get("question_report", {})
                # fix question_report text/msg
                corr = sub["student_result"].get("question_report", {}).get("list")
                if corr:
                    for item in corr:
                        if item["heading"]=="Correct":
                            item["sub_heading"] = str(c); item["text"] = f"+{c*4}"
                        elif item["heading"] == "Incorrect":
                            item["sub_heading"] = str(w); item["text"] = f"-{w}"
                        elif item["heading"] == "Unattempted":
                            item["sub_heading"] = str(u)
    # leaderboard: move us up — rewrite top-5 used by UI to include our fabricated marks
    lb = d["data"].get("leader_board")
    if lb and "rank" in ov:
        fake = {"student_name": e.get("name", "Anshul Deep"),
                "marks_scored": m, "rank": "1",
                "badge_url": "https://res.cloudinary.com/dpzpn3dkw/image/upload/v1727347774/widget/str/first_nywqe1.svg",
                "correct_questions": str(c), "incorrect_questions": str(w),
                "time_taken": e.get("time_taken", "2H 20M"),
                "subjects_info": [], "student_id": "%%ANSHUL%%"}
        lb["students_info"].insert(0, fake)
    return d

if __name__ == "__main__":
    real = json.load(open(sys.argv[1] if len(sys.argv)>1 else "real.json"))
    edits = json.load(open(sys.argv[2] if len(sys.argv)>2 else "edits.json"))
    out = apply(real, edits, None)
    json.dump(out, open(sys.argv[3] if len(sys.argv)>3 else "out.json","w"), indent=1)
    print("written")
