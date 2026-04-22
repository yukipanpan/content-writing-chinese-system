"""
run_skill.py — CLI entry point for the content writing pipeline.

Usage:
  python3 scripts/run_skill.py phase1 \\
    --urls "https://a.com, https://youtu.be/xyz" \\
    --intent "analytical piece on XCM for Ethereum devs" \\
    --generate-snippets --pr-body-file pr_body.md

  python3 scripts/run_skill.py phase1 \\
    --topic "Polkadot JAM upgrade 2025" \\
    --intent "analytical piece on JAM" \\
    --top-n 5 --generate-snippets --pr-body-file pr_body.md

  python3 scripts/run_skill.py phase2 --pr-body-file pr_body.md

  python3 scripts/run_skill.py monthly-recap --month 2026-04
"""

import argparse

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from pipeline import run_phase1, run_phase2, run_monthly_recap


def main():
    parser = argparse.ArgumentParser(description="Content writing pipeline")
    sub = parser.add_subparsers(dest="mode", required=True)

    p1 = sub.add_parser("phase1", help="Fetch sources and generate English outline")
    p1.add_argument("--urls",              default="",    help="Manual source URLs (comma-separated)")
    p1.add_argument("--topic",             default=None,  help="Topic keyword for auto-discovery")
    p1.add_argument("--top-n",             default=5, type=int, help="Max auto-discovered URLs (default 5)")
    p1.add_argument("--intent",            required=True, help="What to write (1-3 sentences)")
    p1.add_argument("--generate-snippets", action="store_true", help="Save source snippets to KB")
    p1.add_argument("--pr-body-file",      default="pr_body.md")

    p2 = sub.add_parser("phase2", help="Generate Chinese article from approved outline")
    p2.add_argument("--pr-body-file", required=True)
    p2.add_argument("--output-dir",   default=None)

    pm = sub.add_parser("monthly-recap", help="Synthesise monthly snippets into a recap article")
    pm.add_argument("--month", required=True, help="Month in YYYY-MM format")

    args = parser.parse_args()

    if args.mode == "phase1":
        run_phase1(args)
    elif args.mode == "phase2":
        run_phase2(args)
    elif args.mode == "monthly-recap":
        run_monthly_recap(args)


if __name__ == "__main__":
    main()
