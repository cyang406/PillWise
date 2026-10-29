# PillWise mobile (iOS and Android)

Owner: C (task C13). An Expo app that shows the PillWise web app full screen in a WebView, so every
safety-critical screen (severity, evidence, pharmacist footer, "could not check") is rendered by one
codebase: `app/` in this repo. Native screens are the roadmap (C15).

What the shell adds: a launch screen with the disclaimer, a camera permission request, an in-page
"Take a photo" camera (the web version only has upload), an offline / error screen with "Try again",
Android back-button navigation, and no cookies, cache or storage kept between sessions (`incognito`,
safety rule 6).

## Step by step: run it on your iPhone (Expo Go, no App Store needed)

You need: the Mac with this repo, an iPhone (Android works the same way), both on the same network.

1. **Install Expo Go** on the iPhone from the App Store (free). If it later says the project needs a newer
   SDK, update Expo Go.
2. **Start the web app on the Mac** (repo root):
   ```bash
   PILLWISE_MOCK=0 uv run --no-project make app        # http://localhost:8501, needs OPENAI_API_KEY in .env
   ```
3. **Find the Mac's address** the phone will use: `ipconfig getifaddr en0` (e.g. `192.168.1.23`).
   On the iPhone, open Safari at `http://192.168.1.23:8501`. If it does not load, the network blocks
   device-to-device traffic (common at venues): turn on the iPhone's **Personal Hotspot**, join it from
   the Mac, run `ipconfig getifaddr en0` again and use that address.
4. **Start the app** on the Mac, with that address:
   ```bash
   cd mobile
   npm install                                           # first time only
   EXPO_PUBLIC_PILLWISE_URL=http://192.168.1.23:8501 npx expo start
   ```
   A QR code appears in the terminal.
5. **Open it on the iPhone**: point the **Camera** app at the QR code and tap the banner; it opens in
   Expo Go. (If the phone can't reach the Mac, use `npx expo start --tunnel` instead.)
6. **Use PillWise on the phone**:
   1. Read the disclaimer, tap **I understand, continue**, allow the camera.
   2. Step 1: type your age (optional).
   3. Step 2: tap **Take a photo** and photograph a bottle label, or **Add bottle photos** to pick
      several from the photo library. Each one appears with "Matched: …" or "Please check this name".
   4. Tap **Check my list**. Read the one-line verdict.
   5. In **How your medicines mix**, tap a square to see what was found for those two medicines; tap a
      medicine name on the left for **About this medicine**.
   6. Scroll to **Ask your pharmacist**: the questions, **Share**, **Pharmacy file**, and
      **Buying something new?**.
   The in-page **Take a photo** camera needs an HTTPS address (a tunnel such as
   `cloudflared tunnel --url http://localhost:8501`). Over plain `http://`, use **Add bottle photos →
   Take Photo**, which works everywhere.

## Step by step: demo it with iPhone Mirroring

iPhone Mirroring shows and controls the iPhone in a window on the Mac, which is easy to screen-record.
Requirements: macOS 15 or later on the Mac, iOS 18 or later on the iPhone, both signed in to the same
Apple Account (two-factor on), Wi-Fi and Bluetooth on, iPhone nearby and **locked**.

1. Do steps 1–5 above first, and check the app opens on the iPhone.
2. **Lock the iPhone** and put it next to the Mac.
3. On the Mac, open **iPhone Mirroring** (Dock, Launchpad or Spotlight). The first time, follow the
   prompts and enter the iPhone passcode.
4. In the mirrored iPhone, open **Expo Go** and tap the PillWise project under "Recently opened".
5. Drive the app with the mouse and keyboard. Type the age and medicine names with the Mac keyboard.
6. **Photos**: the iPhone camera can't be used while mirroring. Before the demo, take the bottle photos
   with the iPhone (or AirDrop `data/photos/bottle_1.png` and `gen_ibuprofen_200mg.png` to it); in the
   demo use **Add bottle photos → Photo Library** and select several at once.
7. **Record**: QuickTime Player → File → New Screen Recording (or ⌘⇧5), select the iPhone Mirroring
   window, record. Zoom the mirroring window (⌘+) so text reads well on video.
8. **To show the live camera** instead: unlock the iPhone (this ends mirroring), connect it by cable,
   QuickTime Player → File → New Movie Recording → the arrow next to the record button → choose the
   iPhone as the camera. Record the photo step this way and cut it into the video.

If mirroring won't connect: unlock and lock the iPhone again, check both devices use the same Apple
Account, and turn off Personal Hotspot if you can (use the venue network or the Mac's own network).

## Checks

```bash
npx tsc --noEmit      # types
npx expo-doctor       # SDK versions and app.json schema
```

Expo changes every SDK release (this is SDK 58): check `node_modules/expo/package.json` and the
versioned docs before changing native APIs, and add packages with `npx expo install`, never `npm install <pkg>`.
