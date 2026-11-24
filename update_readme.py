import os
import re
import requests

USERNAME = "rahul-gupta-2004"
TOKEN = os.getenv("GITHUB_TOKEN")
HEADERS = {"Authorization": f"token {TOKEN}"} if TOKEN else {}
TOP_N = 6

def get_repos():
    repos = []
    page = 1
    while True:
        url = f"https://api.github.com/users/{USERNAME}/repos?per_page=100&page={page}&type=owner"
        res = requests.get(url, headers=HEADERS)
        res.raise_for_status()
        data = res.json()
        if not data:
            break
        repos.extend(data)
        page += 1
    return repos

def score_repo(repo):
    # Skip profile repo and forks
    if repo["name"].lower() == USERNAME.lower() or repo["fork"]:
        return None

    # Fetch all languages detected in the repo
    lang_res = requests.get(repo["languages_url"], headers=HEADERS)
    languages = list(lang_res.json().keys()) if lang_res.status_code == 200 else []
    topics = repo.get("topics", [])

    # Merge unique languages and formatted topics into a clean tech stack list
    seen = set()
    stack = []
    for item in languages + [t.replace("-", " ").title() for t in topics]:
        key = item.lower()
        if key not in seen:
            seen.add(key)
            stack.append(item)

    return {
        "name": repo["name"],
        "url": repo["html_url"],
        "description": repo["description"] or "No description provided.",
        "stack": stack,
        "stack_count": len(stack),
        "updated_at": repo["pushed_at"],
    }

def main():
    scored = []
    for repo in get_repos():
        info = score_repo(repo)
        if info and info["stack_count"] > 0:
            scored.append(info)

    # Sort by largest tech stack count first, then most recently pushed
    scored.sort(key=lambda r: (r["stack_count"], r["updated_at"]), reverse=True)
    top_repos = scored[:TOP_N]

    lines = []
    for r in top_repos:
        tech_badges = ", ".join(f"`{tech}`" for tech in r["stack"][:6])
        lines.append(f"* [**{r['name']}**]({r['url']}) — {r['description']} ({tech_badges})")

    new_block = "\n".join(lines) if lines else "*No public repositories found.*"

    with open("README.md", "r", encoding="utf-8") as f:
        readme = f.read()

    updated_readme = re.sub(
        r"<!-- AUTO-REPOS:START -->.*?<!-- AUTO-REPOS:END -->",
        f"<!-- AUTO-REPOS:START -->\n{new_block}\n<!-- AUTO-REPOS:END -->",
        readme,
        flags=re.DOTALL,
    )

    with open("README.md", "w", encoding="utf-8") as f:
        f.write(updated_readme)

if __name__ == "__main__":
    main()
