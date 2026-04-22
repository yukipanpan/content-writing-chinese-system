Extract URLs and intent from the user's input, run Phase 1, and display the outline for review.

**Arguments:** `$ARGUMENTS` — any combination of URLs (http/https) and free-text intent.

## Steps

1. Parse `$ARGUMENTS`:
   - Extract all tokens that start with `http://` or `https://` — these are the URLs.
   - The remaining text is the intent.
   - If no URLs are found, ask the user to provide at least one URL before continuing.
   - If no intent text is found, ask the user what they want to write before continuing.

2. Run Phase 1:

```bash
python3 scripts/run_skill.py phase1 \
  --urls "<comma-separated URLs>" \
  --intent "<intent text>" \
  --generate-snippets \
  --pr-body-file pr_body.md
```

3. After the command completes, read `pr_body.md` and display the outline section to the user.

4. Ask the user: "Does this outline look right? You can ask me to adjust the angle, sections, or thesis — or say 'looks good' to run `/generate` and produce the Chinese article."

## Edge cases

- If `pr_body.md` is not found after the run, tell the user the script may have failed and show the command output.
- If the user provides a YouTube URL or Twitter/X URL: remind them these work locally but are blocked in GitHub Actions CI. The script will fetch them now.
- If the user provides only pasted text (no URLs): tell them to use the Layer 0 path — open `skills/SKILL.MD` in any AI chat and paste the text directly.
