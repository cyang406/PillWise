# PillWise mobile (iOS and Android)

Owner: C (task C13). An Expo app that shows the PillWise web app full screen in a WebView, so every
safety-critical screen (severity, evidence, pharmacist footer, "could not check") is rendered by one
codebase: `app/` in this repo. Native screens are the roadmap (C15).

What the shell adds: a launch screen with the disclaimer, a camera permission request, an offline /
error screen with "Try again", Android back-button navigation, and no cookies, cache or storage kept
between sessions (`incognito`, safety rule 6).

## Run it on a phone (Expo Go, no app store needed)

1. Start the web app on the laptop (real offline mode is the demo default):
   ```bash
   PILLWISE_MOCK=0 PILLWISE_OFFLINE=1 uv run --no-project make app    # http://localhost:8501
   ```
2. Give it an address the phone can open (C14):
   - Same Wi-Fi: `http://<laptop LAN IP>:8501`. "Upload" works (phones offer "Take photo" there),
     but the in-page camera tab needs HTTPS.
   - HTTPS: a tunnel, e.g. `cloudflared tunnel --url http://localhost:8501`, which prints an
     `https://….trycloudflare.com` address.
3. Start the app with that address and scan the QR code with Expo Go (Android) or the Camera app (iOS):
   ```bash
   cd mobile
   npm install
   EXPO_PUBLIC_PILLWISE_URL=https://….trycloudflare.com npx expo start --tunnel
   ```
   `--tunnel` lets the phone reach the Expo dev server from any network; drop it on the same Wi-Fi.

## Checks

```bash
npx tsc --noEmit      # types
npx expo-doctor       # SDK versions and app.json schema
```

Expo changes every SDK release (this is SDK 58): check `node_modules/expo/package.json` and the
versioned docs before changing native APIs, and add packages with `npx expo install`, never `npm install <pkg>`.
