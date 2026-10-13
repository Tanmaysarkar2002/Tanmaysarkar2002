"""Draw assets/achievements.svg: ride stickers, GitHub-style badges and an odometer
of live GitHub numbers, in the hand-drawn style of tanmaysarkar.dev.

Run daily by .github/workflows/achievements.yml. Locally:
    GITHUB_TOKEN=... python scripts/achievements.py
    python scripts/achievements.py --stats '{"repos": 29, "stars": 0, "top_stars": 0, "merged_prs": 27, "commits": 0, "followers": 5}'
"""
import base64
import datetime
import io
import json
import os
import re
import sys
import urllib.request

from fontTools import subset
from fontTools.ttLib import TTFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "assets", "achievements.svg")
INK, PAPER, PAPER2, ACCENT, SOFT = "#1f1f24", "#f4f1ea", "#fbfaf6", "#ff6b35", "#55565f"
def S(width=2.6):
    return f'stroke="{INK}" stroke-width="{width}" stroke-linecap="round" stroke-linejoin="round"'
TIER_COLORS = {2: "#cd7f32", 3: "#b8bcc4", 4: "#e6b422"}

QUERY = """query($login: String!) {
  user(login: $login) {
    followers { totalCount }
    repositories(ownerAffiliations: OWNER, privacy: PUBLIC, isFork: false, first: 100,
                 orderBy: {field: STARGAZERS, direction: DESC}) {
      totalCount
      nodes { stargazerCount }
    }
    pullRequests(states: MERGED) { totalCount }
    contributionsCollection { totalCommitContributions }
  }
}"""


def fetch_stats(login, token):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": login}}).encode(),
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        body = json.load(r)
    if "errors" in body:
        sys.exit(f"GitHub API error: {body['errors']}")
    u = body["data"]["user"]
    stars = [n["stargazerCount"] for n in u["repositories"]["nodes"]]
    return {
        "repos": u["repositories"]["totalCount"],
        "stars": sum(stars),
        "top_stars": max(stars, default=0),
        "merged_prs": u["pullRequests"]["totalCount"],
        "commits": u["contributionsCollection"]["totalCommitContributions"],
        "followers": u["followers"]["totalCount"],
    }


def tier(value, steps):
    """0 = locked, 1 = earned, 2-4 = x2 (bronze), x3 (silver), x4 (gold)."""
    return sum(value >= s for s in steps)


def font_face(family, path, text):
    opts = subset.Options()
    opts.flavor = "woff2"
    font = TTFont(path)
    sub = subset.Subsetter(opts)
    sub.populate(text=text + " 0123456789")
    sub.subset(font)
    buf = io.BytesIO()
    font.flavor = "woff2"
    font.save(buf)
    b64 = base64.b64encode(buf.getvalue()).decode()
    return f"@font-face{{font-family:'{family}';src:url(data:font/woff2;base64,{b64}) format('woff2');}}"


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# Doodle icons, drawn around (0, 0) and about 50px wide.
ICONS = {
    "star": f'<path d="M0 -24 L7 -8 L24 -7 L11 4 L15 21 L0 12 L-15 21 L-11 4 L-24 -7 L-7 -8 Z" fill="{PAPER2}" {S(2)}/>',
    "shark": f'<path d="M-26 10 Q-6 6 4 -24 Q8 -4 26 10 Z" fill="{PAPER2}" {S(2)}/>'
             f'<path d="M-30 16 q8 -6 15 0 t15 0 t15 0 t15 0" fill="none" {S(2)}/>',
    "bolt": f'<path d="M6 -26 L-14 4 H0 L-6 26 L16 -6 H2 Z" fill="{PAPER2}" {S(2)}/>',
    "yolo": f'<rect x="-20" y="-20" width="40" height="40" rx="8" fill="{PAPER2}" {S(2)}/>'
            f'<circle cx="-9" cy="-9" r="3.4" fill="{INK}"/><circle cx="9" cy="9" r="3.4" fill="{INK}"/><circle r="3.4" fill="{INK}"/>'
            f'<circle cx="9" cy="-9" r="3.4" fill="{INK}"/><circle cx="-9" cy="9" r="3.4" fill="{INK}"/>',
    "pair": f'<circle cx="-10" cy="-8" r="9" fill="{PAPER2}" {S(2)}/><circle cx="11" cy="-8" r="9" fill="{PAPER2}" {S(2)}/>'
            f'<path d="M-24 20 Q-10 2 4 20 M-2 20 Q12 2 26 20" fill="{PAPER2}" {S(2)}/>',
    "brain": f'<path d="M-20 4 Q-26 -14 -10 -20 Q0 -28 10 -20 Q26 -14 20 4 Q22 18 6 18 Q0 24 -6 18 Q-22 18 -20 4 Z" fill="{PAPER2}" {S(2)}/>'
             f'<path d="M0 -20 V16 M-12 -4 q6 4 12 0 M0 4 q6 4 12 0" fill="none" stroke="{INK}" stroke-width="1.6"/>',
}


