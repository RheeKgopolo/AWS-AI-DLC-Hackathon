# Tech

## Stack
- React 19 with `react-dom`, function components and hooks.
- TypeScript (`~7.0`), ES modules (`"type": "module"`).
- Vite 8 with `@vitejs/plugin-react`.
- Oxlint for linting (`.oxlintrc.json`: react, typescript, oxc plugins).
- npm (`package-lock.json`).
- Plain CSS only. No UI framework.
- Runtime dependencies: `react` and `react-dom`. PapaParse is allowed for CSV parsing but is not installed yet. Add no other runtime dependency without a clear need, and say so when adding one.
- Testing: no test framework is installed yet. The feature spec requires unit tests for the scoring function (requirements 4 to 7). Ask before adding a test runner (Vitest is the likely choice for Vite). Do not write tests beyond that unless asked.
- The app must work with `npm install` and `npm run dev`, with no environment variables or keys, and must work offline.

## Commands
- `npm run dev`: Vite dev server on port 5173. Run it in your own terminal, not from the agent.
- `npm run build`: `tsc -b && vite build`.
- `npm run lint`: `oxlint`.
- `npm run preview`: serve the production build.

TypeScript, lint and formatting rules are in `code-style.md`. It loads when `.ts` or `.tsx` files are in context.

## Dev server behind the IDE proxy
`vite.config.ts` is set up for the Kiro IDE CloudFront proxy. Do not undo these settings without asking.
- Dev URL: `https://<your-cloudfront-host>/absproxy/5173/` (trailing slash required).
- `base` is `/absproxy/5173/` for `serve` only. Builds use `/`.
- `server.allowedHosts` is `[".cloudfront.net"]`; the HMR host comes from `VSCODE_PROXY_URI`. `strictPort` is on, so port 5173 must be free.
- HMR uses `wss` on port 443 through that host.
- Because of `base`, reference public files from `index.html` with root paths that Vite rewrites (e.g. `<link href="/favicon.svg">`). For JS and JSX, see `code-style.md`.

## Python app (Royal Table (Account Growth Agent))
The Royal Table (Account Growth Agent) is a separate Python app. The React rules above do not apply to it.
- Python 3.11 or later, Streamlit for the UI, boto3 for Bedrock (Converse API with tool use), pytest for tests.
- Run with `pip install -r requirements.txt` and `streamlit run app.py`. Test with `pytest`.
- Browser tests: `pip install -r requirements-dev.txt` and `playwright install chromium`, then run `pytest` with `BEDROCK_MODEL_ID` set. On Amazon Linux 2023, Chromium needs system libraries from `dnf` (libatomic, nss, atk, mesa-libgbm, alsa-lib and others, plus google-noto-emoji-color-fonts for emoji). `playwright install --with-deps` does not support this OS.
- Config: `BEDROCK_MODEL_ID` and `AWS_REGION` from environment variables. AWS credentials come from the standard credential chain. Never hard code keys.
- All state lives in Streamlit session state. No database.
- Use a virtual environment (`.venv`). Do not install Python packages globally.
- Never change test expectations or the data file to make tests pass.

## Conventions
- Add dependencies only when needed, and say so when you do.
- Keep secrets out of the repo. Client env vars must use the `VITE_` prefix and are public.
