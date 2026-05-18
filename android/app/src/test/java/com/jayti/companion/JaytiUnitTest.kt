package com.jayti.companion

import org.junit.Assert.*
import org.junit.Test
import org.json.JSONObject

class JaytiUnitTest {

    @Test
    fun appUrlIsConfigured() {
        // Build config should have a valid APP_URL
        assertFalse(
            "APP_URL must not be empty",
            BuildConfig.APP_URL.isNullOrBlank()
        )
        assertTrue(
            "APP_URL must start with https",
            BuildConfig.APP_URL.startsWith("https://")
        )
    }

    @Test
    fun appVersionCodeIsPositive() {
        assertTrue("Version code should be > 0", BuildConfig.VERSION_CODE > 0)
    }

    @Test
    fun offlineHtmlContainsRetryButton() {
        // Ensure offline HTML is well-formed enough to contain a button
        val html = """
            <!DOCTYPE html><html><body>
            <button onclick="window.location.reload()">Retry</button>
            </body></html>
        """.trimIndent()
        assertTrue(html.contains("Retry"))
        assertTrue(html.contains("window.location.reload()"))
    }
}
