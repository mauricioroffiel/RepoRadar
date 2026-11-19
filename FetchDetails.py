import json
import os
import re
import requests

maxReadmeChars = 4000
maxDependencyChars = 2000
maxTreePaths = 120
dependencyFiles = [
    "package.json",
    "requirements.txt",
    "pyproject.toml",
    "Cargo.toml",
    "go.mod",
    "Gemfile",
    "pom.xml",
    "build.gradle",
    "composer.json",
    "Dockerfile",
    "docker-compose.yml",
]

token = os.environ.get("GITHUB_TOKEN", "")
headers = {"User-Agent": "RepoRadar", "Accept": "application/vnd.github+json"}
if token != "":
    headers["Authorization"] = "Bearer " + token


def fileNameFor(repoName):
    return repoName.replace("/", "--")


def getJson(url):
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return None
    return response.json()


def getText(url):
    response = requests.get(url, headers={"User-Agent": "RepoRadar"})
    if response.status_code != 200:
        return ""
    return response.text


def cleanReadme(text):
    # Drop badges, images and HTML tags so the size limit keeps real prose
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
    text = re.sub(r"\[!\[[^\]]*\]\([^)]*\)\]\([^)]*\)", "", text)
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"&nbsp;|&#32;", " ", text)
    text = "\n".join(line.rstrip() for line in text.splitlines())
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def shorten(text, limit):
    if len(text) <= limit:
        return text
    return text[:limit] + "\n...(cut)"


def collectDetails(repo):
    name = repo["name"]
    info = getJson("https://api.github.com/repos/" + name)
    if info is None:
        print("Could not read " + name)
        return None

    branch = info.get("default_branch", "main")
    rawBase = "https://raw.githubusercontent.com/" + name + "/" + branch + "/"

    tree = getJson("https://api.github.com/repos/" + name + "/git/trees/" + branch + "?recursive=1")
    paths = []
    if tree is not None:
        for item in tree.get("tree", []):
            if item["path"].count("/") <= 1:
                paths.append(item["path"])
    rootFiles = [path for path in paths if "/" not in path]

    readme = ""
    readmeInfo = getJson("https://api.github.com/repos/" + name + "/readme")
    if readmeInfo is not None and readmeInfo.get("download_url"):
        readme = cleanReadme(getText(readmeInfo["download_url"]))

    lines = []
    lines.append("# " + name)
    lines.append("")
    lines.append("URL: " + repo["url"])
    lines.append("Description: " + repo.get("description", ""))
    lines.append("Main language: " + repo.get("language", ""))
    lines.append("Topics: " + ", ".join(info.get("topics", [])))
    lines.append("Homepage: " + str(info.get("homepage") or ""))
    lines.append("")
    lines.append("## File tree (first two levels)")
    lines.append("\n".join(paths[:maxTreePaths]))
    lines.append("")

    for dependencyFile in dependencyFiles:
        if dependencyFile in rootFiles:
            content = getText(rawBase + dependencyFile)
            lines.append("## " + dependencyFile)
            lines.append(shorten(content, maxDependencyChars))
            lines.append("")

    lines.append("## README")
    lines.append(shorten(readme, maxReadmeChars))
    return "\n".join(lines)


with open("trending.json") as file:
    trending = json.load(file)

allRepos = {}
for period in trending:
    for repo in trending[period]:
        allRepos[repo["name"]] = repo

os.makedirs("analysis", exist_ok=True)
os.makedirs("pending", exist_ok=True)

newCount = 0
for name in allRepos:
    fileName = fileNameFor(name)
    if os.path.exists("analysis/" + fileName + ".json"):
        continue
    details = collectDetails(allRepos[name])
    if details is None:
        continue
    with open("pending/" + fileName + ".md", "w") as file:
        file.write(details)
    newCount = newCount + 1

print(str(newCount) + " new repos to analyze")
