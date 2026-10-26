# AutoDB frontend pages integration

## Files
- `src/App.jsx`: homepage plus auth, customer dashboard, booking, service history and admin dashboard.
- `src/App.css`: existing homepage styles plus page styles for the additional views.
- `src/services/api.js`: centralized API adapter for the proposed backend contract.
- `.env.example`: API base URL configuration example.

## Install / copy
Copy `src/App.jsx`, `src/App.css`, and `src/services/api.js` into the same locations in your Vite React project. Keep your existing `src/CarScene.jsx` and `public/models/porsche.glb` untouched.

## API configuration
Create a `.env` file in `application/frontend` based on `.env.example`. Set `VITE_API_BASE_URL` to the actual backend API prefix, then restart Vite.

The paths in `src/services/api.js` are proposed contracts, not confirmed existing routes. Align them with the backend before testing authentication and data loading. The frontend expects auth responses to contain `user` (or `account`) and a `token` (or `access_token`). User objects should include a `role` field with `customer` or `admin`.

## Security notes
- The registration form never lets the user choose an admin role.
- Client-side page routing is for navigation only. Enforce authentication, ownership checks and admin authorization on the backend.
- This version intentionally displays empty states or API errors instead of inventing customer/appointment records.
