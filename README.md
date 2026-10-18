# Pre-consultation Preparation System

A self-hosted web application that helps people organize information before a healthcare appointment. Users can record a concern in their own words, answer relevant follow-up questions, and prepare a consultation brief to review with a healthcare professional.

> **Health notice:** This academic prototype does not diagnose conditions, provide treatment advice, or replace professional care. Its patterns and safety prompts are informational only. For urgent or worsening symptoms, contact local emergency or healthcare services.

## Highlights

- Account registration, sign-in, sign-out, and password reset flow.
- Guided consultation form for the concern, description, duration, severity, optional weight, and extra context.
- Symptom normalization for selected common terms and spelling variations, while preserving the user's wording.
- Context-aware follow-up questions that use information already provided.
- Rule-based possible discussion patterns and safety findings, presented with uncertainty language.
- Consultation history scoped to the signed-in account.
- Print-friendly consultation brief that can be saved as PDF from the browser.
- Soft baby-pink interface with rose-colored buttons designed for clear contrast.
- No third-party runtime packages; the server uses Python's standard library and SQLite.

## Project files

~~~text
app.js        Browser application and user flows
engine.js     Follow-up selection and rule-based analysis
index.html    Application entry point
normalizer.js Symptom aliases and spelling normalization
server.py     Local HTTP API, authentication, and SQLite persistence
start.bat     Windows launcher
style.css     Layout, responsive styles, and color palette
data/         Created automatically for the local SQLite database
~~~

## Requirements

- Python 3.10 or later.
- A current web browser.
- Windows users can start the app with start.bat. macOS and Linux users can run it from a terminal.

No npm install or Python package installation is required. package.json is included for editor and tooling metadata; the application itself is served by Python.

## Run locally

### Windows

1. Open this project folder.
2. Double-click start.bat.
3. When the browser opens, visit http://127.0.0.1:8000.
4. Keep the server window open while using the app. Close it to stop the server.

### macOS or Linux

From this folder, run:

~~~bash
python3 server.py
~~~

Then open http://127.0.0.1:8000. On systems where python refers to Python 3.10 or later, python server.py also works.

Do not open index.html directly from the file system. The application needs its server for authentication and saved consultations.

## Configuration

The app works locally with no configuration. The server supports these optional environment variables:

| Variable | Purpose |
| --- | --- |
| APP_DB | SQLite database path; defaults to data/preconsultation.sqlite3. |
| APP_SECRET | Secret used to sign session cookies. Set a long, random value before any shared deployment. |
| APP_ENV | Set to development to enable the demonstration reset-token response without email. Do not use this mode for a public deployment. |
| APP_PUBLIC_URL | Public base URL used to construct reset links when SMTP is configured. |
| SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_FROM | Optional SMTP settings for password reset emails. The port defaults to 587 and TLS is used. |

Keep credentials in environment variables or a local .env file that is never committed. The repository .gitignore excludes .env files, Python cache files, and local SQLite databases.

## Data, privacy, and deployment

Consultation content is saved in a local SQLite database and associated with the account that created it. The app does not send patient text to external services. The local database is deliberately excluded from version control.

This project uses Python's built-in development HTTP server and is intended for local academic demonstration. It is **not hardened for public internet or clinical deployment**. Do not expose it to the internet or use real patient information. A production deployment would require a properly configured HTTPS web server, secure secret management, deployment-grade session and request protections, operational monitoring, and a privacy and security review appropriate to the deployment context.

## License

This project is licensed under the MIT License. See the LICENSE file.
