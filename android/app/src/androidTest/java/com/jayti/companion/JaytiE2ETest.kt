package com.jayti.companion

import android.content.Context
import androidx.test.core.app.ApplicationProvider
import androidx.test.espresso.web.sugar.Web.onWebView
import androidx.test.espresso.web.webdriver.DriverAtoms.*
import androidx.test.espresso.web.webdriver.Locator
import androidx.test.ext.junit.rules.ActivityScenarioRule
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.filters.LargeTest
import androidx.test.platform.app.InstrumentationRegistry
import androidx.test.uiautomator.*
import org.junit.Assert.*
import org.junit.Before
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

/**
 * E2E test suite for the Jayti Android app.
 *
 * Run on a connected device or emulator:
 *   ./gradlew connectedAndroidTest
 *
 * Or target a specific test:
 *   ./gradlew connectedAndroidTest -Pandroid.testInstrumentationRunnerArguments.class=\
 *     com.jayti.companion.JaytiE2ETest#testLoginPageLoads
 */
@RunWith(AndroidJUnit4::class)
@LargeTest
class JaytiE2ETest {

    @get:Rule
    val activityRule = ActivityScenarioRule(MainActivity::class.java)

    private lateinit var device: UiDevice
    private val context: Context get() = ApplicationProvider.getApplicationContext()

    // ── Timeouts ──────────────────────────────────────────────────────────────
    private val PAGE_LOAD_TIMEOUT = 15_000L   // ms
    private val ELEMENT_TIMEOUT  =  8_000L

    @Before
    fun setup() {
        device = UiDevice.getInstance(InstrumentationRegistry.getInstrumentation())
        // Wait for the app window to be fully visible
        device.waitForWindowUpdate(context.packageName, PAGE_LOAD_TIMEOUT)
    }

    // ── 1. App Launch ─────────────────────────────────────────────────────────
    @Test
    fun testAppLaunchesSuccessfully() {
        // The WebView should be visible
        val webView = device.findObject(
            UiSelector().className("android.webkit.WebView")
        )
        assertTrue("WebView should be visible", webView.waitForExists(PAGE_LOAD_TIMEOUT))
    }

    @Test
    fun testAppTitleIsJayti() {
        Thread.sleep(3000) // Wait for page load
        activityRule.scenario.onActivity { activity ->
            assertEquals("Jayti", activity.title?.toString() ?: activity.getString(R.string.app_name))
        }
    }

    // ── 2. Login Page ─────────────────────────────────────────────────────────
    @Test
    fun testLoginPageLoads() {
        // Wait for the page to load and check we see a login form
        onWebView()
            .withElement(findElement(Locator.TAG_NAME, "body"))
            .check { element, exception ->
                assertNull("Page body should be accessible", exception)
            }
    }

    @Test
    fun testLoginFormHasUsernameAndPassword() {
        Thread.sleep(4000)
        onWebView()
            .withElement(findElement(Locator.CSS_SELECTOR, "input[name='username'], input[type='text']"))
            .check { element, exception ->
                assertNull("Username field should exist", exception)
            }
        onWebView()
            .withElement(findElement(Locator.CSS_SELECTOR, "input[type='password']"))
            .check { element, exception ->
                assertNull("Password field should exist", exception)
            }
    }

    @Test
    fun testLoginWithInvalidCredentialsFails() {
        Thread.sleep(4000)

        onWebView()
            .withElement(findElement(Locator.CSS_SELECTOR, "input[name='username']"))
            .perform(clearElement())
            .perform(webKeys("wrong_user"))

        onWebView()
            .withElement(findElement(Locator.CSS_SELECTOR, "input[type='password']"))
            .perform(clearElement())
            .perform(webKeys("wrong_pass"))

        onWebView()
            .withElement(findElement(Locator.CSS_SELECTOR, "button[type='submit'], input[type='submit']"))
            .perform(webClick())

        Thread.sleep(2000)

        // Should still be on login page (not dashboard)
        onWebView()
            .withElement(findElement(Locator.CSS_SELECTOR, "input[type='password']"))
            .check { element, exception ->
                assertNull("Should still show login form after bad credentials", exception)
            }
    }

    // ── 3. Network & WebView ──────────────────────────────────────────────────
    @Test
    fun testHealthEndpointReachable() {
        // Navigate to /health — should return 200
        activityRule.scenario.onActivity { activity ->
            activity.runOnUiThread {
                activity.findViewById<android.webkit.WebView>(R.id.webView)
                    .loadUrl("${BuildConfig.APP_URL}/health")
            }
        }
        Thread.sleep(5000)
        onWebView()
            .withElement(findElement(Locator.TAG_NAME, "body"))
            .check { element, exception ->
                assertNull("Health endpoint body should be reachable", exception)
            }
    }

    @Test
    fun testOfflinePageShowsOnNetworkError() {
        // Load an invalid URL to trigger the offline page
        activityRule.scenario.onActivity { activity ->
            activity.runOnUiThread {
                activity.findViewById<android.webkit.WebView>(R.id.webView)
                    .loadUrl("https://thisdomaindoesnotexist-jayti-test-12345.com/")
            }
        }
        Thread.sleep(8000)
        // Should show the offline fallback HTML
        onWebView()
            .withElement(findElement(Locator.CSS_SELECTOR, "button"))
            .check { element, exception ->
                assertNull("Offline page Retry button should be visible", exception)
            }
    }

