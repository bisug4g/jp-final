const firebaseConfigElement = document.getElementById('firebase-config');

if (!firebaseConfigElement) {
  console.info('[Firebase] No config element found; skipping initialization.');
} else {
  let firebaseConfig;

  try {
    firebaseConfig = JSON.parse(firebaseConfigElement.textContent);
  } catch (error) {
    console.error('[Firebase] Invalid config payload.', error);
  }

  const hasRequiredConfig = firebaseConfig
    && firebaseConfig.enabled
    && firebaseConfig.apiKey
    && firebaseConfig.projectId
    && firebaseConfig.appId;

  window.JaytiFirebase = {
    enabled: false,
    analyticsEnabled: false,
    config: firebaseConfig || null,
  };

  if (!hasRequiredConfig) {
    console.info('[Firebase] Public config not set; skipping initialization.');
  } else {
    initializeFirebase(firebaseConfig);
  }
}

async function initializeFirebase(firebaseConfig) {
  try {
    const { initializeApp } = await import('https://www.gstatic.com/firebasejs/10.14.1/firebase-app.js');
    const app = initializeApp({
      apiKey: firebaseConfig.apiKey,
      authDomain: firebaseConfig.authDomain,
      projectId: firebaseConfig.projectId,
      storageBucket: firebaseConfig.storageBucket,
      messagingSenderId: firebaseConfig.messagingSenderId,
      appId: firebaseConfig.appId,
      measurementId: firebaseConfig.measurementId,
    });

    window.JaytiFirebase.app = app;
    window.JaytiFirebase.enabled = true;

    if (!firebaseConfig.measurementId) {
      console.info('[Firebase] Measurement ID not set; analytics disabled.');
      return;
    }

    const { getAnalytics, isSupported } = await import('https://www.gstatic.com/firebasejs/10.14.1/firebase-analytics.js');
    const analyticsSupported = await isSupported();
    if (!analyticsSupported) {
      console.info('[Firebase] Analytics not supported in this browser context.');
      return;
    }

    window.JaytiFirebase.analytics = getAnalytics(app);
    window.JaytiFirebase.analyticsEnabled = true;
  } catch (error) {
    console.error('[Firebase] Initialization failed.', error);
  }
}
