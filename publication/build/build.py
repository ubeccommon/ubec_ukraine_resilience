#!/usr/bin/env python3
"""
Build the publication outputs from Markdown sources and numbers.yaml.

  paper/paper.md, brief/brief.md, essay/essay.md,
  dispatch/four_carpathians.md                    -> build/out/<name>.pdf, .html, .md
  data_package/ (README, ATTRIBUTION, LICENSE, CITATION.cff, licenses/)
                                                  -> build/out/data_package/
  report                                          -> build/report.md

Steps
  1. Read numbers.yaml (flat `key: "value"  # comment` lines; no PyYAML needed).
  2. Strip HTML comments from Markdown sources.
  3. Replace {{key}} with its value. Keys whose value is PENDING, and unknown
     keys, are marked visibly.
  4. Count [[PENDING …]], [[CHECK …]], [[FIELD NOTE …]] markers per file and
     write build/report.md.
  5. Draft mode (default): markers are highlighted in red in PDF and HTML.
     Release mode (--release): stops if any marker, PENDING value or unknown
     key remains.

Usage (from anywhere):
  python publication/build/build.py                  # draft, all outputs
  python publication/build/build.py --only paper     # one document
  python publication/build/build.py --no-pdf         # HTML + Markdown only
  python publication/build/build.py --pdf-engine weasyprint
  python publication/build/build.py --release        # fails on any placeholder

Requires: pandoc >= 3, and xelatex (default) or weasyprint for PDF.
"""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

PUB = Path(__file__).resolve().parent.parent          # publication/
BUILD = PUB / "build"
OUT = BUILD / "out"
AUX = BUILD / "aux"
NUMBERS = PUB / "numbers.yaml"

DOCS = {
    "paper": PUB / "paper" / "paper.md",
    "brief": PUB / "brief" / "brief.md",
    "essay": PUB / "essay" / "essay.md",
    "carpathians": PUB / "dispatch" / "four_carpathians.md",
}
DATA_PACKAGE_FILES = ["README.md", "ATTRIBUTION.md", "LICENSE.md", "CITATION.cff"]
PDF_OPTIONS = {
    "paper": {"toc": True, "fontsize": "11pt"},
    "brief": {"toc": False, "fontsize": "10pt"},
    "essay": {"toc": False, "fontsize": "11pt"},
    "carpathians": {"toc": False, "fontsize": "11pt"},
}
MD_FORMAT = "markdown+lists_without_preceding_blankline"  # lists may follow a line directly
SERIF_CANDIDATES = ["Noto Serif", "DejaVu Serif", "Liberation Serif"]
MONO_CANDIDATES = ["DejaVu Sans Mono", "Noto Sans Mono", "Liberation Mono"]
FALLBACK_CANDIDATES = ["DejaVu Serif", "DejaVu Sans"]
# Characters taken from the fallback font when the main font lacks them (xelatex only)
FALLBACK_CHARS = "−→←↑↓≈≥≤≠±×∼"

KEY_RE = re.compile(r"\{\{\s*([A-Za-z0-9_]+)\s*\}\}")
MARKER_RE = re.compile(r"\[\[(.+?)\]\]")
COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
SENTINEL = "\u00a7\u00a7"  # §§key§§ marks a PENDING value during processing
SENTINEL_RE = re.compile(SENTINEL + r"([A-Za-z0-9_]+)" + SENTINEL)

LUA_FILTER = r'''
-- Highlight spans with class "pending" in LaTeX output (HTML uses CSS).
function Span(el)
  if el.classes:includes("pending") and FORMAT:match("latex") then
    local out = { pandoc.RawInline("latex", "\\textcolor{red}{\\textbf{") }
    for _, x in ipairs(el.content) do table.insert(out, x) end
    table.insert(out, pandoc.RawInline("latex", "}}"))
    return out
  end
end
'''

LATEX_HEADER = r'''
\usepackage{xcolor}
\usepackage{fancyhdr}
\pagestyle{fancy}
\fancyhf{}
\fancyfoot[C]{\thepage}
\fancyfoot[R]{\footnotesize BUILDSTAMP}
\renewcommand{\headrulewidth}{0pt}
FALLBACK
'''

