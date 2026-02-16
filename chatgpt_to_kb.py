import json
import re
from pathlib import Path
from slugify import slugify
from collections import defaultdict

INPUT = "conversations.json"
OUT = Path("knowledge-base")
OUT.mkdir(exist_ok=True)

# ---------------------------
# Topic classifier (rule + keyword hybrid)
# ---------------------------

TOPIC_RULES = {
    "system-design": [
        "microservice", "scaling", "kafka", "k8s", "docker",
        "architecture", "api gateway", "load balancer", "database design",
        "high level design", "low level design", "distributed system"
    ],

    "dsa": [
        "dfs", "bfs", "dp", "dynamic programming", "graph",
        "tree", "leetcode", "complexity", "time complexity",
        "flood fill", "union find", "recursion"
    ],

    "machine-learning": [
        "pca", "regression", "model", "training", "accuracy",
        "overfitting", "cnn", "transformer", "feature selection"
    ],

    "career": [
        "promotion", "manager", "review", "leadership",
        "communication", "meeting", "behavioral"
    ],

    "finance": [
        "loan", "interest", "emi", "repo rate", "bank",
        "investment", "tax", "home loan"
    ],

    "programming": [
        "python", "java", "angular", "react", "bug",
        "error", "compile", "syntax", "api", "backend"
    ],
}


def detect_topic(text: str):
    text = text.lower()
    scores = defaultdict(int)

    for topic, keywords in TOPIC_RULES.items():
        for kw in keywords:
            if kw in text:
                scores[topic] += 1

    if not scores:
        return "general"

    return max(scores, key=scores.get)


def extract_tags(text):
    words = set(re.findall(r"[a-zA-Z]{4,}", text.lower()))
    return list(sorted(words))[:8]


# ---------------------------
# Load conversations
# ---------------------------

with open(INPUT, "r", encoding="utf-8") as f:
    data = json.load(f)

index = defaultdict(list)

for convo in data:
    title = convo.get("title", "untitled")
    mapping = convo.get("mapping", {})

    ordered = sorted(mapping.items(), key=lambda x: x[1].get("create_time", 0))

    full_text = ""
    md_lines = []

    for _, node in ordered:
        msg = node.get("message")
        if not msg:
            continue

        role = msg["author"]["role"]
        parts = msg["content"].get("parts", [])
        content = "\n".join(parts)

        full_text += " " + content

        if role == "user":
            md_lines.append("## 👤 User\n")
        else:
            md_lines.append("## 🤖 Assistant\n")

        md_lines.append(content + "\n")

    # -------- classify --------
    topic = detect_topic(full_text)
    tags = extract_tags(full_text)

    folder = OUT / topic
    folder.mkdir(exist_ok=True)

    filename = slugify(title)[:80] + ".md"
    filepath = folder / filename

    # -------- front matter --------
    frontmatter = [
        "---",
        f"title: {title}",
        f"topic: {topic}",
        f"tags: {', '.join(tags)}",
        "---\n"
    ]

    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(frontmatter + md_lines))

    index[topic].append((title, filepath.relative_to(OUT)))

# ---------------------------
# Build README
# ---------------------------

readme = ["# 📚 ChatGPT Knowledge Base\n"]

for topic in sorted(index.keys()):
    readme.append(f"\n## {topic}\n")
    for title, path in sorted(index[topic]):
        readme.append(f"- [{title}]({path})")

with open(OUT / "README.md", "w", encoding="utf-8") as f:
    f.write("\n".join(readme))

print("✅ Knowledge base created!")
