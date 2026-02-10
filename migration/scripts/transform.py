"""Transform WordPress JSON export into Astro-compatible markdown files."""

import json
import re
import sys
from pathlib import Path

EXPORT_FILE = Path(__file__).parent.parent / "exports" / "recipes.json"
OUTPUT_DIR = Path(__file__).parent.parent.parent / "src" / "content" / "recipes"
PAGES_DIR = Path(__file__).parent.parent.parent / "src" / "content" / "pages"


def strip_wp_blocks(html: str) -> str:
    """Remove WordPress block comments, convert HTML to clean markdown."""
    text = html
    # Strip WP block comments
    text = re.sub(r"<!-- /?wp:\w+.*?-->", "", text, flags=re.DOTALL)
    text = re.sub(r"<!--more-->", "", text)
    text = re.sub(r"<!--End WPRM Recipe-->", "", text)

    # Convert HTML to markdown
    text = re.sub(r"<blockquote.*?>(.*?)</blockquote>", r"> \1", text, flags=re.DOTALL)
    text = re.sub(r'<a\s+href="([^"]*)"[^>]*>(.*?)</a>', r"[\2](\1)", text)
    text = re.sub(r"<strong>(.*?)</strong>", r"**\1**", text)
    text = re.sub(r"<em>(.*?)</em>", r"*\1*", text)
    text = re.sub(r"<p>(.*?)</p>", r"\1\n", text, flags=re.DOTALL)
    text = re.sub(r"<br\s*/?>", "\n", text)
    text = re.sub(r"</?[^>]+>", "", text)

    # Clean up whitespace
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def yaml_escape(val: str) -> str:
    """Escape a string for YAML output."""
    if not val:
        return '""'
    needs_quoting = any(c in val for c in ':"\'{}[]&*?|>!%@`#,')
    needs_quoting = needs_quoting or val.startswith("-") or val.startswith(" ")
    if needs_quoting:
        escaped = val.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'
    return val


def build_frontmatter(post: dict) -> str:
    recipe = post["recipe"]
    title = post["post_title"]
    slug = post["post_slug"]
    date = post["post_date"][:10]

    # Extract description from recipe summary or first line of narrative
    description = strip_wp_blocks(recipe.get("summary", "")).strip()
    if not description:
        narrative = strip_wp_blocks(post["post_content"])
        first_line = narrative.split("\n")[0].strip() if narrative else ""
        description = first_line[:200] if first_line else ""

    # Category — take the first non-Uncategorized category
    category = ""
    for c in post["categories"]:
        if c["slug"] != "uncategorized":
            category = c["name"]
            break

    tags = [t["name"] for t in post["tags"]]

    lines = [
        "---",
        f"title: {yaml_escape(title)}",
        f"slug: {yaml_escape(slug)}",
        f"date: {date}",
        f"description: {yaml_escape(description)}",
        f"category: {yaml_escape(category)}",
    ]

    # Tags as YAML list
    if tags:
        lines.append("tags:")
        for tag in tags:
            lines.append(f"  - {yaml_escape(tag)}")
    else:
        lines.append("tags: []")

    # Times
    prep = int(recipe.get("prep_time") or 0)
    cook = int(recipe.get("cook_time") or 0)
    total = int(recipe.get("total_time") or 0)
    lines.append(f"prepTime: {prep}")
    lines.append(f"cookTime: {cook}")
    lines.append(f"totalTime: {total}")

    # Servings
    servings = recipe.get("servings", "")
    servings_unit = recipe.get("servings_unit", "")
    lines.append(f"servings: {yaml_escape(str(servings))}")
    if servings_unit:
        lines.append(f"servingsUnit: {yaml_escape(servings_unit)}")

    # Ingredients
    has_ingredients = any(ing for group in recipe["ingredients"] for ing in group["ingredients"])
    if has_ingredients:
        lines.append("ingredients:")
        for group in recipe["ingredients"]:
            if group["name"]:
                lines.append(f'  - type: "group_header"')
                lines.append(f"    group: {yaml_escape(group['name'])}")
            for ing in group["ingredients"]:
                lines.append(f'  - type: "ingredient"')
                lines.append(f"    amount: {yaml_escape(str(ing.get('amount', '')))}")
                lines.append(f"    unit: {yaml_escape(str(ing.get('unit', '')))}")
                lines.append(f"    name: {yaml_escape(ing.get('name', ''))}")
                if ing.get("notes"):
                    lines.append(f"    notes: {yaml_escape(ing['notes'])}")
    else:
        lines.append("ingredients: []")

    # Instructions
    has_instructions = any(step for group in recipe["instructions"] for step in group["instructions"])
    if has_instructions:
        lines.append("instructions:")
        for group in recipe["instructions"]:
            if group["name"]:
                lines.append(f'  - type: "group_header"')
                lines.append(f"    group: {yaml_escape(group['name'])}")
            for step in group["instructions"]:
                lines.append(f'  - type: "step"')
                lines.append(f"    text: {yaml_escape(step['text'])}")
    else:
        lines.append("instructions: []")

    lines.append("---")
    return "\n".join(lines)


def build_markdown(post: dict) -> str:
    frontmatter = build_frontmatter(post)
    narrative = strip_wp_blocks(post["post_content"])
    return f"{frontmatter}\n\n{narrative}\n"


def transform_page(page: dict) -> str:
    content = strip_wp_blocks(page["content"])
    lines = [
        "---",
        f"title: {yaml_escape(page['title'])}",
        f"slug: {yaml_escape(page['slug'])}",
        "---",
        "",
        content,
        "",
    ]
    return "\n".join(lines)


def main():
    with open(EXPORT_FILE) as f:
        data = json.load(f)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    PAGES_DIR.mkdir(parents=True, exist_ok=True)

    count = 0
    for post in data["recipes"]:
        if not post["recipe"]:
            print(f"SKIP (no recipe data): {post['post_title']}", file=sys.stderr)
            continue

        slug = post["post_slug"]
        md = build_markdown(post)
        out_path = OUTPUT_DIR / f"{slug}.md"
        out_path.write_text(md)
        count += 1

    # Transform pages (skip Sample Page)
    for page in data["pages"]:
        if page["slug"] == "sample-page":
            continue
        md = transform_page(page)
        out_path = PAGES_DIR / f"{page['slug']}.md"
        out_path.write_text(md)

    print(f"Wrote {count} recipe files to {OUTPUT_DIR}")
    print(f"Wrote pages to {PAGES_DIR}")


if __name__ == "__main__":
    main()
