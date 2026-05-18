// Firebase SDK initialisation — project: jpfinal-c9340
// Config is injected by Django context processor (firebase_config).
// The hardcoded fallback below is safe to expose (public web config).

const FIREBASE_FALLBACK = {
  apiKey: "AIzaSyCSrVXiA9_AR_Asp-1h4KeRTWxG0758KA4",
  authDomain: "jpfinal-c9340.firebaseapp.com",
  projectId: "jpfinal-c9340",
  storageBucket: "jpfinal-c9340.firebasestorage.app",
  messagingSenderId: "588713240952",
  appId: "1:588713240952:web:2b25d423858efc11fe008d"
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
    console.info('[Firebase] Initialised — project: jpfinal-c9340');

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
