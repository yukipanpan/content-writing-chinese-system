Generate a monthly recap article from all snippets accumulated for a given month.

**Arguments:** `$ARGUMENTS` — optional month in `YYYY-MM` format (e.g. `2026-04`).

## Steps

1. Parse `$ARGUMENTS` for a month string matching the pattern `YYYY-MM`.
   - If a valid month is found, use it.
   - If no month is provided or the format is invalid, use the current month (today's date formatted as `YYYY-MM`).

2. Run the monthly recap:

```bash
python3 scripts/run_skill.py monthly-recap --month <YYYY-MM>
```

3. After the command completes, tell the user:
   - Which month was processed
   - Where the recap article was saved: `output/monthly-recap/`
   - The filename if it appears in the script output

## Notes

- The script reads all snippet files in `references/snippets/` whose IDs match the target month.
- If no snippets exist for the requested month, the script will report this — tell the user to run `/phase1` with sources first to build up the knowledge base.
- The monthly recap also runs automatically via GitHub Actions on the 1st of every month (Layer 3).
