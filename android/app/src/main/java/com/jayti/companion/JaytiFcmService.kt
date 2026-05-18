package com.jayti.companion

import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Intent
import androidx.core.app.NotificationCompat
import com.google.firebase.messaging.FirebaseMessagingService
import com.google.firebase.messaging.RemoteMessage

/**
 * Handles incoming Firebase Cloud Messaging (FCM) push notifications.
 *
 * Jayti sends two types:
 *  - Morning diary reminder   (channel: diary_reminders)
 *  - Evening reflection nudge (channel: diary_reminders)
 *
 * The Django backend sends these via pywebpush / firebase-admin when
 * the user has granted notification permission and subscribed.
 */
class JaytiFcmService : FirebaseMessagingService() {

    companion object {
        const val CHANNEL_ID   = "jayti_diary_reminders"
        const val CHANNEL_NAME = "Diary Reminders"
        const val CHANNEL_DESC = "Morning and evening reminders to write in your diary"
    }

    override fun onNewToken(token: String) {
        super.onNewToken(token)
        // Token refreshed — send to Django backend so it can update the
        // push subscription in the PushSubscription model.
        // In a full implementation: POST /api/push-subscribe/ with the new token.
        android.util.Log.d("JaytiFCM", "New FCM token: ${token.take(20)}…")
    }

    override fun onMessageReceived(message: RemoteMessage) {
        super.onMessageReceived(message)

        val title = message.notification?.title
            ?: message.data["title"]
            ?: "💝 Jayti"

        val body = message.notification?.body
            ?: message.data["body"]
            ?: "Your space is waiting for you."

        val deepLink = message.data["url"] ?: BuildConfig.APP_URL

        showNotification(title, body, deepLink)
    }

    private fun showNotification(title: String, body: String, deepLink: String) {
        val nm = getSystemService(NOTIFICATION_SERVICE) as NotificationManager

        // Create channel (no-op if already exists)
        val channel = NotificationChannel(
            CHANNEL_ID, CHANNEL_NAME, NotificationManager.IMPORTANCE_DEFAULT
        ).apply { description = CHANNEL_DESC }
        nm.createNotificationChannel(channel)

        // Tap opens the app at the deep link
        val intent = Intent(this, MainActivity::class.java).apply {
            action = Intent.ACTION_VIEW
            data   = android.net.Uri.parse(deepLink)
            flags  = Intent.FLAG_ACTIVITY_SINGLE_TOP or Intent.FLAG_ACTIVITY_CLEAR_TOP
        }
        val pending = PendingIntent.getActivity(
            this, 0, intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )

        val notification = NotificationCompat.Builder(this, CHANNEL_ID)
            .setSmallIcon(R.drawable.splash_icon)
            .setContentTitle(title)
            .setContentText(body)
            .setStyle(NotificationCompat.BigTextStyle().bigText(body))
            .setContentIntent(pending)
            .setAutoCancel(true)
            .setPriority(NotificationCompat.PRIORITY_DEFAULT)
            .build()

        nm.notify(System.currentTimeMillis().toInt(), notification)
    }
}