def sticker(x, y, name, sub, color, icon, level, delay):
    rot = (-6, 4, -3, 5, -4, 3, -5, 4)[int(x) // 148 % 8]
    if level:
        disc = (f'<circle r="46" fill="{color}" {S(3)}/>'
                f'<circle r="38" fill="none" stroke="{INK}" stroke-width="1.4" stroke-dasharray="4 5"/>{ICONS[icon]}')
        cls = "pop"
    else:
        disc = (f'<circle r="46" fill="#d9d6ce" {S(3)} stroke-dasharray="8 6"/>'
                f'<g opacity=".35">{ICONS[icon]}</g>')
        cls = "lock"
    ribbon = ""
    if level >= 2:
        ribbon = (f'<g transform="translate(30 -34) rotate(12)"><rect x="-17" y="-12" width="34" height="24" rx="5" '
                  f'fill="{TIER_COLORS[level]}" {S(2)}/><text x="0" y="6" text-anchor="middle" '
                  f'font-size="16" font-weight="bold">x{level}</text></g>')
    size = 15 if len(name) < 12 else 12.5
    return (f'<g transform="translate({x} {y}) rotate({rot})"><g class="{cls}" style="animation-delay:{delay:.2f}s">'
            f'<g filter="url(#rough)">{disc}</g>{ribbon}'
            f'<text x="0" y="66" text-anchor="middle" font-size="{size}" font-weight="bold">{esc(name)}</text>'
            f'<text x="0" y="83" text-anchor="middle" font-size="13" style="fill:{SOFT}">{esc(sub)}</text></g></g>')


def odometer(x, y, label, value):
    digits = f"{min(value, 99999):05d}"
    cells = "".join(
        f'<rect x="{i*22}" y="0" width="20" height="30" rx="3" fill="{"#2b2b33" if i < 4 else ACCENT}" stroke="{INK}" stroke-width="1.6"/>'
        f'<text class="digit" x="{i*22+10}" y="23" text-anchor="middle" font-size="22" style="fill:#fbfaf6">{d}</text>'
        for i, d in enumerate(digits))
    return (f'<g transform="translate({x} {y})">{cells}'
            f'<text x="54" y="50" text-anchor="middle" font-size="15" style="fill:#e9e6ff">{esc(label)}</text></g>')


def build(cfg, stats):
    W, H = 1200, 560
    manual = cfg["github_manual"]
    shark = tier(stats["merged_prs"], (2, 16, 128, 1024))
    starry = tier(stats["top_stars"], (16, 128, 512, 4096))

    def flag(v):
        return int(v)  # true/false, or a tier number 0-4

    github = [
        ("PULL SHARK", f'{stats["merged_prs"]} PRs merged', "#7fc8f8", "shark", shark),
        ("STARSTRUCK", f'{stats["top_stars"]}/16 stars on a repo' if not starry else f'{stats["top_stars"]} stars on a repo', "#ffd166", "star", starry),
        ("QUICKDRAW", "closed in 5 min", "#ffb3c1", "bolt", flag(manual.get("QUICKDRAW", 0))),
        ("YOLO", "merged, no review", "#b8f2b0", "yolo", flag(manual.get("YOLO", 0))),
        ("PAIR EXTRAORDINAIRE", "co-authored PRs", "#d6c8ff", "pair", flag(manual.get("PAIR EXTRAORDINAIRE", 0))),
        ("GALAXY BRAIN", "answers accepted", "#ffd29a", "brain", flag(manual.get("GALAXY BRAIN", 0))),
    ]
    ride = [(n, d, c, "star", 1) for n, d, c in cfg["ride"]] + [("???", "find it on the site", "", "star", 0)] * 2
    earned_gh = sum(1 for g in github if g[4])

    row1 = "".join(sticker(80 + i * 148, 150, *s, i * 0.25) for i, s in enumerate(ride))
    row2 = "".join(sticker(150 + i * 180, 330, *s, i * 0.3) for i, s in enumerate(github))
    year = datetime.date.today().year
    odo = "".join(odometer(160 + i * 190, 466, l, v) for i, (l, v) in enumerate([
        ("public repos", stats["repos"]), ("stars earned", stats["stars"]), ("PRs merged", stats["merged_prs"]),
        (f"commits in {year}", stats["commits"]), ("followers", stats["followers"])]))

    body = f'''<rect width="{W}" height="{H}" fill="{PAPER}"/>
<rect width="{W}" height="{H}" fill="#ffc9a8" opacity=".25"/>
<text class="sk" x="30" y="48" font-size="32">Achievements unlocked</text>
<text x="1170" y="44" text-anchor="end" font-size="19" style="fill:{SOFT}">the rest of the ride stickers are hidden on tanmaysarkar.dev</text>
<text x="30" y="86" font-size="20" style="fill:{SOFT}">on the road · 6 / 18</text>
<path d="M30 94 H200" stroke="{ACCENT}" stroke-width="2.4" stroke-linecap="round"/>
{row1}
<text x="30" y="266" font-size="20" style="fill:{SOFT}">on GitHub · {earned_gh} / {len(github)}</text>
<path d="M30 274 H200" stroke="{ACCENT}" stroke-width="2.4" stroke-linecap="round"/>
{row2}
<g filter="url(#rough)"><rect x="20" y="440" width="{W-40}" height="104" rx="14" fill="#2c3470" {S()}/></g>
<text class="sk" x="44" y="478" font-size="22" style="fill:#ffd166">ODO</text>
<text x="44" y="502" font-size="13" style="fill:#e9e6ff">refuelled</text>
<text x="44" y="520" font-size="13" style="fill:#e9e6ff">daily</text>
{odo}
<rect width="{W}" height="{H}" filter="url(#grain)" opacity=".5"/>
<rect x="1.5" y="1.5" width="{W-3}" height="{H-3}" rx="10" fill="none" stroke="{INK}" stroke-width="3"/>'''

    texts = "".join(re.findall(r">([^<>]+)</text>", body)).replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")
    sketch = "".join(re.findall(r'class="sk"[^>]*>([^<]+)<', body))
    fonts = (font_face("Sketch", os.path.join(HERE, "fonts", "cabin-sketch-latin-700-normal.woff2"), sketch)
             + font_face("Hand", os.path.join(HERE, "fonts", "patrick-hand-latin-400-normal.woff2"), texts))
    label = (f"Achievements. On the road: {', '.join(n for n, *_ in cfg['ride'])}. "
             f"On GitHub: {', '.join(n.title() + (f' x{l}' if l > 1 else '') for n, _, _, _, l in github if l) or 'none yet'}. "
             f"{stats['repos']} public repos, {stats['stars']} stars, {stats['merged_prs']} PRs merged, "
             f"{stats['commits']} commits in {year}, {stats['followers']} followers.")
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="{esc(label)}">
<title>{esc(label)}</title>
<style>{fonts}
text{{font-family:Hand,'Comic Sans MS',cursive;fill:{INK}}}
.sk{{font-family:Sketch,Hand,cursive}}
.pop{{animation:pop 6s ease-in-out infinite}}
.lock{{animation:wob 4s ease-in-out infinite}}
.digit{{animation:roll .6s ease-out both}}
@keyframes pop{{0%{{transform:scale(1)}}4%{{transform:scale(1.12)}}8%,100%{{transform:scale(1)}}}}
@keyframes wob{{0%,90%{{transform:rotate(0)}}93%{{transform:rotate(-6deg)}}96%{{transform:rotate(6deg)}}100%{{transform:rotate(0)}}}}
@keyframes roll{{from{{transform:translateY(-14px);opacity:0}}}}
@media (prefers-reduced-motion:reduce){{*{{animation:none!important}}}}</style>
<defs>
<filter id="rough" x="-5%" y="-5%" width="110%" height="110%"><feTurbulence type="fractalNoise" baseFrequency="0.03" numOctaves="2" seed="4"/><feDisplacementMap in="SourceGraphic" scale="3"/></filter>
<filter id="grain"><feTurbulence type="fractalNoise" baseFrequency=".9" numOctaves="2" stitchTiles="stitch"/><feColorMatrix values="0 0 0 0 .3  0 0 0 0 .28  0 0 0 0 .25  0 0 0 .2 0"/></filter>
</defs>
{body}
</svg>
'''


def main():
    cfg = json.load(open(os.path.join(HERE, "achievements.json")))
    if len(sys.argv) == 3 and sys.argv[1] == "--stats":
        stats = json.loads(sys.argv[2])
    else:
        token = os.environ.get("GITHUB_TOKEN")
        if not token:
            sys.exit("Set GITHUB_TOKEN, or pass --stats '<json>'.")
        stats = fetch_stats(cfg["login"], token)
    print(json.dumps(stats))
    with open(OUT, "w") as f:
        f.write(build(cfg, stats))


if __name__ == "__main__":
    main()
