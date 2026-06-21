plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
    id("com.google.gms.google-services")          // Firebase
    id("com.google.firebase.crashlytics")         // Crashlytics
}

android {
    namespace = "com.jayti.companion"
    compileSdk = 34

    defaultConfig {
        applicationId = "com.jayti.companion"
        minSdk = 26          // Android 8.0 — covers 95%+ of active devices
        targetSdk = 34
        versionCode = 1
        versionName = "1.0.0"

        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
    }

    buildTypes {
        debug {
            isDebuggable = true
            // No applicationIdSuffix — keeps com.jayti.companion matching google-services.json
            buildConfigField("String", "APP_URL", "\"https://jpfinal-bisu-2026.web.app\"")
            buildConfigField("String", "ENV", "\"debug\"")
        }
        release {
            isMinifyEnabled = true
            isShrinkResources = true
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
            buildConfigField("String", "APP_URL", "\"https://jaytibirthday.in\"")
            buildConfigField("String", "ENV", "\"release\"")
        }
    }

    buildFeatures {
        buildConfig = true
        viewBinding = true
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    kotlinOptions {
        jvmTarget = "17"
    }

    packaging {
        resources {
            excludes += "/META-INF/{AL2.0,LGPL2.1}"
        }
    }
}

dependencies {
    // AndroidX core
    implementation("androidx.core:core-ktx:1.12.0")
    implementation("androidx.appcompat:appcompat:1.6.1")
    implementation("com.google.android.material:material:1.11.0")
    implementation("androidx.constraintlayout:constraintlayout:2.1.4")
    implementation("androidx.swiperefreshlayout:swiperefreshlayout:1.1.0")

    // Splash screen
    implementation("androidx.core:core-splashscreen:1.0.1")

    // WebView extras — file chooser, JS bridge, geolocation
    implementation("androidx.webkit:webkit:1.10.0")

    // Lifecycle
    implementation("androidx.lifecycle:lifecycle-runtime-ktx:2.7.0")
    implementation("androidx.activity:activity-ktx:1.8.2")

    // ─── Firebase (BOM manages all versions) ─────────────────────────────────
    implementation(platform("com.google.firebase:firebase-bom:33.1.0"))
    implementation("com.google.firebase:firebase-analytics-ktx")       // Analytics
    implementation("com.google.firebase:firebase-crashlytics-ktx")     // Crash reporting
    implementation("com.google.firebase:firebase-messaging-ktx")       // Push notifications (FCM)
    implementation("com.google.firebase:firebase-storage-ktx")         // Firebase Storage (Tangred photos)
    implementation("com.google.firebase:firebase-auth-ktx")            // Auth (future use)

    // ─── Unit tests ──────────────────────────────────────────────────────────
    testImplementation("junit:junit:4.13.2")
    testImplementation("org.mockito:mockito-core:5.8.0")
    testImplementation("org.jetbrains.kotlinx:kotlinx-coroutines-test:1.7.3")

    // ─── Instrumented E2E tests (Espresso + UIAutomator) ─────────────────────
    androidTestImplementation("androidx.test.ext:junit:1.1.5")
    androidTestImplementation("androidx.test.espresso:espresso-core:3.5.1")
    androidTestImplementation("androidx.test.espresso:espresso-web:3.5.1")
    androidTestImplementation("androidx.test:runner:1.5.2")
    androidTestImplementation("androidx.test:rules:1.5.0")
    androidTestImplementation("androidx.test.uiautomator:uiautomator:2.3.0")
}
