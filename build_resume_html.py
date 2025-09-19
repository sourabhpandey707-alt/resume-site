#!/usr/bin/env python3
# build_resume_html.py
# Generates an IIM-BG–style resume as HTML for GitHub Pages hosting.

import os, re, json, csv, argparse
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from jinja2 import Environment, FileSystemLoader

# 1) DEFAULT PROFILE (pre-filled)
DEFAULT_PROFILE = {
    "name": "Sourabh Pandey",
    "program": "MBA-HHM",
    "batch": "2025–2027",
    "email": "sourabh.p2027h@iimbg.ac.in",
    "phone": "+91-8103867459",
    "address": "Indian Institute of Management Bodhgaya, Bihar",
    "education": [
        {"degree":"MBA-HHM","institute":"IIM Bodhgaya","cgpa":"","year":"2027"},
        {"degree":"B.Com","institute":"J.H. P.G. College, Betul","cgpa":"68.7%","year":"2024"},
        {"degree":"XII","institute":"Little Flower Senior Secondary School, Betul","cgpa":"78.4%","year":"2021"},
        {"degree":"X","institute":"Little Flower Senior Secondary School, Betul","cgpa":"80.83%","year":"2019"},
    ],
    "por":[
        "Project Group Leader — Led a team of 5 through the project lifecycle (2022).",
        "Consolidated findings into a cohesive report and presentation (2022).",
        "Ensured timely, high-quality submission of deliverables (2022)."
    ],
    "achievements":[
        "Cleared SBI Clerk Prelims; 92+ percentile in General English (2025).",
        "HDFC Bank Survey: Proposed 5 improvements boosting NPS by 12% (2021).",
        "Comparative Financial Analysis: Benchmarked HDFC’s capital adequacy vs peers (2023)."
    ],
    "activities":[
        "Chess: Gold medalist in District Championship (2022).",
        "Vice-Captain, College Chess Team; 4th place at State-Level Tournament (2022).",
        "Represented university at National Level Chess; ranked 24/83 (2022)."
    ],
    "interests":["Badminton","Swimming","Reading Books"]
}

# 2) Parse Coursera CSV (fallback)
def parse_coursera_csv(path):
    total, comps = 0.0, []
    if Path(path).exists():
        with open(path, encoding='utf-8') as f:
            for r in csv.DictReader(f):
                hrs = float(r.get('Hours') or 0)
                total += hrs
                if r.get('Status','').lower() in ('completed','passed','certificate earned'):
                    dt=None
                    for fmt in ('%Y-%m-%d','%d-%m-%Y','%d/%m/%Y'):
                        try: dt=datetime.strptime(r.get('Completion Date','')[:10],fmt); break
                        except: pass
                    comps.append({
                        "title": r.get('Course Name',''),
                        "provider":"Coursera",
                        "hours": round(hrs,1),
                        "completed_at": dt,
                        "completed_at_display": dt.strftime('%d %b %Y') if dt else ''
                    })
    comps.sort(key=lambda x: x['completed_at'] or datetime.min, reverse=True)
    return round(total,1), comps

# 3) Fetch Coursera via API
def fetch_coursera_api(token):
    url = "https://api.coursera.org/api/onDemandEnrollments.v1?q=me&fields=courseName,workload,completionDate,slug"
    hdr = {"Authorization":f"Bearer {token}"}
    resp = requests.get(url, headers=hdr, timeout=30); resp.raise_for_status()
    certs=[]
    for e in resp.json().get('elements',[]):
        if e.get('completionDate'):
            certs.append({
                "title": e['courseName'],
                "provider": "Coursera",
                "hours": e.get('workload'),
                "url": f"https://www.coursera.org/learn/{e['slug']}"
            })
    return certs

# 4) Load external courses JSON
def fetch_external(path):
    out=[]
    if Path(path).exists():
        for itm in json.loads(Path(path).read_text()):
            out.append({
                "title": itm.get('title',''),
                "provider": itm.get('provider',''),
                "hours": itm.get('estimated_hours',0),
                "status": itm.get('status','in-progress'),
                "url": itm.get('url','')
            })
    return out

# 5) Render HTML with Jinja2
def render_html(profile, total_hours, completed, external, certifications, out_dir):
    env = Environment(loader=FileSystemLoader(str(Path(__file__).parent)), autoescape=True)
    tpl = env.get_template('resume_template.html')
    html = tpl.render(
        profile=profile,
        total_hours=total_hours,
        completed=completed,
        external=external,
        certifications=certifications
    )
    Path(out_dir).mkdir(parents=True,exist_ok=True)
    Path(out_dir,'index.html').write_text(html,encoding='utf-8')

# 6) Main
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--coursera-token', help='Coursera API token')
    ap.add_argument('--csv', default='data/coursera_export.csv')
    ap.add_argument('--external', default='data/external_courses.json')
    ap.add_argument('--out', default='docs')
    args=ap.parse_args()

    profile=DEFAULT_PROFILE
    total_csv, recent_csv = parse_coursera_csv(args.csv)

    completed=[]
    if args.coursera_token:
        completed += fetch_coursera_api(args.coursera_token)
    else:
        completed += recent_csv

    external = fetch_external(args.external)
    certs = completed + [e for e in external if e['status']=='completed']

    render_html(profile, total_csv, completed, external, certs, args.out)
    print(f"Generated HTML resume at {args.out}/index.html")

if __name__=='__main__':
    main()