CSS = r'''
@page { size: A4; margin: 22mm 20mm 25mm 20mm;
        @bottom-center { content: counter(page); font-size: 9pt; } }
html { font-family: "Noto Serif", "DejaVu Serif", Georgia, serif; font-size: 11pt;
       line-height: 1.5; color: #1a1a1a; }
body { max-width: 46em; margin: 2em auto; padding: 0 1em; }
h1, h2, h3 { font-family: "Noto Sans", "DejaVu Sans", sans-serif; line-height: 1.25; }
h1.title { font-size: 1.7em; margin-bottom: 0.2em; }
p.subtitle { font-size: 1.15em; margin-top: 0; color: #444; }
h2 { font-size: 1.3em; margin-top: 1.8em; border-bottom: 1px solid #ccc; }
h3 { font-size: 1.1em; margin-top: 1.4em; }
table { border-collapse: collapse; width: 100%; font-size: 0.88em; margin: 1em 0; }
th, td { border: 1px solid #bbb; padding: 0.3em 0.5em; vertical-align: top; text-align: left; }
th { background: #eee; }
blockquote { border-left: 3px solid #bbb; margin-left: 0; padding-left: 1em; color: #333; }
code, pre { font-family: "DejaVu Sans Mono", monospace; font-size: 0.85em; }
pre { background: #f5f5f5; padding: 0.6em; overflow-x: auto; }
.pending { background: #fff3b0; color: #a00000; font-weight: bold; }
img { max-width: 100%; }
'''


# ---------------------------------------------------------------- numbers.yaml
@dataclass
class Number:
    value: str
    comment: str = ""

    @property
    def pending(self) -> bool:
        return self.value.strip().upper() == "PENDING"

    @property
    def check(self) -> bool:
        return "CHECK" in self.comment.upper()


def load_numbers(path: Path) -> dict[str, Number]:
    """Parse the flat numbers.yaml: `key: "value"  # comment` or `key: value  # comment`."""
    numbers: dict[str, Number] = {}
    line_re = re.compile(r"^([A-Za-z0-9_]+)\s*:\s*(.*)$")
    for lineno, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        m = line_re.match(line)
        if not m:
            sys.exit(f"numbers.yaml line {lineno}: cannot parse: {raw}")
        key, rest = m.group(1), m.group(2)
        if rest.startswith('"'):
            end = rest.find('"', 1)
            if end == -1:
                sys.exit(f"numbers.yaml line {lineno}: unclosed quote")
            value = rest[1:end]
            comment = rest[end + 1:].split("#", 1)[1].strip() if "#" in rest[end + 1:] else ""
        else:
            parts = rest.split(" #", 1)
            value = parts[0].strip()
            comment = parts[1].strip() if len(parts) > 1 else ""
        if key in numbers:
            print(f"WARNING numbers.yaml: duplicate key '{key}' (line {lineno}), last value used")
        numbers[key] = Number(value, comment)
    return numbers


# ---------------------------------------------------------------- processing
@dataclass
class FileReport:
    name: str
    pending_markers: list[str] = field(default_factory=list)
    check_markers: list[str] = field(default_factory=list)
    field_notes: list[str] = field(default_factory=list)
    other_markers: list[str] = field(default_factory=list)
    pending_values: set[str] = field(default_factory=set)
    unknown_keys: set[str] = field(default_factory=set)
    used_keys: set[str] = field(default_factory=set)

    @property
    def blocking(self) -> int:
        return (len(self.pending_markers) + len(self.check_markers) + len(self.field_notes)
                + len(self.other_markers) + len(self.pending_values) + len(self.unknown_keys))


def substitute(text: str, numbers: dict[str, Number], rep: FileReport, sentinel: bool) -> str:
    """Replace {{key}}. PENDING values become a sentinel (markdown) or stay 'PENDING' (plain)."""
    def repl(m: re.Match) -> str:
        key = m.group(1)
        rep.used_keys.add(key)
        if key not in numbers:
            rep.unknown_keys.add(key)
            return f"[[UNKNOWN KEY: {key}]]"
        n = numbers[key]
        if n.pending:
            rep.pending_values.add(key)
            return f"{SENTINEL}{key}{SENTINEL}" if sentinel else "PENDING"
        return n.value
    return KEY_RE.sub(repl, text)


