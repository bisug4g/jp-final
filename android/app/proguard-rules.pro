# Keep JavaScript bridge class and annotated methods intact (obfuscation would
# break the JS ↔ Android interface because method names are looked up by string)
-keepclassmembers class com.jayti.companion.JaytiJsBridge {
    @android.webkit.JavascriptInterface <methods>;
}
-keep class com.jayti.companion.JaytiJsBridge { *; }

# WebView internals
-keepclassmembers class * extends android.webkit.WebViewClient {
    public void *(android.webkit.WebView, java.lang.String, android.graphics.Bitmap);
    public boolean *(android.webkit.WebView, java.lang.String);
}
-keepclassmembers class * extends android.webkit.WebChromeClient {
    public void *(android.webkit.WebView, java.lang.String);
}

# Kotlin coroutines
-keepnames class kotlinx.coroutines.internal.MainDispatcherFactory {}
-keepnames class kotlinx.coroutines.CoroutineExceptionHandler {}
