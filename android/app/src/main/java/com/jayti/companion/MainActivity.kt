package com.jayti.companion

import android.Manifest
import android.annotation.SuppressLint
import android.app.Activity
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Bundle
import android.os.Environment
import android.provider.MediaStore
import android.webkit.*
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat
import androidx.core.content.FileProvider
import androidx.core.splashscreen.SplashScreen.Companion.installSplashScreen
import androidx.core.view.WindowCompat
import androidx.swiperefreshlayout.widget.SwipeRefreshLayout
import com.jayti.companion.databinding.ActivityMainBinding
import java.io.File
import java.text.SimpleDateFormat
import java.util.*

class MainActivity : AppCompatActivity() {

    private lateinit var binding: ActivityMainBinding
    private var filePathCallback: ValueCallback<Array<Uri>>? = null
    private var cameraPhotoUri: Uri? = null

    // ── Activity result launchers ─────────────────────────────────────────────
    private val fileChooserLauncher = registerForActivityResult(
        ActivityResultContracts.StartActivityForResult()
    ) { result ->
        if (result.resultCode == Activity.RESULT_OK) {
            val data = result.data
            val uris: Array<Uri>? = when {
                data?.clipData != null -> Array(data.clipData!!.itemCount) { i ->
                    data.clipData!!.getItemAt(i).uri
                }
                data?.data != null -> arrayOf(data.data!!)
                cameraPhotoUri != null -> arrayOf(cameraPhotoUri!!)
                else -> null
            }
            filePathCallback?.onReceiveValue(uris)
        } else {
            filePathCallback?.onReceiveValue(null)
        }
        filePathCallback = null
        cameraPhotoUri = null
    }

    private val locationPermissionLauncher = registerForActivityResult(
        ActivityResultContracts.RequestMultiplePermissions()
    ) { /* Permission result handled in WebChromeClient */ }

    private val notificationPermissionLauncher = registerForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { /* Push notification permission */ }

    // ── Lifecycle ─────────────────────────────────────────────────────────────
    override fun onCreate(savedInstanceState: Bundle?) {
        installSplashScreen()
        super.onCreate(savedInstanceState)

        WindowCompat.setDecorFitsSystemWindows(window, false)
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)

        setupWebView()
        setupSwipeRefresh()