def classify_markers(text: str, rep: FileReport) -> None:
    for m in MARKER_RE.finditer(text):
        body = m.group(1).strip()
        body_clean = SENTINEL_RE.sub(lambda s: f"{s.group(1)}?", body)
        head = body.split(":", 1)[0].strip().upper()
        if head.startswith("PENDING"):
            rep.pending_markers.append(body_clean)
        elif head.startswith("CHECK"):
            rep.check_markers.append(body_clean)
        elif head.startswith("FIELD NOTE"):
            rep.field_notes.append(body_clean)
        elif head.startswith("UNKNOWN KEY"):
            pass  # already counted in unknown_keys
        else:
            rep.other_markers.append(body_clean)


def markers_to_spans(text: str) -> str:
    """[[…]] and PENDING sentinels -> pandoc spans with class .pending."""
    def marker(m: re.Match) -> str:
        body = SENTINEL_RE.sub(lambda s: f"{s.group(1)}?", m.group(1).strip())
        body = body.replace("[", "(").replace("]", ")")
        return f"[\u00ab{body}\u00bb]{{.pending}}"
    text = MARKER_RE.sub(marker, text)
    return SENTINEL_RE.sub(lambda s: f"[{s.group(1)}: PENDING]{{.pending}}", text)


def process_markdown(src: Path, numbers: dict[str, Number], rep: FileReport) -> str:
    text = COMMENT_RE.sub("", src.read_text(encoding="utf-8"))
    text = substitute(text, numbers, rep, sentinel=True)
    classify_markers(text, rep)
    return markers_to_spans(text)


def process_plain(src: Path, numbers: dict[str, Number], rep: FileReport) -> str:
    """Data package files: substitute values, keep [[…]] markers as plain text."""
    text = src.read_text(encoding="utf-8")
    if src.suffix == ".md":
        text = COMMENT_RE.sub("", text)
    text = substitute(text, numbers, rep, sentinel=False)
    classify_markers(text, rep)
    return text


# ---------------------------------------------------------------- pandoc
def run(cmd: list[str], label: str) -> bool:
    res = subprocess.run(cmd, capture_output=True, text=True)
    msgs = [l for l in (res.stderr or "").splitlines() if l.strip()]
    missing = [l for l in msgs if "Missing character" in l]
    other = [l for l in msgs if "Missing character" not in l]
    for l in other[:15]:
        print(f"    {l}")
    if missing:
        chars = sorted({re.sub(r".*There is no (\S+).*", r"\1", l) for l in missing})
        print(f"    WARNING {label}: font lacks {len(chars)} character(s): {' '.join(chars[:30])}")
        print("    -> add them to FALLBACK_CHARS in build.py, or use --font 'DejaVu Serif'")
    if res.returncode != 0:
        print(f"  FAILED {label} (pandoc exit {res.returncode})")
        return False
    print(f"  ok     {label}")
    return True


def first_font(candidates: list[str]) -> str | None:
    if not shutil.which("fc-list"):
        return None
    families = subprocess.run(["fc-list", ":", "family"], capture_output=True, text=True).stdout
    available = {f.strip() for line in families.splitlines() for f in line.split(",")}
    return next((c for c in candidates if c in available), None)


def fallback_block(main: str | None, fallback: str | None) -> str:
    """LaTeX lines that print FALLBACK_CHARS in the fallback font, keeping the main font elsewhere."""
    if not fallback or fallback == main:
        return ""
    lines = [r"\usepackage{newunicodechar}", r"\newfontfamily\fallbackfont{" + fallback + "}"]
    for ch in FALLBACK_CHARS:
        lines.append(r"\newunicodechar{" + ch + r"}{{\fallbackfont\char" + f'"{ord(ch):04X}' + "}}")
    return "\n".join(lines)


