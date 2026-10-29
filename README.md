# Vehicle Service Management System

## Project Overview
A DBMS project for managing vehicle servicing operations using MySQL and an application interface.

## Database
- Database name: `VehicleServiceDB`
- Database platform: MySQL
- Existing baseline: 10 core relational tables

## Branches
- `main` — stable, submission-ready version
- `frontend` — frontend development
- `backend` — backend and database integration logic
- `integration` — combined application and integration testing

## Project Structure
- `application/frontend/` — React + Vite frontend source and dependencies
- `application/backend/` — Flask API, authentication and database connectivity
- `database/` — MySQL schema, sample data, migrations and queries
- `documentation/` — report and ER diagram
- `presentation/` — final presentation
- `testing/` — test cases and verified results

## Contribution Rules
1. Work on the assigned branch.
2. Commit only relevant project files.
3. Do not commit passwords, API keys or private configuration.
4. Document setup instructions and dependencies.
5. Open a pull request before merging changes into `integration`.
6. Test integrated changes before merging them into `main`.

## Current Status
Development and integration are in progress. Testing results will be added after execution and verification.

## Local Development
1. Configure `application/backend/.env` with `JWT_SECRET_KEY` and your local MySQL connection settings.
2. In `application/backend/`, install `requirements.txt` and run `python app.py`.
3. In `application/frontend/`, run `npm install` and `npm run dev`.
4. Configure and verify `VehicleServiceDB` using the SQL files in `database/`; apply `inspection_estimate_migration.sql` to an existing database before testing inspection and estimate approval.
5. Never commit `.env` files, passwords, or private configuration.
