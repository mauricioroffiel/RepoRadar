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


def buildStack(analysis):
    stack = analysis.get("stack", {})
    rows = ""
    for key, label in layers:
        value = stack.get(key) or "—"
        emptyClass = " empty" if value.strip() in ("—", "-", "", "None", "none") else ""
        rows += '<div class="layer' + emptyClass + '"><dt>' + label + "</dt><dd>" + safe(value) + "</dd></div>"
    return '<dl class="stack">' + rows + "</dl>"


def buildChips(analysis):
    chips = ""
    for tech in analysis.get("technologies", [])[:8]:
        chips += '<li>' + safe(tech) + "</li>"
    if chips == "":
        return ""
    return '<ul class="chips">' + chips + "</ul>"


def buildCard(position, repo, period):
    analysis = loadAnalysis(repo["name"])
    owner, project = repo["name"].split("/", 1)

    card = '<article class="card">'
    card += '<header class="cardHead">'
    card += '<span class="rank">' + str(position) + "</span>"
    avatarUrl = "https://github.com/" + owner + ".png?size=96"
    card += '<a class="avatar" href="https://github.com/' + safe(owner) + '" target="_blank" rel="noopener">'
    card += '<img src="' + safe(avatarUrl) + '" alt="' + safe(owner) + '" width="40" height="40" loading="lazy"></a>'
    card += '<div class="title"><a href="' + safe(repo["url"]) + '" target="_blank" rel="noopener">'
    card += '<span class="owner">' + safe(owner) + ' /</span> <span class="project">' + safe(project) + "</span></a>"
    card += '<div class="meta">'
    if repo.get("language"):
        card += '<span>' + safe(repo["language"]) + "</span>"
    card += '<span>★ ' + formatNumber(repo.get("stars", 0)) + "</span>"
    card += '<span class="gained">+' + formatNumber(repo.get("gained", 0)) + " " + gainedLabels[period] + "</span>"
    card += "</div></div></header>"

    if analysis is None:
        card += '<p class="description">' + safe(repo.get("description")) + "</p>"
        card += '<p class="waiting">Analysis coming in the next run.</p>'
    else:
        card += '<section><h3>What it solves</h3><p>' + safe(analysis.get("problem")) + "</p></section>"
        card += '<section><h3>Stack</h3>' + buildStack(analysis) + "</section>"
        card += '<section class="new"><h3>What\'s new here</h3><p>' + safe(analysis.get("whatsNew")) + "</p></section>"
        card += buildChips(analysis)

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
    panels += '<section role="tabpanel" id="panel-' + period + '" aria-labelledby="tab-' + period + '" class="grid"' + hidden + ">" + cards + "</section>"
    first = False

updated = datetime.datetime.now(datetime.timezone.utc).strftime("%B %d, %Y")

with open("Template.html") as file:
    template = file.read()

page = template.replace("{{tabs}}", tabs).replace("{{panels}}", panels).replace("{{updated}}", updated)

os.makedirs("docs", exist_ok=True)
with open("docs/index.html", "w") as file:
    file.write(page)

print("Page saved to docs/index.html")
