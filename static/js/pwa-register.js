// PWA Registration and Push Notification Setup

(function() {
  'use strict';

  // Register Service Worker
  if ('serviceWorker' in navigator) {
    window.addEventListener('load', function() {
      navigator.serviceWorker.register('/static/js/sw.js')
        .then(function(registration) {
          console.log('ServiceWorker registered:', registration.scope);
          
          // Request notification permission
          requestNotificationPermission(registration);
        })
        .catch(function(error) {
          console.log('ServiceWorker registration failed:', error);
        });
    });
  }

  // Request notification permission
  function requestNotificationPermission(registration) {
    if (!('Notification' in window)) {
      console.log('This browser does not support notifications');
      return;
    }

    if (Notification.permission === 'granted') {
      subscribeToPush(registration);
    } else if (Notification.permission !== 'denied') {
      // Show a prompt to enable notifications
      showNotificationPrompt(registration);
    }
  }

  // Show notification prompt
  function showNotificationPrompt(registration) {
    // Create a subtle banner
    const banner = document.createElement('div');
    banner.className = 'notification-prompt';
    banner.innerHTML = `
      <div style="position: fixed; top: 20px; right: 20px; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.2); z-index: 9999; max-width: 300px;">
        <h4 style="margin: 0 0 10px 0; color: #FF69B4;">📬 Stay Connected</h4>
        <p style="margin: 0 0 15px 0; font-size: 14px;">Get gentle reminders to write in your diary</p>
        <button id="enable-notifications" style="background: #FF69B4; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; margin-right: 10px;">Enable</button>
        <button id="dismiss-notifications" style="background: #ccc; color: #333; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer;">Maybe Later</button>
      </div>
    `;
    
    document.body.appendChild(banner);
    
    document.getElementById('enable-notifications').addEventListener('click', function() {
      Notification.requestPermission().then(function(permission) {
        if (permission === 'granted') {
          subscribeToPush(registration);
        }
        banner.remove();
      });
    });
    
    document.getElementById('dismiss-notifications').addEventListener('click', function() {
      banner.remove();
    });
  }

  // Subscribe to push notifications
  function subscribeToPush(registration) {
    if (!VAPID_PUBLIC_KEY) {
      console.log('Push notifications not configured (no VAPID key)');
      return;
    }
    registration.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: urlBase64ToUint8Array(VAPID_PUBLIC_KEY)
    })
    .then(function(subscription) {
      console.log('Push subscription:', subscription);
      
      // Send subscription to server
      sendSubscriptionToServer(subscription);
    })
    .catch(function(error) {
      console.log('Push subscription failed:', error);
    });
  }

  // Send subscription to server
  function sendSubscriptionToServer(subscription) {
    const subscriptionData = {
      endpoint: subscription.endpoint,
      keys: {
        p256dh: arrayBufferToBase64(subscription.getKey('p256dh')),
        auth: arrayBufferToBase64(subscription.getKey('auth'))
      }
    };
    
    fetch('/api/push-subscribe/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken')
      },
      body: JSON.stringify(subscriptionData)
    })
    .then(function(response) {
      if (response.ok) {
        console.log('Subscription sent to server');
      }
    })
    .catch(function(error) {
      console.log('Failed to send subscription:', error);
    });
  }

  // Utility functions
  function urlBase64ToUint8Array(base64String) {
    const padding = '='.repeat((4 - base64String.length % 4) % 4);
    const base64 = (base64String + padding)
      .replace(/\-/g, '+')
      .replace(/_/g, '/');
    
    const rawData = window.atob(base64);
    const outputArray = new Uint8Array(rawData.length);
    
    for (let i = 0; i < rawData.length; ++i) {
      outputArray[i] = rawData.charCodeAt(i);
    }
    return outputArray;
  }

  function arrayBufferToBase64(buffer) {
    const bytes = new Uint8Array(buffer);
    let binary = '';
    for (let i = 0; i < bytes.byteLength; i++) {
      binary += String.fromCharCode(bytes[i]);
    }
    return window.btoa(binary);
  }

  function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
      const cookies = document.cookie.split(';');
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === (name + '=')) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }

  // Install prompt for PWA
  let deferredPrompt;
  
  window.addEventListener('beforeinstallprompt', function(e) {
    e.preventDefault();
    deferredPrompt = e;
    
    // Show install button
    showInstallPrompt();
  });

  function showInstallPrompt() {
    const installBanner = document.createElement('div');
    installBanner.innerHTML = `
      <div style="position: fixed; bottom: 20px; left: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px 20px; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.3); z-index: 9999; max-width: 300px;">
        <h4 style="margin: 0 0 10px 0;">📱 Install Jayti App</h4>
        <p style="margin: 0 0 15px 0; font-size: 14px;">Add to your home screen for quick access</p>
        <button id="install-pwa" style="background: white; color: #667eea; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; font-weight: bold;">Install</button>
        <button id="dismiss-install" style="background: transparent; color: white; border: 1px solid white; padding: 10px 20px; border-radius: 5px; cursor: pointer; margin-left: 10px;">Not Now</button>
      </div>
    `;
    
    document.body.appendChild(installBanner);
    
    document.getElementById('install-pwa').addEventListener('click', function() {
      installBanner.remove();
      deferredPrompt.prompt();
      deferredPrompt.userChoice.then(function(choiceResult) {
        if (choiceResult.outcome === 'accepted') {
          console.log('PWA installed');
        }
        deferredPrompt = null;
      });
    });
    
    document.getElementById('dismiss-install').addEventListener('click', function() {
      installBanner.remove();
    });
  }

})();

// VAPID public key (set via Django template tag or environment variable)
const VAPID_PUBLIC_KEY = (typeof DJANGO_VAPID_PUBLIC_KEY !== 'undefined' && DJANGO_VAPID_PUBLIC_KEY && DJANGO_VAPID_PUBLIC_KEY !== 'YOUR_VAPID_PUBLIC_KEY_HERE')
  ? DJANGO_VAPID_PUBLIC_KEY
  : null;
