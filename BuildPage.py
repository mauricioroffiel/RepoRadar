import datetime
import html
import json
import os

layers = [
    ("frontend", "Frontend"),
    ("backend", "Backend"),
    ("database", "Database"),
    ("ai", "AI"),
    ("deploy", "Deploy"),
]
tabNames = {"weekly": "Weekly", "monthly": "Monthly"}
gainedLabels = {"weekly": "this week", "monthly": "this month"}


def fileNameFor(repoName):
    return repoName.replace("/", "--")


def loadAnalysis(repoName):
    path = "analysis/" + fileNameFor(repoName) + ".json"
    if not os.path.exists(path):
        return None
    try:
        with open(path) as file:
            return json.load(file)
    except (json.JSONDecodeError, OSError):
        return None


def safe(text):
    return html.escape(str(text or ""))


def formatNumber(number):
    return "{:,}".format(number)


emptyValues = ("—", "-", "", "none", "n/a")


def buildStack(analysis):
    stack = analysis.get("stack", {})
    rows = ""
    for key, label in layers:
        value = (stack.get(key) or "").strip()
        if value.lower() in emptyValues:
            rows += '<div class="layer empty"><dt>' + label + "</dt><dd>None listed</dd></div>"
        else:
            rows += '<div class="layer"><dt>' + label + "</dt><dd>" + safe(value) + "</dd></div>"
    return '<dl class="stack">' + rows + "</dl>"


def buildTags(analysis):
    tags = ""
    for tech in analysis.get("technologies", [])[:8]:
        tags += "<li>" + safe(tech) + "</li>"
    if tags == "":
        return ""
    return '<ul class="tags" aria-label="Key technologies">' + tags + "</ul>"


def withSize(url, size):
    return url + ("&" if "?" in url else "?") + "s=" + str(size)


def buildCreator(repo, owner):
    creator = repo.get("creator") or {"login": owner, "avatar": repo.get("avatar"), "role": "owner"}
    login = creator.get("login") or owner
    avatar = creator.get("avatar") or "https://github.com/" + login + ".png"
    part = '<div class="creator">'
    part += '<img src="' + safe(withSize(avatar, 96)) + '" alt="" width="48" height="48">'
    part += '<div class="creatorText">'
    part += '<a class="creatorName" href="https://github.com/' + safe(login) + '" target="_blank" rel="noopener">' + safe(login) + "</a>"
    if creator.get("role") == "topContributor":
        ownerAvatar = repo.get("avatar") or "https://github.com/" + owner + ".png"
        part += '<span class="creatorRole">Top contributor at '
        part += '<a class="org" href="https://github.com/' + safe(owner) + '" target="_blank" rel="noopener">'
        part += '<img src="' + safe(withSize(ownerAvatar, 40)) + '" alt="" width="16" height="16">' + safe(owner) + "</a></span>"
    else:
        part += '<span class="creatorRole">Created the repo</span>'
    part += "</div></div>"
    return part


def buildCard(position, repo, period):
    analysis = loadAnalysis(repo["name"])
    owner, project = repo["name"].split("/", 1)
    headingId = "repo-" + period + "-" + str(position)

    card = '<article class="repo" aria-labelledby="' + headingId + '">'
    card += '<div class="repoId">'
    card += '<span class="rank num" aria-hidden="true">' + str(position) + "</span>"
    card += '<div class="repoName">'
    card += '<h2 id="' + headingId + '"><a href="' + safe(repo["url"]) + '" target="_blank" rel="noopener">' + safe(project) + "</a></h2>"
    card += '<p class="meta"><span>by ' + safe(owner) + "</span>"
    if repo.get("language"):
        card += "<span>" + safe(repo["language"]) + "</span>"
    card += '<span class="num">' + formatNumber(repo.get("stars", 0)) + " stars</span>"
    card += '<span class="gained num">+' + formatNumber(repo.get("gained", 0)) + " " + gainedLabels[period] + "</span>"
    card += "</p></div>"
    card += buildCreator(repo, owner)
    card += "</div>"

    if analysis is None:
        card += '<div class="repoText"><p>' + safe(repo.get("description")) + "</p>"
        card += '<p class="waiting">Analysis coming in the next run.</p></div>'
    else:
        card += '<div class="repoText">'
        card += '<section><h3>What it solves</h3><p>' + safe(analysis.get("problem")) + "</p></section>"
        card += '<section><h3>What’s new here</h3><p>' + safe(analysis.get("whatsNew")) + "</p></section>"
        card += buildTags(analysis)
        card += "</div>"
        card += '<section class="repoStack"><h3>Stack</h3>' + buildStack(analysis) + "</section>"

    card += "</article>"
    return card


with open("trending.json") as file:
    trending = json.load(file)

tabs = ""
panels = ""
first = True
for period in ["weekly", "monthly"]:
    repos = sorted(trending.get(period, []), key=lambda repo: repo.get("gained", 0), reverse=True)
    selected = "true" if first else "false"
    hidden = "" if first else " hidden"
    tabs += '<button role="tab" id="tab-' + period + '" aria-controls="panel-' + period + '" aria-selected="' + selected + '">' + tabNames[period] + "</button>"
    cards = ""
    position = 1
    for repo in repos:
        cards += buildCard(position, repo, period)
        position = position + 1
    panels += '<section role="tabpanel" id="panel-' + period + '" aria-labelledby="tab-' + period + '" class="repoList"' + hidden + ">" + cards + "</section>"
    first = False

fetchedText = trending.get("fetchedAt")
try:
    fetched = datetime.datetime.fromisoformat(fetchedText)
except (TypeError, ValueError):
    fetched = datetime.datetime.now(datetime.timezone.utc)
fetched = fetched.astimezone(datetime.timezone.utc)
fetchedIso = fetched.isoformat(timespec="seconds").replace("+00:00", "Z")
fetchedAt = fetched.strftime("%B %d, %Y at %H:%M UTC")

with open("Template.html") as file:
    template = file.read()

page = template.replace("{{tabs}}", tabs).replace("{{panels}}", panels).replace("{{fetchedIso}}", fetchedIso).replace("{{fetchedAt}}", fetchedAt)

os.makedirs("docs", exist_ok=True)
with open("docs/index.html", "w") as file:
    file.write(page)

print("Page saved to docs/index.html")
