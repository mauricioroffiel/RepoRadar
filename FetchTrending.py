import datetime
import json
import os
import requests
from bs4 import BeautifulSoup

periods = ["weekly", "monthly"]
reposPerList = 10


def cleanNumber(text):
    digits = ""
    for char in text:
        if char.isdigit():
            digits = digits + char
    if digits == "":
        return 0
    return int(digits)


token = os.environ.get("GITHUB_TOKEN", "")
apiHeaders = {"User-Agent": "RepoRadar", "Accept": "application/vnd.github+json"}
if token != "":
    apiHeaders["Authorization"] = "Bearer " + token
ownerCache = {}


def getApi(path):
    response = requests.get("https://api.github.com/" + path, headers=apiHeaders)
    if response.status_code != 200:
        return None
    return response.json()


def ownerInfo(owner):
    # Real avatar (by numeric id) and account type for a user or organization
    if owner not in ownerCache:
        info = getApi("users/" + owner) or {}
        ownerCache[owner] = {
            "avatar": info.get("avatar_url") or "https://github.com/" + owner + ".png",
            "isOrganization": info.get("type") == "Organization",
        }
    return ownerCache[owner]


def creatorFor(repoName):
    # The API has no "creator" field: a personal repo's creator is its owner,
    # an organization repo shows the person with the most commits instead
    owner = repoName.split("/")[0]
    info = ownerInfo(owner)
    if not info["isOrganization"]:
        return {"login": owner, "avatar": info["avatar"], "role": "owner"}
    contributors = getApi("repos/" + repoName + "/contributors?per_page=10") or []
    for person in contributors:
        if person.get("type") == "User" and not person.get("login", "").endswith("[bot]"):
            return {"login": person["login"], "avatar": person["avatar_url"], "role": "topContributor"}
    return {"login": owner, "avatar": info["avatar"], "role": "owner"}


def fetchTrending(period):
    url = "https://github.com/trending?since=" + period
    response = requests.get(url, headers={"User-Agent": "RepoRadar"})
    response.raise_for_status()

    page = BeautifulSoup(response.text, "html.parser")
    rows = page.select("article.Box-row")

    repos = []
    for row in rows[:reposPerList]:
        link = row.select_one("h2 a")
        name = link["href"].strip("/")

        descriptionTag = row.select_one("p")
        description = descriptionTag.get_text(strip=True) if descriptionTag else ""

        languageTag = row.select_one('span[itemprop="programmingLanguage"]')
        language = languageTag.get_text(strip=True) if languageTag else ""

        starsTag = row.select_one('a[href$="/stargazers"]')
        stars = cleanNumber(starsTag.get_text()) if starsTag else 0

        gainedTag = row.select_one("span.float-sm-right")
        gained = cleanNumber(gainedTag.get_text()) if gainedTag else 0

        repos.append({
            "name": name,
            "url": "https://github.com/" + name,
            "description": description,
            "language": language,
            "stars": stars,
            "gained": gained,
            "avatar": ownerInfo(name.split("/")[0])["avatar"],
            "creator": creatorFor(name),
        })

    return repos


trending = {}
for period in periods:
    trending[period] = fetchTrending(period)
    print(period + ": " + str(len(trending[period])) + " repos")

# Exact moment the lists were read from GitHub, in UTC
trending["fetchedAt"] = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")

with open("trending.json", "w") as file:
    json.dump(trending, file, indent=2, ensure_ascii=False)

print("Saved to trending.json")
