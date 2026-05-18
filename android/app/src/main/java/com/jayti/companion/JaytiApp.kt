package com.jayti.companion

import android.app.Application
import android.webkit.WebView
import com.google.firebase.FirebaseApp
import com.google.firebase.analytics.FirebaseAnalytics
import com.google.firebase.crashlytics.FirebaseCrashlytics

class JaytiApp : Application() {

    lateinit var analytics: FirebaseAnalytics
        private set

    override fun onCreate() {
        super.onCreate()

        // Initialise Firebase (reads google-services.json automatically)
        FirebaseApp.initializeApp(this)

        // Analytics
        analytics = FirebaseAnalytics.getInstance(this)

        // Crashlytics — disable data collection in debug builds
        FirebaseCrashlytics.getInstance().setCrashlyticsCollectionEnabled(!BuildConfig.DEBUG)

        // WebView debugging in debug builds (chrome://inspect)
        if (BuildConfig.DEBUG) {
            WebView.setWebContentsDebuggingEnabled(true)
        }
    }
}
