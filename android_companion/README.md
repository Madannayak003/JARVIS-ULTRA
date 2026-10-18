# JARVIS Android Camera2 companion

This small companion is required for verified phone flashlight control and
actual photo capture. ADB can launch Android activities, but it cannot
reliably access Samsung's torch or receive an `IMAGE_CAPTURE` result by itself.

Build and install from a machine with Android SDK/Gradle configured:

```powershell
cd android_companion
gradle assembleDebug
adb install -r app/build/outputs/apk/debug/app-debug.apk
adb shell pm grant com.jarvis.androidcontrol android.permission.CAMERA
```

The app is controlled only through explicit ADB `am start` arguments by the
existing Python Android manager. It stores the last structured result in its
private files directory; the manager reads it using `run-as` and requires a
matching request ID before reporting success.

The first camera operation may require the phone to be unlocked. The app saves
verified JPEGs under `Pictures/JARVIS` through MediaStore. Flashlight commands
are accepted by `CameraManager.setTorchMode`; Android does not expose a
portable read-back state, so JARVIS reports that limitation.