def build_doc(name: str, md_path: Path, src_dir: Path, args,
              fonts: tuple[str | None, str | None, str | None], stamp: str) -> None:
    opts = PDF_OPTIONS[name]
    resource = f"{src_dir}:{PUB / 'figures'}:{PUB}"
    lua = AUX / "pending.lua"
    css = AUX / "style.css"

    html_cmd = ["pandoc", str(md_path), "-f", MD_FORMAT, "-o", str(OUT / f"{name}.html"),
                "--standalone", "--embed-resources", "--mathml",
                "--css", str(css), "--lua-filter", str(lua),
                "--resource-path", resource, "--metadata", "lang=en"]
    if opts["toc"]:
        html_cmd += ["--toc", "--toc-depth=2"]
    run(html_cmd, f"{name}.html")

    if args.no_pdf:
        return
    pdf = OUT / f"{name}.pdf"
    if args.pdf_engine == "xelatex":
        header = AUX / "header.tex"
        serif, mono, fallback = fonts
        header.write_text(LATEX_HEADER.replace("BUILDSTAMP", stamp.replace("_", r"\_"))
                          .replace("FALLBACK", fallback_block(serif, fallback)), encoding="utf-8")
        cmd = ["pandoc", str(md_path), "-f", MD_FORMAT, "-o", str(pdf), "--pdf-engine=xelatex",
               "--lua-filter", str(lua), "-H", str(header),
               "--resource-path", resource, "--metadata", "lang=en",
               "-V", "papersize=a4", "-V", "geometry:margin=25mm",
               "-V", f"fontsize={opts['fontsize']}", "-V", "linestretch=1.15",
               "-V", "colorlinks=true", "-V", "linkcolor=blue", "-V", "urlcolor=blue"]
        if serif:
            cmd += ["-V", f"mainfont={serif}"]
        if mono:
            cmd += ["-V", f"monofont={mono}"]
        if opts["toc"]:
            cmd += ["--toc", "--toc-depth=2"]
    else:
        cmd = ["pandoc", str(md_path), "-f", MD_FORMAT, "-o", str(pdf), "--pdf-engine=weasyprint",
               "--standalone", "--css", str(css), "--lua-filter", str(lua),
               "--resource-path", resource, "--metadata", "lang=en"]
        if opts["toc"]:
            cmd += ["--toc", "--toc-depth=2"]
    run(cmd, f"{name}.pdf ({args.pdf_engine})")


# ---------------------------------------------------------------- report
def write_report(reports: list[FileReport], numbers: dict[str, Number], stamp: str, mode: str) -> Path:
    used = set().union(*(r.used_keys for r in reports)) if reports else set()
    lines = [f"# Build report — {stamp} ({mode})", "",
             "| File | PENDING markers | PENDING values | CHECK | Field notes | Other | Unknown keys |",
             "|---|---|---|---|---|---|---|"]
    for r in reports:
        lines.append(f"| {r.name} | {len(r.pending_markers)} | {len(r.pending_values)} | "
                     f"{len(r.check_markers)} | {len(r.field_notes)} | {len(r.other_markers)} | "
                     f"{len(r.unknown_keys)} |")
    total = sum(r.blocking for r in reports)
    lines += ["", f"**Total blocking items: {total}**", ""]

    for r in reports:
        if not r.blocking:
            continue
        lines += [f"## {r.name}", ""]
        for title, items in [("PENDING markers", r.pending_markers), ("CHECK markers", r.check_markers),
                             ("Field notes", r.field_notes), ("Other markers", r.other_markers)]:
            if items:
                lines += [f"**{title}**", ""] + [f"- {i}" for i in items] + [""]
        if r.pending_values:
            lines += ["**Keys still PENDING in numbers.yaml**", "", ", ".join(sorted(r.pending_values)), ""]
        if r.unknown_keys:
            lines += ["**Keys not defined in numbers.yaml**", "", ", ".join(sorted(r.unknown_keys)), ""]

    checks = sorted(k for k, n in numbers.items() if n.check)
    if checks:
        lines += ["## Values marked CHECK in numbers.yaml", ""]
        lines += [f"- `{k}` = {numbers[k].value} — {numbers[k].comment}" for k in checks] + [""]
    unused = sorted(set(numbers) - used)
    if unused:
        lines += ["## Keys defined but not used in any output", "", ", ".join(unused), ""]

    path = BUILD / "report.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


