# Smart Check-In Dashboard — DCT Abu Dhabi

A real-time project tracking dashboard for the **DCT Abu Dhabi Face Recognition Smart Check-In Programme**, built as a standalone React application.

## Overview

This dashboard provides a comprehensive view of the Smart Check-In project across all phases — from initiation and planning through pilot deployment, hotel scaling, and mobile arrival integration.

### Features

- **Phase Tracker** — Visual progress tracking across 5 project phases (Initiate → Planning → Pilot → Hotel Scaling → Mobile Arrival)
- **Task Breakdown** — Detailed task-level progress for each phase with percentage completion
- **Interactive Charts** — Bar and pie charts powered by Recharts for data visualization
- **Password-Protected** — SHA-256 hashed passcode lock screen for restricted access
- **AI Chat Assistant** — Built-in conversational assistant for project queries
- **Responsive Design** — Works across desktop and tablet screens

## Tech Stack

- **React 18** (loaded via CDN)
- **Recharts** — charting library
- **Lucide React** — icon set
- **Babel Standalone** — in-browser JSX transpilation
- **Google Fonts (Outfit)** — typography

## Deployment

The dashboard is a single `index.html` file with no build step required. It can be deployed to any static hosting provider:

- **GitHub Pages** — enable in repository settings under Pages → Source → Deploy from a branch
- **Any static host** — simply serve `index.html`

## Project Structure

```
index.html                  # Standalone dashboard (deployment entry point)
SmartCheckInDashboard.jsx   # React component source
```

## Connect

- **Instagram** — [@brdgconcept](https://www.instagram.com/brdgconcept)

## License

Internal use — DCT Abu Dhabi.
