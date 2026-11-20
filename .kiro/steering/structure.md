# Structure

## Layout
```
idea-board/
├── index.html            Vite entry; mounts <div id="root"> and loads /src/main.tsx
├── vite.config.ts        Vite config (React plugin, IDE proxy settings)
├── package.json
├── tsconfig.json         References tsconfig.app.json and tsconfig.node.json
├── tsconfig.app.json     Compiler options for src/
├── tsconfig.node.json    Compiler options for vite.config.ts
├── .oxlintrc.json        Lint config
├── public/               Static files served as-is (favicon.svg, icons.svg)
└── src/
    ├── main.tsx          Creates the React root, renders <App /> in StrictMode
    ├── App.tsx           Root component (still the template demo)
    ├── App.css           Styles for App
    ├── index.css         Global styles
    └── assets/           Images imported from code (hero.png, react.svg, vite.svg)
```

## Python app files (Royal Table (Account Growth Agent))
The Python app lives at the repo root, next to the React app, and does not import from `src/`.
```
app.py                    Streamlit UI and agent loop
tools.py                  score_accounts, build_invite_list, draft_spend_request (pure functions)
test_tools.py             pytest tests for tools.py
test_e2e.py               Playwright browser tests (real Bedrock)
requirements.txt
requirements-dev.txt      Test-only dependencies (pytest-playwright)
assets/royal_cyber_logo.svg
data/tampa_target_accounts.csv    Read-only input. Identical to public/sample/tampa_target_accounts.csv
```
Do not add other Python files without asking. Scoring logic is deliberately duplicated in `tools.py` and `src/scoring.ts`. Keep both in sync.

## Conventions
- Application code goes in `src/`. Anything outside `src/` is tooling config.
- Components are PascalCase `.tsx` files. Put a component's CSS next to it, with the same name (`Thing.tsx`, `Thing.css`).
- Import images and other assets from `src/assets/`. Put files that must keep a fixed URL in `public/`.
- `main.tsx` stays minimal. App-level composition belongs in `App.tsx`.
- When `src/` grows, group by feature (e.g. `src/features/ideas/`) rather than by file type. Do not create folders ahead of need.
- Sample data goes at `public/sample/tampa_target_accounts.csv` (fixed by the feature spec).
- Scoring logic is a single pure function in its own module with no React imports, so it can be unit tested on its own.
- Do not edit `node_modules/` or generated tsbuildinfo files.
