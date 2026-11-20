---
inclusion: fileMatch
fileMatchPattern: ["**/*.ts", "**/*.tsx"]
---

# Code style (TypeScript and TSX)

## Formatting
- No semicolons, single quotes, 2-space indent. Match the existing files.

## TypeScript rules (tsconfig.app.json)
- `verbatimModuleSyntax`: use `import type` for type-only imports.
- `erasableSyntaxOnly`: no `enum`, `namespace`, or constructor parameter properties. Use union types and plain objects.
- `noUnusedLocals` and `noUnusedParameters` are on.
- `allowImportingTsExtensions`: local imports include the extension where the existing code does (e.g. `./App.tsx`).
- `moduleResolution: bundler`, `jsx: react-jsx`.

## Lint rules (.oxlintrc.json)
- `react/rules-of-hooks` is an error.
- `react/only-export-components` is a warning. Keep component files exporting only components.

## Asset URLs
- The dev server runs with `base: '/absproxy/5173/'`. In JS or JSX, import the asset or build the URL from `import.meta.env.BASE_URL`. A hardcoded root path such as `/icons.svg` will not get the base (`src/App.tsx` currently has this problem).