        // Request notification permission on Android 13+
        if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.TIRAMISU) {
            if (ContextCompat.checkSelfPermission(this, Manifest.permission.POST_NOTIFICATIONS)
                != PackageManager.PERMISSION_GRANTED) {
                notificationPermissionLauncher.launch(Manifest.permission.POST_NOTIFICATIONS)
            }
        }

        // Load app or restore state
        if (savedInstanceState != null) {
            binding.webView.restoreState(savedInstanceState)
        } else {
            binding.webView.loadUrl(BuildConfig.APP_URL)
        }
    }

    override fun onSaveInstanceState(outState: Bundle) {
        super.onSaveInstanceState(outState)
        binding.webView.saveState(outState)
    }

    override fun onBackPressed() {
        if (binding.webView.canGoBack()) {
            binding.webView.goBack()
        } else {
            super.onBackPressed()
        }
    }

    // ── WebView Setup ─────────────────────────────────────────────────────────
    @SuppressLint("SetJavaScriptEnabled")
    private fun setupWebView() {
        val webView = binding.webView
        val settings = webView.settings

        // JavaScript + modern web features
        settings.javaScriptEnabled = true
        settings.domStorageEnabled = true
        settings.databaseEnabled = true
        settings.javaScriptCanOpenWindowsAutomatically = true

        // File access for uploads
        settings.allowFileAccess = true
        settings.allowContentAccess = true

        // Media autoplay (needed for voice diary)
        settings.mediaPlaybackRequiresUserGesture = false

        // Viewport handling (ensures PWA meta-viewport is respected)
        settings.useWideViewPort = true
        settings.loadWithOverviewMode = true

        // Caching — use cache when available (offline-capable PWA)
        settings.cacheMode = WebSettings.LOAD_DEFAULT

        // Modern UA so the site doesn't serve a mobile-stripped view
        settings.userAgentString = settings.userAgentString + " JaytiAndroid/1.0"

        // Safe browsing
        WebView.enableSlowWholeDocumentDraw()

        webView.webViewClient = JaytiWebViewClient(binding.swipeRefreshLayout)
        webView.webChromeClient = JaytiWebChromeClient()

        // JavaScript bridge — lets web pages call Android APIs
        webView.addJavascriptInterface(JaytiJsBridge(this), "JaytiAndroid")
    }

    private fun setupSwipeRefresh() {
        binding.swipeRefreshLayout.apply {
            setColorSchemeColors(
                ContextCompat.getColor(context, R.color.pink_primary)
            )
            setOnRefreshListener {
                binding.webView.reload()
            }
        }
    }

    // ── WebViewClient ─────────────────────────────────────────────────────────
    inner class JaytiWebViewClient(
        private val swipeRefresh: SwipeRefreshLayout
    ) : WebViewClient() {

        override fun onPageStarted(view: WebView?, url: String?, favicon: android.graphics.Bitmap?) {
            super.onPageStarted(view, url, favicon)
        }

        override fun onPageFinished(view: WebView?, url: String?) {
            super.onPageFinished(view, url)
            swipeRefresh.isRefreshing = false
        }

        override fun onReceivedError(
            view: WebView?, request: WebResourceRequest?, error: WebResourceError?
        ) {
            super.onReceivedError(view, request, error)
            swipeRefresh.isRefreshing = false
            if (request?.isForMainFrame == true) {
                // Load offline fallback page
                view?.loadData(offlineHtml(), "text/html", "UTF-8")
            }
        }

        override fun shouldOverrideUrlLoading(view: WebView?, request: WebResourceRequest?): Boolean {
            val url = request?.url?.toString() ?: return false
            return when {
                // Keep jaytibirthday.in URLs inside the app
                url.startsWith("https://jaytibirthday.in") -> false
                url.startsWith("https://www.jaytibirthday.in") -> false
                // Open external URLs in the device browser
                url.startsWith("http") -> {
                    startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(url)))
                    true
                }
                // tel:, mailto:, etc.
                else -> {
                    try {
                        startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(url)))
                    } catch (_: Exception) {}
                    true
                }
            }
        }
    }

    // ── WebChromeClient ───────────────────────────────────────────────────────
    inner class JaytiWebChromeClient : WebChromeClient() {

        override fun onShowFileChooser(
            webView: WebView?,
            filePathCallback: ValueCallback<Array<Uri>>?,
            fileChooserParams: FileChooserParams?
        ): Boolean {
            this@MainActivity.filePathCallback?.onReceiveValue(null)
            this@MainActivity.filePathCallback = filePathCallback

            val intentList = mutableListOf<Intent>()

            // Camera intent
            val photoFile = createImageFile()
            cameraPhotoUri = FileProvider.getUriForFile(
                this@MainActivity,
                "${packageName}.fileprovider",
                photoFile
            )
            val cameraIntent = Intent(MediaStore.ACTION_IMAGE_CAPTURE).apply {
                putExtra(MediaStore.EXTRA_OUTPUT, cameraPhotoUri)
            }
            intentList.add(cameraIntent)

            // Gallery/file intent
            val galleryIntent = Intent(Intent.ACTION_GET_CONTENT).apply {
                type = "image/*"
                putExtra(Intent.EXTRA_ALLOW_MULTIPLE, true)
            }

            val chooserIntent = Intent.createChooser(galleryIntent, "Select Image").apply {
                putExtra(Intent.EXTRA_INITIAL_INTENTS, intentList.toTypedArray())
            }
            fileChooserLauncher.launch(chooserIntent)
            return true
        }

        override fun onGeolocationPermissionsShowPrompt(
            origin: String?,
            callback: GeolocationPermissions.Callback?
        ) {
            val fineGranted = ContextCompat.checkSelfPermission(
                this@MainActivity, Manifest.permission.ACCESS_FINE_LOCATION
            ) == PackageManager.PERMISSION_GRANTED

            if (fineGranted) {
                callback?.invoke(origin, true, false)
            } else {
                locationPermissionLauncher.launch(
                    arrayOf(
                        Manifest.permission.ACCESS_FINE_LOCATION,
                        Manifest.permission.ACCESS_COARSE_LOCATION
                    )
                )
                // Re-invoke once permission is (or isn't) granted — simplified here;
                // production apps should store the callback and invoke after the result.
                callback?.invoke(origin, fineGranted, false)
            }
        }

        override fun onPermissionRequest(request: PermissionRequest?) {
            request?.grant(request.resources)
        }

        override fun onConsoleMessage(consoleMessage: ConsoleMessage?): Boolean {
            if (BuildConfig.DEBUG) {
                android.util.Log.d(
                    "JaytiWebView",
                    "[${consoleMessage?.sourceId()}:${consoleMessage?.lineNumber()}] ${consoleMessage?.message()}"
                )
            }
            return true
        }
    }

    // ── Helpers ───────────────────────────────────────────────────────────────
    private fun createImageFile(): File {
        val timestamp = SimpleDateFormat("yyyyMMdd_HHmmss", Locale.getDefault()).format(Date())
        val storageDir = getExternalFilesDir(Environment.DIRECTORY_PICTURES)
        return File.createTempFile("JAYTI_${timestamp}_", ".jpg", storageDir)
    }

    private fun offlineHtml() = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
          <meta charset="utf-8">
          <meta name="viewport" content="width=device-width, initial-scale=1">
          <title>No connection</title>
          <style>
            body{display:flex;align-items:center;justify-content:center;flex-direction:column;
                 min-height:100vh;margin:0;font-family:Georgia,serif;background:#fff5f7;color:#c2185b}
            .heart{font-size:3rem;margin-bottom:1rem}
            h2{margin:0 0 .5rem}
            p{color:#888;font-size:.9rem;text-align:center;max-width:260px}
            button{margin-top:1.5rem;padding:.7rem 1.8rem;border:none;border-radius:8px;
                   background:#e91e8c;color:#fff;font-size:1rem;cursor:pointer}
          </style>
        </head>
        <body>
          <div class="heart">💝</div>
          <h2>No internet</h2>
          <p>Check your connection and try again.</p>
          <button onclick="window.location.reload()">Retry</button>
        </body>
        </html>
    """.trimIndent()
}
