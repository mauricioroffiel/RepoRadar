import json
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
        })

    return repos


trending = {}
for period in periods:
    trending[period] = fetchTrending(period)
    print(period + ": " + str(len(trending[period])) + " repos")

with open("trending.json", "w") as file:
    json.dump(trending, file, indent=2, ensure_ascii=False)

print("Saved to trending.json")
