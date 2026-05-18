package com.jayti.companion

import android.app.Application
import android.webkit.WebView

class JaytiApp : Application() {
    override fun onCreate() {
        super.onCreate()
        // Enable WebView debugging in debug builds so Chrome DevTools
        // (chrome://inspect) can attach to the in-app WebView during testing.
        if (BuildConfig.DEBUG) {
            WebView.setWebContentsDebuggingEnabled(true)
        }
    }
}
