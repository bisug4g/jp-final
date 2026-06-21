// Firebase SDK initialisation — project: jpfinal-bisu-2026
// Config is injected by Django context processor (firebase_config).
// The hardcoded fallback below is safe to expose (public web config).
// TODO: Replace REPLACE_WITH_* values with the actual web app config from
//       Firebase console → Project Settings → Your apps → Web app.

const FIREBASE_FALLBACK = {
  apiKey: "REPLACE_WITH_FIREBASE_API_KEY",
  authDomain: "jpfinal-bisu-2026.firebaseapp.com",
  projectId: "jpfinal-bisu-2026",
  storageBucket: "jpfinal-bisu-2026.firebasestorage.app",
  messagingSenderId: "REPLACE_WITH_MESSAGING_SENDER_ID",
  appId: "REPLACE_WITH_FIREBASE_APP_ID"
};

window.JaytiFirebase = { enabled: false, analyticsEnabled: false, config: null };

(async function initFirebase() {
  // Prefer Django-injected config (has enabled flag + measurementId)
  let config = null;
  const el = document.getElementById('firebase-config');
  if (el) {
    try {
      const parsed = JSON.parse(el.textContent);
      if (parsed && parsed.projectId) config = parsed;
    } catch (_) {}
  }
  // Fall back to hardcoded public config
  if (!config) config = { ...FIREBASE_FALLBACK, enabled: true };

  window.JaytiFirebase.config = config;

  if (!config.enabled && !config.apiKey) {
    console.info('[Firebase] Config not set; skipping init.');
    return;
  }

  try {
    const { initializeApp } = await import('https://www.gstatic.com/firebasejs/10.14.1/firebase-app.js');
    const app = initializeApp({
      apiKey:            config.apiKey            || FIREBASE_FALLBACK.apiKey,
      authDomain:        config.authDomain        || FIREBASE_FALLBACK.authDomain,
      projectId:         config.projectId         || FIREBASE_FALLBACK.projectId,
      storageBucket:     config.storageBucket     || FIREBASE_FALLBACK.storageBucket,
      messagingSenderId: config.messagingSenderId || FIREBASE_FALLBACK.messagingSenderId,
      appId:             config.appId             || FIREBASE_FALLBACK.appId,
      measurementId:     config.measurementId,
    });

    window.JaytiFirebase.app     = app;
    window.JaytiFirebase.enabled = true;
    console.info('[Firebase] Initialised — project: jpfinal-bisu-2026');

    // Analytics — only if measurementId is set
    if (config.measurementId) {
      const { getAnalytics, isSupported } = await import('https://www.gstatic.com/firebasejs/10.14.1/firebase-analytics.js');
      if (await isSupported()) {
        window.JaytiFirebase.analytics        = getAnalytics(app);
        window.JaytiFirebase.analyticsEnabled = true;
        console.info('[Firebase] Analytics enabled.');
      }
    }
  } catch (err) {
    console.error('[Firebase] Init failed:', err);
  }
})();
