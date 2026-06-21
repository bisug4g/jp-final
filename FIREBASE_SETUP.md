# Firebase Full-Stack Setup

## Project: jpfinal-c9340

## 1. Enable Firebase services

In the Firebase console for `jpfinal-c9340`:
- **Authentication** → Enable Email/Password provider
- **Firestore** → Create database (production mode, asia-south1)
- **Functions** → Already configured

## 2. Add Firebase config to frontend

Copy `frontend/.env.example` to `frontend/.env.local` and fill in values from Firebase console → Project Settings → Your apps:

```
VITE_FIREBASE_API_KEY=<from console>
VITE_FIREBASE_AUTH_DOMAIN=jpfinal-c9340.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=jpfinal-c9340
VITE_FIREBASE_STORAGE_BUCKET=jpfinal-c9340.appspot.com
VITE_FIREBASE_MESSAGING_SENDER_ID=<from console>
VITE_FIREBASE_APP_ID=<from console>
VITE_API_URL=https://asia-south1-jpfinal-c9340.cloudfunctions.net/api
```

## 3. Add Gemini API key to Firebase secrets

```bash
firebase functions:secrets:set GEMINI_API_KEY
# Paste your Gemini API key when prompted
```

## 4. Create the user account

In Firebase console → Authentication → Add user:
- Email: your email
- Password: your password

## 5. Deploy

```bash
# Build frontend first
cd frontend
npm run build

# Deploy everything
cd ..
firebase deploy
```

Or deploy separately:
```bash
firebase deploy --only hosting    # Frontend
firebase deploy --only functions  # Backend
firebase deploy --only firestore  # Rules + indexes
```

## 6. Local development

```bash
# Terminal 1 — Firebase emulators
firebase emulators:start --only functions,firestore,auth

# Terminal 2 — Vite dev server
cd frontend
cp .env.example .env.local
# Fill in VITE_FIREBASE_* values
npm run dev
```

## Architecture

```
Firebase Hosting  ─── React SPA (shadcn/ui + Tailwind)
       │
       ├── /api/** ─── Cloud Functions (Express, asia-south1)
       │                    ├── /notes
       │                    ├── /diary
       │                    ├── /goals + AI task generation
       │                    ├── /chat (Gemini 2.0 Flash)
       │                    └── /dashboard (activity, briefing, thought)
       │
Firebase Auth ─── Email/Password
Firestore ─────── /users/{uid}/{notes,diary,goals,chat,activity,briefings}
                  /daily_thoughts/{date}
```
