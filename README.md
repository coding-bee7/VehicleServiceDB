# AutoDB --- Frontend Branch

> **Project:** Vehicle Service and Maintenance Management System\
> **Application name:** AutoDB\
> **Branch:** `frontend`\
> **Frontend stack:** React, Vite, JavaScript, CSS\
> **Backend integration:** Flask API (integration contracts must be
> confirmed with the backend branch)

This README documents the frontend work maintained on the `frontend`
branch. It focuses on the frontend application and does not replace the
repository-wide documentation for the database, backend, testing, or
project deliverables.

------------------------------------------------------------------------

## Table of Contents

-   [Overview](#overview)
-   [Frontend goals](#frontend-goals)
-   [Technology stack](#technology-stack)
-   [Repository location and
    structure](#repository-location-and-structure)
-   [Application pages and user
    flows](#application-pages-and-user-flows)
-   [Design system](#design-system)
-   [3D car scene and assets](#3d-car-scene-and-assets)
-   [Prerequisites](#prerequisites)
-   [Installation](#installation)
-   [Running the frontend](#running-the-frontend)
-   [Environment configuration](#environment-configuration)
-   [API integration](#api-integration)
-   [Authentication and
    authorization](#authentication-and-authorization)
-   [Development workflow](#development-workflow)
-   [Git workflow](#git-workflow)
-   [Troubleshooting](#troubleshooting)
-   [Current status and integration
    checklist](#current-status-and-integration-checklist)
-   [Security notes](#security-notes)
-   [Contributing](#contributing)

------------------------------------------------------------------------

## Overview

AutoDB is the frontend for a vehicle service and maintenance management
system. It provides a customer-facing experience for discovering
services and accessing service-related workflows, alongside an
administrative interface intended for managing the system.

The interface uses a warm, premium automotive visual style: beige and
brown surfaces, espresso-toned accents, large editorial typography,
motion effects, and a prominent car visual on the landing page.

The frontend is a separate application from the Flask backend and
database components. The frontend can be developed and previewed
independently, but real sign-in, persistent records, bookings, and
administrative operations require a working backend API and a correctly
configured database.

## Frontend goals

-   Present AutoDB and its service offerings through a polished landing
    page.
-   Provide sign-in and account-related entry points.
-   Separate customer-facing and administrator-facing experiences.
-   Provide frontend screens for service booking and viewing service
    history.
-   Keep API communication in a dedicated service module instead of
    scattering requests throughout UI components.
-   Maintain a responsive layout for common desktop and mobile screen
    sizes.
-   Keep the frontend easy to run locally for development and team
    review.

## Technology stack

  -----------------------------------------------------------------------
  Technology                          Purpose
  ----------------------------------- -----------------------------------
  React                               Component-based user interface

  Vite                                Local development server and
                                      production build tooling

  JavaScript / JSX                    Application logic and UI components

  CSS                                 Styling, layout, responsive
                                      behavior, and visual effects

  Fetch/API service module            Central location for communicating
                                      with the backend

  GLB 3D model asset                  Car visual used by the 3D scene,
                                      where supported by the existing
                                      scene implementation

  Flask backend                       Expected HTTP API provider;
                                      maintained separately from this
                                      frontend
  -----------------------------------------------------------------------

The exact dependencies and scripts are defined in `package.json`. Check
that file for the authoritative list of installed packages and available
commands.

## Repository location and structure

The frontend application lives under `application/frontend/` in the
repository.

``` text
application/
└── frontend/
    ├── public/
    │   ├── images/
    │   │   └── autodb-car.png        # Static car image, if used by the UI
    │   ├── models/
    │   │   └── porsche.glb           # 3D model asset
    │   ├── favicon.svg
    │   └── icons.svg
    ├── src/
    │   ├── assets/
    │   │   └── ...                   # Imported frontend assets
    │   ├── services/
    │   │   └── api.js                # Shared API request helpers
    │   ├── App.jsx                   # Main application UI and page/state flow
    │   ├── App.css                   # Main application styles
    │   ├── CarScene.jsx               # Car/3D scene component
    │   ├── index.css                 # Global styles
    │   └── main.jsx                  # React entry point
    ├── .env.example                  # Example local environment configuration
    ├── .gitignore
    ├── eslint.config.js
    ├── index.html
    ├── package.json
    ├── package-lock.json
    ├── vite.config.js
    ├── README.md                     # Frontend application instructions
    └── README-INTEGRATION.md          # Notes for coordinating API integration
```

The exact contents may change as the branch evolves. Keep this tree
synchronized with the files actually committed to the branch. Do not
commit `node_modules/` or a local `.env` file.

## Application pages and user flows

The frontend is organized around these intended screens and flows.
Actual access to protected data or successful submission depends on
backend integration.

### 1. Landing page

-   Introduces AutoDB and its vehicle-service offering.
-   Uses the shared visual theme and automotive imagery/3D visual.
-   Provides navigation and calls to action for exploring services or
    starting an account workflow.

### 2. Sign-in and account entry

-   Provides an entry point for users to sign in.
-   Protected actions may direct unauthenticated visitors to sign in
    first.
-   A service selected before sign-in should be preserved or preselected
    after sign-in where that flow is implemented.

**Important:** A sign-in screen in the frontend does not by itself
authenticate a user. Authentication is only functional once the API
contract, session/token handling, and backend validation are connected
and tested.

### 3. Customer area

The customer-facing screens are intended to support workflows such as:

-   Viewing a customer dashboard.
-   Starting or managing a service booking.
-   Reviewing service or booking history.
-   Navigating back to the service catalogue and account-related
    screens.

Live customer data and booking actions require the corresponding backend
endpoints.

### 4. Service booking

The booking UI is intended to collect the information required to
request a vehicle service. Confirm the final required fields and
validation rules with the backend developer before treating the form as
integrated.

A successful-looking UI state should not be interpreted as proof that a
booking was saved in the database. Verify the API response and confirm
the resulting record through the backend/database workflow.

### 5. Administrator area

The frontend includes an administrative experience intended to provide a
separate interface for system-management tasks. The final set of admin
capabilities must match the backend's implemented endpoints and the
project's agreed requirements.

Administrator-only actions must be enforced by the backend. Hiding admin
controls in React is not sufficient authorization.

### Navigation behavior

Some calls to action may send a visitor to sign-in when the visitor is
not authenticated. This is appropriate for protected actions, but every
button should have a clear, intentional destination or action. Public
actions---such as learning about services---should not automatically
behave like protected actions unless that is an explicit product
requirement.

------------------------------------------------------------------------

## Design system

The frontend's visual direction is a premium automotive theme.

-   **Palette:** warm beige and cream backgrounds, brown surfaces, and
    dark espresso accents.
-   **Typography:** strong, high-contrast headings with readable body
    text.
-   **Layout:** generous spacing, clear sections, and prominent calls to
    action.
-   **Motion:** subtle hover, transition, and entrance effects where
    implemented.
-   **Responsive behavior:** layouts should remain usable on smaller
    screens as well as desktop.
-   **Consistency:** reuse existing CSS variables, classes, and
    component patterns rather than introducing unrelated styles for each
    page.

When changing styles, check the landing page, customer screens, admin
screens, and authentication views so a change does not unintentionally
break another page.

## 3D car scene and assets

The project includes `src/CarScene.jsx` and the model asset
`public/models/porsche.glb`.

-   Keep the model file at the path expected by the scene component
    unless you update the reference in the code.
-   The 3D model may be large; avoid committing duplicate copies.
-   Test the landing page in a browser after changing the scene or asset
    path.
-   If the browser or device cannot render the 3D scene reliably,
    consider using the existing static car image as a fallback if that
    behavior is implemented.
-   Do not describe the model as a production vehicle configurator
    unless such functionality is actually implemented.

## Prerequisites

Install the following on your development machine:

-   A supported, currently maintained version of Node.js (which includes
    npm).
-   Git.
-   A code editor such as Visual Studio Code.
-   Access to the project repository and the `frontend` branch.

The frontend can be started separately from the backend for UI
development. Backend-dependent features require the backend service to
be running and reachable.

## Installation

Open a terminal at the repository root, then move into the frontend
directory:

``` powershell
cd application/frontend
```

Install dependencies using the committed lockfile:

``` powershell
npm ci
```

If `npm ci` cannot be used because the lockfile is missing or
intentionally out of sync, use `npm install` and commit any intentional
lockfile changes.

### PowerShell note

If PowerShell blocks the `npm` script due to execution policy, try the
Windows command shim:

``` powershell
npm.cmd ci
```

Run other npm commands with `npm.cmd` in the same way if needed.

## Running the frontend

From `application/frontend/`, start the Vite development server:

``` powershell
npm run dev
```

If needed in PowerShell:

``` powershell
npm.cmd run dev
```

Vite prints the local development URL in the terminal. Open that URL in
a browser. Do not assume a fixed port: if the default port is already in
use, Vite may choose another one.

### Other common commands

Check `package.json` for the exact scripts available in this branch.
Typical Vite project commands include:

``` powershell
npm run build
npm run preview
npm run lint
```

Use `npm.cmd` instead of `npm` if PowerShell requires it. A successful
build checks whether the frontend compiles; it does not prove that
backend endpoints or database operations work.

## Environment configuration

The project may use environment variables to configure the backend API
base URL. Start with `.env.example` and the current implementation in
`src/services/api.js`.

1.  Copy `.env.example` to a local `.env` file inside
    `application/frontend/`.
2.  Set the API base URL to the address where the Flask backend is
    running.
3.  Use the exact variable name read by the current frontend code. For a
    Vite-exposed variable, the name normally begins with `VITE_`, but do
    not rename it without updating the code.
4.  Restart the Vite development server after changing environment
    variables.

Example only---replace the value and variable name with those expected
by the committed code:

``` dotenv
VITE_API_BASE_URL=http://127.0.0.1:5000
```

Do not put passwords, database credentials, private API keys, or other
secrets in Vite environment variables. Values exposed to browser code
are not secret.

## API integration

The frontend's shared request logic is located in:

``` text
src/services/api.js
```

This module should be the primary place to configure the API base URL,
shared request headers, response parsing, and common error handling.

### Coordinate the API contract

Before relying on a frontend workflow, confirm the following with the
backend developer:

-   Exact route paths and HTTP methods.
-   Request body fields and expected data types.
-   Response JSON shape and status codes.
-   Authentication method and where credentials/session state are
    stored.
-   Role names and authorization rules.
-   Validation and error-response format.
-   CORS configuration for the local frontend origin.
-   How to start the backend and seed or create test data.

Any endpoint names shown in frontend code or integration notes should be
treated as **proposed or implementation-specific until confirmed against
the actual Flask routes**. Do not assume that a UI route automatically
exists on the backend.

### Suggested integration checklist

For each frontend API call:

1.  Match the request method and URL to the backend route.
2.  Match request and response fields to the backend's schema.
3.  Handle loading, success, empty, and error states.
4.  Show understandable feedback when the server is unavailable or
    rejects the request.
5.  Test the call with the backend running.
6.  Confirm that any created or updated record persists as expected.
7.  Test unauthorized and forbidden responses for protected actions.

Avoid hardcoding backend URLs throughout JSX. Keep configuration
centralized and avoid swallowing errors silently.

## Authentication and authorization

Authentication must be implemented as a coordinated frontend/backend
flow.

-   The frontend may control which screens are shown based on sign-in
    state.
-   The backend must validate credentials and authorize every protected
    request.
-   Customer and admin experiences should use the role information
    defined by the backend.
-   Do not rely on client-side navigation guards as a security boundary.
-   Do not log passwords, access tokens, or other sensitive
    authentication information.
-   Agree with the backend developer on token/session lifetime, logout
    behavior, and handling expired sessions.

Until this flow has been integrated and tested, treat sign-in and
role-specific screens as frontend UI rather than proof of secure access
control.

## Development workflow

1.  Pull the latest version of the `frontend` branch.
2.  Make changes inside `application/frontend/` unless the task
    explicitly concerns shared project files.
3.  Run the development server and check the affected screens.
4.  Run the available lint and build commands from `package.json`.
5.  Check browser developer tools for React errors, failed network
    requests, and missing assets.
6.  Review the Git diff before committing.
7.  Commit and push the work to the `frontend` branch.

Keep components readable, reuse styles where practical, and avoid
introducing a new dependency for functionality already available in the
project.

## Git workflow

The frontend work belongs on the `frontend` branch.

``` powershell
git switch frontend
git pull origin frontend
```

After making and checking changes:

``` powershell
git status
git diff
git add application/frontend/
git diff --cached
git commit -m "Update AutoDB frontend"
git push origin frontend
```

Use a commit message that describes the actual change. If the
repository's branch policy requires pull requests, push the branch and
open a pull request instead of merging directly.

### Files that should not be committed

-   `node_modules/`
-   Local `.env` files containing machine-specific configuration or
    secrets
-   Build output or temporary files unless the project explicitly
    requires them
-   Editor caches and operating-system-generated files

Keep `.env.example` in version control, but ensure it contains
placeholders only. The frontend `.gitignore` should exclude
`node_modules/`, local environment files, and generated output.

## Troubleshooting

### `npm` is blocked in PowerShell

Try `npm.cmd` instead of `npm`, for example:

``` powershell
npm.cmd install
npm.cmd run dev
```

### Vite reports a parsing or duplicate declaration error

-   Open the file and inspect the reported line.
-   Check for duplicate imports or duplicate declarations such as
    `useState`.
-   Confirm that a component or function has not been pasted into the
    file twice.
-   Save the file and allow Vite to reload.

### The page loads but API actions fail

-   Confirm the Flask backend is running.
-   Check the API base URL in the local environment file.
-   Confirm the route, HTTP method, request payload, and response shape
    with the backend branch.
-   Check browser developer tools for network errors and CORS failures.
-   Confirm that the backend is listening on the expected host and port.

### The car model does not appear

-   Confirm `public/models/porsche.glb` exists.
-   Check the asset URL used by `CarScene.jsx`.
-   Inspect the browser console for failed asset requests or rendering
    errors.
-   Test with a supported browser and check whether the existing static
    image fallback is available.

### Styles or pages appear broken after a change

-   Check `App.css` and `index.css` for conflicting global selectors.
-   Inspect responsive styles at a narrow viewport.
-   Verify that JSX class names match the CSS selectors.
-   Review the last diff and isolate the change that introduced the
    problem.

### Git reports LF/CRLF line-ending warnings on Windows

These warnings commonly indicate that Git will normalize line endings
according to repository settings. They are not, by themselves, a failed
`git add`. Check `git status` and review the staged diff before
committing.

### `node_modules` is missing from GitHub

This is expected. Dependencies should be restored from `package.json`
and `package-lock.json` using `npm ci`; `node_modules/` should not be
committed.

## Current status and integration checklist

This README describes the frontend structure and intended user flows.
The following should be checked against the actual branch and backend
before declaring the complete application integrated:

-   [ ] Frontend dependencies install cleanly from the lockfile.
-   [ ] The Vite development server starts successfully.
-   [ ] Production build and lint commands pass, if configured.
-   [ ] Landing page and car visual load without console errors.
-   [ ] Navigation links and buttons lead to their intended
    destinations.
-   [ ] Sign-in is connected to the real backend authentication route.
-   [ ] Customer dashboard uses real API data where required.
-   [ ] Booking form validates input and persists bookings through the
    backend.
-   [ ] Service history displays backend records.
-   [ ] Admin screens are connected to implemented admin routes.
-   [ ] Backend enforces role permissions for all protected operations.
-   [ ] Loading, empty, error, and success states are tested.
-   [ ] API base URL and CORS settings work in the local environment.
-   [ ] `.env` and `node_modules/` are excluded from Git.
-   [ ] README details and endpoint documentation match the current
    code.

A checkbox should be marked complete only after the behavior has been
tested. A screen existing in React does not mean the corresponding
backend operation is complete.

## Security notes

-   Never commit passwords, tokens, database credentials, or secret
    keys.
-   Do not store sensitive secrets in `VITE_` variables; they are
    exposed to client-side code.
-   Treat all browser-submitted data as untrusted.
-   Backend validation and authorization are required even if the
    frontend validates forms or hides admin controls.
-   Use HTTPS for deployed environments and follow the project's
    approved session/token handling design.

## Contributing

Before submitting frontend changes:

1.  Keep changes focused and consistent with the existing visual system.
2.  Confirm that the application still starts and builds.
3.  Test the screens affected by the change.
4.  Confirm any API contract changes with the backend developer.
5.  Review the staged files to ensure no local secrets or
    `node_modules/` are included.
6.  Update this README when setup instructions, scripts, pages, assets,
    or integration behavior change.

------------------------------------------------------------------------

**Documentation note:** This file is intended for the `frontend` branch.
Keep the root project README, backend README, and database documentation
aligned at the project level, but do not duplicate backend
implementation details here unless they are needed to explain frontend
integration.
