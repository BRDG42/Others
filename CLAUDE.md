# CLAUDE.md

## Repository Overview

**Others** is a general-purpose repository for miscellaneous projects and files that don't belong to a dedicated repo. It acts as a catch-all workspace.

- **Owner:** BRDG42
- **Default branch:** `main`

## Repository Structure

```
/
├── README.md                              # Project description
├── DCT_Master_PPT_Template - basic.pptx   # PowerPoint 2007+ template file
└── CLAUDE.md                              # This file
```

## Contents

| File | Description |
|------|-------------|
| `DCT_Master_PPT_Template - basic.pptx` | Microsoft PowerPoint template (binary, ~6.7 MB) |
| `README.md` | Brief project description |

## Development Workflow

- There is no build system, test suite, or CI/CD pipeline in this repository.
- No package manager or dependency files are present.
- Changes are committed directly; there are no linting or formatting tools configured.

## Conventions for AI Assistants

1. **Binary files** — The `.pptx` file is a binary asset. Do not attempt to read, diff, or modify it with text-based tools.
2. **Simplicity** — This is a lightweight, unstructured repo. Avoid introducing unnecessary tooling, configs, or abstractions.
3. **Commit messages** — Follow the existing style: short, descriptive summaries (e.g., "Add files via upload", "Update README with new project information").
4. **Branch naming** — Feature branches follow the pattern `claude/<description>-<id>`.
5. **No tests or builds** — There is nothing to compile, test, or lint. Do not add CI workflows unless explicitly requested.