# ---------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--only", nargs="+", choices=[*DOCS, "data"], help="build only these outputs")
    ap.add_argument("--release", action="store_true", help="fail if any placeholder remains")
    ap.add_argument("--no-pdf", action="store_true", help="skip PDF output")
    ap.add_argument("--pdf-engine", choices=["xelatex", "weasyprint"], default="xelatex")
    ap.add_argument("--font", help="main serif font for xelatex (default: auto)")
    args = ap.parse_args()

    if not shutil.which("pandoc"):
        sys.exit("pandoc not found on PATH")
    if not args.no_pdf and not shutil.which(args.pdf_engine):
        sys.exit(f"{args.pdf_engine} not found on PATH (use --no-pdf or another --pdf-engine)")

    numbers = load_numbers(NUMBERS)
    targets = args.only or [*DOCS, "data"]
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    mode = "release" if args.release else "draft"

    OUT.mkdir(parents=True, exist_ok=True)
    AUX.mkdir(parents=True, exist_ok=True)
    (AUX / "pending.lua").write_text(LUA_FILTER, encoding="utf-8")
    (AUX / "style.css").write_text(CSS, encoding="utf-8")

    # Pass 1: process text, collect report
    processed: dict[str, tuple[Path, str]] = {}
    reports: list[FileReport] = []
    for name in [t for t in targets if t in DOCS]:
        src = DOCS[name]
        if not src.exists():
            print(f"skip {name}: {src} not found")
            continue
        rep = FileReport(name)
        processed[name] = (src, process_markdown(src, numbers, rep))
        reports.append(rep)

    data_out: dict[str, str] = {}
    if "data" in targets:
        for fname in DATA_PACKAGE_FILES:
            src = PUB / "data_package" / fname
            if not src.exists():
                print(f"skip data_package/{fname}: not found")
                continue
            rep = FileReport(f"data_package/{fname}")
            data_out[fname] = process_plain(src, numbers, rep)
            reports.append(rep)

    report_path = write_report(reports, numbers, stamp, mode)
    total = sum(r.blocking for r in reports)
    print(f"Placeholders remaining: {total}  (details: {report_path.relative_to(PUB.parent)})")
    for r in reports:
        if r.blocking:
            print(f"  {r.name:32s} pending {len(r.pending_markers) + len(r.pending_values):3d}  "
                  f"check {len(r.check_markers):2d}  field notes {len(r.field_notes)}  "
                  f"unknown keys {len(r.unknown_keys)}")

    if args.release and total:
        print("RELEASE STOPPED: resolve all items in the report first.")
        return 1

    # Pass 2: write outputs
    serif = args.font or first_font(SERIF_CANDIDATES)
    mono = first_font(MONO_CANDIDATES)
    fallback = first_font(FALLBACK_CANDIDATES)
    if not args.no_pdf and args.pdf_engine == "xelatex":
        fb = f", symbol fallback = {fallback}" if fallback and fallback != serif else ""
        print(f"Fonts: main = {serif or 'LaTeX default'}, mono = {mono or 'LaTeX default'}{fb}")

    build_stamp = f"{mode} build {stamp}"
    for name, (src, text) in processed.items():
        md_out = OUT / f"{name}.md"
        md_out.write_text(text, encoding="utf-8")
        build_doc(name, md_out, src.parent, args, (serif, mono, fallback), build_stamp)

    if data_out:
        dp = OUT / "data_package"
        dp.mkdir(parents=True, exist_ok=True)
        for fname, text in data_out.items():
            (dp / fname).write_text(text, encoding="utf-8")
        lic = PUB / "data_package" / "licenses"
        if lic.is_dir():
            shutil.copytree(lic, dp / "licenses", dirs_exist_ok=True)
        print(f"  ok     data_package ({len(data_out)} files)")

    print(f"Outputs in {OUT.relative_to(PUB.parent)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
