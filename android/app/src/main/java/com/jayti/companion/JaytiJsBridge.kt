package com.jayti.companion

import android.content.Context
import android.webkit.JavascriptInterface
import android.widget.Toast
import org.json.JSONObject

/**
 * JavaScript interface injected into the WebView as `window.JaytiAndroid`.
 *
 * The web app can call these methods directly from JS:
 *   JaytiAndroid.showToast("Hello!")
 *   JaytiAndroid.getAppVersion()
 *   JaytiAndroid.vibrate()
 */
class JaytiJsBridge(private val context: Context) {

    @JavascriptInterface
    fun showToast(message: String) {
        Toast.makeText(context, message, Toast.LENGTH_SHORT).show()
    }

    @JavascriptInterface
    fun getAppVersion(): String {
        return try {
            val pInfo = context.packageManager.getPackageInfo(context.packageName, 0)
            JSONObject().apply {
                put("versionName", pInfo.versionName)
                put("versionCode", pInfo.longVersionCode)
                put("platform", "android")
                put("env", BuildConfig.ENV)
            }.toString()
        } catch (e: Exception) {
            "{\"error\": \"${e.message}\"}"
        }
    }

    @JavascriptInterface
    fun vibrate() {
        val vibrator = context.getSystemService(android.os.Vibrator::class.java)
        if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.O) {
            vibrator?.vibrate(
                android.os.VibrationEffect.createOneShot(
                    100, android.os.VibrationEffect.DEFAULT_AMPLITUDE
                )
            )
        } else {
            @Suppress("DEPRECATION")
            vibrator?.vibrate(100)
        }
    }

    @JavascriptInterface
    fun isNativeApp(): Boolean = true
}
