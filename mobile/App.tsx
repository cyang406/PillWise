// PillWise mobile shell (C13): the web app in a full-screen WebView, so the safety-critical screens
// (severity, evidence, pharmacist footer, "could not check") exist in one place only: app/ in the repo.
import { useCameraPermissions } from 'expo-camera';
import { StatusBar } from 'expo-status-bar';
import { useEffect, useRef, useState } from 'react';
import { ActivityIndicator, BackHandler, Pressable, StyleSheet, Text, View } from 'react-native';
import { SafeAreaProvider, SafeAreaView } from 'react-native-safe-area-context';
import { WebView } from 'react-native-webview';

// Set at bundle time: EXPO_PUBLIC_PILLWISE_URL=https://... npx expo start
const PILLWISE_URL = process.env.EXPO_PUBLIC_PILLWISE_URL ?? '';

const TEAL = '#0f766e';
const DISCLAIMER =
  'PillWise is an educational tool, not medical advice. It does not replace your pharmacist or doctor. ' +
  'If you have urgent symptoms, call emergency services.';

export default function App() {
  return (
    <SafeAreaProvider>
      <SafeAreaView style={styles.root} edges={['top', 'bottom']}>
        <StatusBar style="dark" />
        <Main />
      </SafeAreaView>
    </SafeAreaProvider>
  );
}

function Main() {
  const [accepted, setAccepted] = useState(false);
  const [permission, requestPermission] = useCameraPermissions();

  if (!PILLWISE_URL) {
    return (
      <Message title="App not configured" body="Start it with EXPO_PUBLIC_PILLWISE_URL set to the PillWise web address." />
    );
  }
  if (!accepted) {
    return (
      <View style={styles.center}>
        <Text style={styles.logo}>💊 PillWise</Text>
        <Text style={styles.tagline}>Snap your pills. Understand them. Stay safe.</Text>
        <Text style={styles.disclaimer}>{DISCLAIMER}</Text>
        <Text style={styles.small}>PillWise uses photos only to read the label and does not store them.</Text>
        <Button
          label="I understand, continue"
          onPress={async () => {
            if (!permission?.granted) await requestPermission(); // a "no" still allows upload and manual entry
            setAccepted(true);
          }}
        />
      </View>
    );
  }
  return <PillWiseWeb />;
}

function PillWiseWeb() {
  const web = useRef<WebView<{}>>(null);
  const [failed, setFailed] = useState(false);
  const [canGoBack, setCanGoBack] = useState(false);
  const [attempt, setAttempt] = useState(0);

  // Android back button goes back inside the app (Results -> Home) before leaving it.
  useEffect(() => {
    const sub = BackHandler.addEventListener('hardwareBackPress', () => {
      if (canGoBack) web.current?.goBack();
      return canGoBack;
    });
    return () => sub.remove();
  }, [canGoBack]);

  if (failed) {
    return (
      <Message
        title="Can't reach PillWise"
        body="Check your internet connection and try again."
        action={{ label: 'Try again', onPress: () => { setFailed(false); setAttempt((n) => n + 1); } }}
      />
    );
  }
  return (
    <WebView
      key={attempt}
      ref={web}
      source={{ uri: PILLWISE_URL }}
      // The web app shows its in-page camera tab only when it sees this (app/components.py: in_mobile_app).
      applicationNameForUserAgent="PillWiseMobile/1.0"
      style={styles.root}
      // Privacy (safety rule 6): no cookies, cache or storage kept between sessions.
      incognito
      cacheEnabled={false}
      // Camera inside the page (st.camera_input) and the photo picker (st.file_uploader).
      mediaCapturePermissionGrantType="grant"
      allowsInlineMediaPlayback
      mediaPlaybackRequiresUserAction={false}
      javaScriptEnabled
      domStorageEnabled
      pullToRefreshEnabled
      startInLoadingState
      renderLoading={() => <ActivityIndicator style={styles.loading} size="large" color={TEAL} />}
      onNavigationStateChange={(s) => setCanGoBack(s.canGoBack)}
      onError={() => setFailed(true)}
      onHttpError={(e) => e.nativeEvent.statusCode >= 500 && setFailed(true)}
      setSupportMultipleWindows={false}
    />
  );
}

function Message({ title, body, action }: { title: string; body: string; action?: { label: string; onPress: () => void } }) {
  return (
    <View style={styles.center}>
      <Text style={styles.title}>{title}</Text>
      <Text style={styles.body}>{body}</Text>
      {action && <Button label={action.label} onPress={action.onPress} />}
    </View>
  );
}

function Button({ label, onPress }: { label: string; onPress: () => void }) {
  return (
    <Pressable accessibilityRole="button" onPress={onPress} style={({ pressed }) => [styles.button, pressed && { opacity: 0.8 }]}>
      <Text style={styles.buttonText}>{label}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: '#fff' },
  center: { flex: 1, padding: 24, justifyContent: 'center', backgroundColor: '#fff' },
  logo: { fontSize: 36, fontWeight: '700', marginBottom: 4 },
  tagline: { fontSize: 16, color: '#555', marginBottom: 24 },
  disclaimer: { fontSize: 17, lineHeight: 24, backgroundColor: '#e8f1fb', color: '#0b4a8b', padding: 16, borderRadius: 10, marginBottom: 12 },
  small: { fontSize: 14, color: '#555', marginBottom: 28 },
  title: { fontSize: 22, fontWeight: '700', marginBottom: 8 },
  body: { fontSize: 16, color: '#444', marginBottom: 24 },
  button: { backgroundColor: TEAL, borderRadius: 10, paddingVertical: 16, alignItems: 'center' },
  buttonText: { color: '#fff', fontSize: 18, fontWeight: '600' },
  loading: { position: 'absolute', top: '45%', alignSelf: 'center' },
});
