Generate the Chinese article from the approved outline in `pr_body.md`.

## Steps

1. Check whether `pr_body.md` exists in the project root.
   - If it does not exist: tell the user to run `/phase1 <urls> <intent>` first to generate an outline.

2. Run Phase 2:

```bash
python3 scripts/run_skill.py phase2 \
  --pr-body-file pr_body.md
```

3. After the command completes, tell the user where the article was saved:
   - Analytical / opinion pieces → `output/analysis/`
   - Tutorials → `output/tutorials/`
   - Concept explainers → `output/explainers/`
   - Pop-science / YouTube-based → `output/science-pop/`
   - Monthly recaps → `output/monthly-recap/`
   
   The article type is determined automatically from the outline in `pr_body.md`. Read the script output or the `pr_body.md` type field to confirm which folder was used, and tell the user the exact filename if it appears in the output.