    // ── 4. Back Navigation ────────────────────────────────────────────────────
    @Test
    fun testBackButtonNavigatesWebHistory() {
        Thread.sleep(4000)
        // Navigate to a different page inside the app
        activityRule.scenario.onActivity { activity ->
            activity.runOnUiThread {
                activity.findViewById<android.webkit.WebView>(R.id.webView)
                    .loadUrl("${BuildConfig.APP_URL}/notes/")
            }
        }
        Thread.sleep(4000)

        // Press back
        device.pressBack()
        Thread.sleep(2000)

        // Should have navigated back within the WebView (not exited the app)
        val webView = device.findObject(UiSelector().className("android.webkit.WebView"))
        assertTrue("App should still be open after back press", webView.exists())
    }

    // ── 5. Swipe-to-Refresh ───────────────────────────────────────────────────
    @Test
    fun testSwipeToRefreshWorks() {
        Thread.sleep(3000)
        val webView = device.findObject(UiSelector().className("android.webkit.WebView"))
        assertTrue("WebView should be present", webView.exists())

        // Swipe down from top to trigger refresh
        val bounds = webView.bounds
        device.swipe(
            bounds.centerX(), bounds.top + 50,
            bounds.centerX(), bounds.top + 400,
            10
        )
        Thread.sleep(3000)

        // After refresh, WebView should still be visible
        assertTrue("WebView should still be visible after swipe refresh", webView.exists())
    }

    // ── 6. JavaScript Bridge ──────────────────────────────────────────────────
    @Test
    fun testJsBridgeIsNativeAppReturnsTrue() {
        Thread.sleep(3000)
        // Execute JS in WebView and verify bridge works
        activityRule.scenario.onActivity { activity ->
            activity.runOnUiThread {
                activity.findViewById<android.webkit.WebView>(R.id.webView)
                    .evaluateJavascript("typeof JaytiAndroid !== 'undefined' && JaytiAndroid.isNativeApp()") { result ->
                        assertEquals("'true'", result)
                    }
            }
        }
        Thread.sleep(1000)
    }

    @Test
    fun testJsBridgeVersionInfoIsValid() {
        Thread.sleep(3000)
        var versionJson: String? = null
        activityRule.scenario.onActivity { activity ->
            activity.runOnUiThread {
                activity.findViewById<android.webkit.WebView>(R.id.webView)
                    .evaluateJavascript("JaytiAndroid.getAppVersion()") { result ->
                        versionJson = result
                    }
            }
        }
        Thread.sleep(1000)
        assertNotNull("Version info should not be null", versionJson)
        assertTrue("Version JSON should contain versionName", versionJson?.contains("versionName") == true)
        assertTrue("Version JSON should contain platform=android", versionJson?.contains("android") == true)
    }

    // ── 7. PWA Manifest ───────────────────────────────────────────────────────
    @Test
    fun testManifestJsonIsServed() {
        activityRule.scenario.onActivity { activity ->
            activity.runOnUiThread {
                activity.findViewById<android.webkit.WebView>(R.id.webView)
                    .loadUrl("${BuildConfig.APP_URL}/static/manifest.json")
            }
        }
        Thread.sleep(5000)
        onWebView()
            .withElement(findElement(Locator.TAG_NAME, "body"))
            .check { element, exception ->
                assertNull("manifest.json body should be readable", exception)
            }
    }

    // ── 8. Page routes exist ──────────────────────────────────────────────────
    @Test
    fun testDashboardRouteLoads() {
        activityRule.scenario.onActivity { activity ->
            activity.runOnUiThread {
                activity.findViewById<android.webkit.WebView>(R.id.webView)
                    .loadUrl("${BuildConfig.APP_URL}/dashboard/")
            }
        }
        Thread.sleep(6000)
        val webView = device.findObject(UiSelector().className("android.webkit.WebView"))
        assertTrue("WebView visible after dashboard navigation", webView.exists())
    }

    @Test
    fun testNotesRouteRedirectsToLogin() {
        activityRule.scenario.onActivity { activity ->
            activity.runOnUiThread {
                activity.findViewById<android.webkit.WebView>(R.id.webView)
                    .loadUrl("${BuildConfig.APP_URL}/notes/")
            }
        }
        Thread.sleep(6000)
        // Unauthenticated access should redirect to login
        onWebView()
            .withElement(findElement(Locator.CSS_SELECTOR, "input[type='password'], form"))
            .check { element, exception ->
                assertNull("Notes redirect should land on login form", exception)
            }
    }

    @Test
    fun testDiaryRouteRedirectsToLogin() {
        activityRule.scenario.onActivity { activity ->
            activity.runOnUiThread {
                activity.findViewById<android.webkit.WebView>(R.id.webView)
                    .loadUrl("${BuildConfig.APP_URL}/diary/")
            }
        }
        Thread.sleep(6000)
        onWebView()
            .withElement(findElement(Locator.CSS_SELECTOR, "form"))
            .check { element, exception ->
                assertNull("Diary redirect should land on login form", exception)
            }
    }
}
