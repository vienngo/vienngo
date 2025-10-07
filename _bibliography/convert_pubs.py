import os
import bibtexparser
import yaml
from datetime import datetime

# --- CONFIG ---
BIB_FILE = "vien_dblp_pubs.bib"
OUTPUT_DIR = "_publications"
DEFAULT_MONTH = "01"
DEFAULT_DAY = "01"

# --- UTILITIES ---
def safe_filename(s):
    """Clean strings to create safe filenames."""
    return "".join(c if c.isalnum() or c in "-_" else "_" for c in s)[:80]


def is_patent(entry):
    """Check whether this entry looks like a patent."""
    entrytype = entry.get("ENTRYTYPE", "").lower()
    title = entry.get("title", "").lower()
    howpublished = entry.get("howpublished", "").lower()
    note = entry.get("note", "").lower()

    # Common heuristics for patents
    if "patent" in entrytype:
        return True
    if "patent" in title or "pat." in title:
        return True
    if "patent" in howpublished or "patent" in note:
        return True
    return False


def is_arxiv(entry):
    journal = entry.get("journal") or entry.get("booktitle") or ""
    # Common heuristics for patents
    if "CoRR" in journal:
        return True

    return False


# --- MAIN CONVERSION ---
def bib_to_markdown():
    with open(BIB_FILE, encoding="utf-8") as bibtex_file:
        bib_db = bibtexparser.load(bibtex_file)

    count = 0
    skipped = 0

    for entry in bib_db.entries:
        if is_patent(entry):
            print(f"🚫 Skipped patent: {entry.get('title', 'Unknown Title')}")
            skipped += 1
            continue

        if is_arxiv(entry):
            print(f"🚫 Skipped arxiv pub: {entry.get('title', 'Unknown Title')}")
            skipped += 1
            continue

        title = entry.get("title", "").strip("{}")
        year = entry.get("year", "9999")
        month = entry.get("month", DEFAULT_MONTH)
        day = entry.get("day", DEFAULT_DAY)
        date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"

        authors = [
            a.strip()
            for a in entry.get("author", "")
            .replace(" and ", "; ")
            .split("; ")
            if a.strip()
        ]

        journal = entry.get("journal") or entry.get("booktitle") or ""
        doi = entry.get("doi", "")
        url = entry.get("url", "")
        pdf = entry.get("pdf", "")

        links = []
        if pdf:
            links.append(["PDF", {"url": pdf, "target": "_blank"}])
        if doi:
            links.append(["DOI", f"https://doi.org/{doi}"])
        if url and not any(url in l[1] for l in links):
            links.append(["Link", url])

        front_matter = {
            "title": title,
            "date": date,
            "authors": authors,
            "pub": journal,
        }
        if links:
            front_matter["links"] = links

        year_dir = os.path.join(OUTPUT_DIR, year)
        os.makedirs(year_dir, exist_ok=True)

        filename = safe_filename(entry.get("ID", title.lower().replace(" ", "_")))
        md_path = os.path.join(year_dir, f"{filename}.md")

        with open(md_path, "w", encoding="utf-8") as f:
            f.write("---\n")
            yaml.safe_dump(front_matter, f, sort_keys=False, allow_unicode=True)
            f.write("---\n")
            if "abstract" in entry:
                f.write(entry["abstract"].strip() + "\n")

        print(f"✅ Saved: {md_path}")
        count += 1

    print(f"\n🎯 Completed! Saved {count} publications. Skipped {skipped} patents or arxiv.")


if __name__ == "__main__":
    print(f"Converting {BIB_FILE} → Markdown in {OUTPUT_DIR}/...")
    bib_to_markdown()
    print("🎉 Done!")
