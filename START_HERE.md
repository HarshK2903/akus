# Start building AKUS with Codex CLI on Linux

## 1. Install prerequisite commands
- `git --version`, `node --version`, `npm --version`, `python3 --version`, `docker --version`, `docker compose version`
- Install missing tools appropriate to your Linux distribution. The target FastAPI backend prefers Python 3.13; ensure Codex can arrange a project-local interpreter when unavailable.
- Install/update Codex with `npm install -g @openai/codex@latest` (or the official Codex standalone installer), then `codex --version`.

## 2. Unpack into a CLEAN project directory
`mkdir -p ~/projects/akus && cd ~/projects/akus`
`unzip ~/Downloads/AKUS_Codex_Starter_Kit.zip`
`git init`
`git add AGENTS.md START_HERE.md docs/`
`git commit -m 'docs: seed AKUS binding specification and Codex workflow'`

## 3. Start Codex IN THIS DIRECTORY
`cd ~/projects/akus && codex`
Sign in using the official interactive flow if prompted. Paste the TEXT from `docs/codex/FIRST_PROMPT.txt` as your FIRST Codex message. Do not paste 400 KB of the master spec into the chat.

## 4. Repeat after a completed slice
`Continue the next unfinished phase from docs/codex/BUILD_PHASES.md and BUILD_PROGRESS.md. Implement real APIs, data and pages, run tests and update traceability. Do not mark unfinished work complete.`

## 5. Verify and review
Ask Codex to start the app locally and give exact frontend/backend URLs, commands, local demo accounts, test reports and traces. For each phase inspect `git status`, `BUILD_PROGRESS.md`, and screenshots. Resume later with `codex resume --last` from the same project folder.

## Additional cautions
- The master prompt already CONTAINS the UIUX blueprint. Do not blindly concat the blueprint again when passing it to a model.
- `POLICY_GAPS.md` must include topic-mapping edits to already reserved seats, Q51 multi-subject Silver credit, current Principal emerging-tech permissions and active-case role promotion. Keep these blocked unless formally decided.
- Screens using demo identity or provider fixtures must be labeled as DEMO, never production verification.
- Never run Codex with unsafe sandbox bypass just to make tasks run; approve narrowly scoped permissions where needed.
