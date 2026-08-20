# Google Authentication Integration & Fixes

This document serves as a complete log of all the changes made to the codebase, database, environment variables, and infrastructure to successfully implement and debug Google Authentication.

## 1. Environment Variable Changes (`.env`)

Google Authentication requires the Client ID to be synced across the frontend and backend.

### What we changed:
- **Backend**: Added `GOOGLE_CLIENT_ID="474511502741-ftafb9rf41sia9i40uja5fj1higolm6v.apps.googleusercontent.com"` to `/backend/.env`.
- **Frontend**: Updated the hardcoded `GOOGLE_CLIENT_ID` variable in `/research-lab/src/components/AuthModal.tsx` to match the backend.

### What you ALWAYS need in your environment:
If you ever deploy this to production or set this up on a new machine, you MUST have:
1. **`GOOGLE_CLIENT_ID`** in the backend `.env`.
2. **`GOOGLE_CLIENT_ID`** accessible to the frontend (currently hardcoded in `AuthModal.tsx`, but ideally moved to `.env.local` as `VITE_GOOGLE_CLIENT_ID`).
3. **Google Cloud Console Configuration**: The exact URL of your frontend (e.g., `http://localhost:3000` or `https://your-domain.com`) **must** be added to the "Authorized JavaScript origins" in the Google Cloud Console.

---

## 2. Codebase Changes

### Frontend (`vite.config.ts`)
- **Change**: Hardcoded `port: 3000` into the Vite server configuration.
- **Why**: Google Identity Services strictly validates the origin port. Vite was randomly picking port `5173` or `5174`, which caused the Google popup to block access (`no registered origin - Error 401`). Forcing port `3000` ensures it matches what is registered in the Google Cloud Console.

### Backend (`app/services/auth_service.py`)
- **Change**: Added `clock_skew_in_seconds=60` to the `verify_oauth2_token` function.
- **Why**: When your computer's local clock is slightly out of sync with Google's servers (even by 10 seconds), Google's Python library rejects the token as "Token used too early". This 60-second buffer fixes that issue.

---

## 3. Database Changes (Alembic & PostgreSQL)

The authentication system crashed repeatedly because the database schema was severely out of sync with the Python models.

### What we did:
1. **Ran Migration 0003**: Applied the migration that added `google_sub`, `avatar_url`, and `last_login_at` to the `users` table so we could save Google profile data.
2. **Generated Missing Migration**: We discovered that previous developers had added several fields to the Python models (like `role` on the `users` table, and `cost_usd` on `payments`) but *forgot* to generate database migrations for them. 
3. **Applied Missing Migration**: We generated a new migration (`501d0a946e1a_add_missing_columns.py`) that added all these missing columns to the PostgreSQL database.
- **Why**: When the backend tried to create a new user, it attempted to insert the `role` field. Because the column didn't exist in the database, it threw a severe `UndefinedColumnError` crashing the login flow.

---

## 4. Infrastructure (Docker & Redis)

- **What we changed**: We manually started the Redis Docker container (`docker compose up -d redis`).
- **Why**: After a successful database insertion, the backend issues JWT authentication tokens and attempts to save the refresh token session in Redis. Because Redis was offline, the connection failed and caused a generic "500 Internal Server Error" on the frontend. Redis MUST be running for the authentication system to work.
