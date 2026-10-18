package com.jarvis.androidcontrol;

import android.Manifest;
import android.app.Activity;
import android.content.ContentValues;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.graphics.ImageFormat;
import android.graphics.SurfaceTexture;
import android.hardware.camera2.CameraAccessException;
import android.hardware.camera2.CameraCaptureSession;
import android.hardware.camera2.CameraCharacteristics;
import android.hardware.camera2.CameraDevice;
import android.hardware.camera2.CameraManager;
import android.hardware.camera2.CaptureRequest;
import android.media.Image;
import android.media.ImageReader;
import android.net.Uri;
import android.os.Bundle;
import android.os.Environment;
import android.os.Handler;
import android.os.HandlerThread;
import android.provider.MediaStore;
import android.view.Surface;
import android.view.TextureView;
import android.view.ViewGroup;
import android.widget.FrameLayout;

import org.json.JSONObject;

import java.io.File;
import java.io.FileOutputStream;
import java.nio.ByteBuffer;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Date;
import java.util.Locale;

/** Small, explicit Camera2 bridge controlled only by ADB am start commands. */
public final class MainActivity extends Activity {
    private static final int CAMERA_PERMISSION = 42;
    private String action, facing, requestId;
    private CameraManager cameras;
    private CameraDevice camera;
    private CameraCaptureSession session;
    private ImageReader reader;
    private Handler handler;
    private HandlerThread thread;
    private TextureView preview;

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        Intent intent = getIntent();
        action = intent.getStringExtra("action");
        facing = intent.getStringExtra("facing");
        requestId = intent.getStringExtra("request_id");
        if (requestId == null) requestId = "";
        cameras = (CameraManager) getSystemService(CAMERA_SERVICE);
        if ("preview".equals(action)) {
            preview = new TextureView(this);
            preview.setLayoutParams(new ViewGroup.LayoutParams(-1, -1));
            setContentView(preview);
            preview.setSurfaceTextureListener(new TextureView.SurfaceTextureListener() {
                public void onSurfaceTextureAvailable(SurfaceTexture s, int w, int h) {
                    if (checkSelfPermission(Manifest.permission.CAMERA) != PackageManager.PERMISSION_GRANTED) requestPermissions(new String[]{Manifest.permission.CAMERA}, CAMERA_PERMISSION);
                    else open(false);
                }
                public void onSurfaceTextureSizeChanged(SurfaceTexture s, int w, int h) {}
                public boolean onSurfaceTextureDestroyed(SurfaceTexture s) { return true; }
                public void onSurfaceTextureUpdated(SurfaceTexture s) {}
            });
        } else {
            setContentView(new FrameLayout(this));
            if (checkSelfPermission(Manifest.permission.CAMERA) != PackageManager.PERMISSION_GRANTED) {
                requestPermissions(new String[]{Manifest.permission.CAMERA}, CAMERA_PERMISSION);
            } else handleAction();
        }
    }

    @Override public void onRequestPermissionsResult(int request, String[] permissions, int[] results) {
        super.onRequestPermissionsResult(request, permissions, results);
        if (request == CAMERA_PERMISSION && results.length > 0 && results[0] == PackageManager.PERMISSION_GRANTED) {
            if ("preview".equals(action)) open(false); else handleAction();
        }
        else fail("Camera permission was not granted", true);
    }

    private void handleAction() {
        if ("flashlight_on".equals(action) || "flashlight_off".equals(action)) {
            try {
                String id = backCamera();
                if (id == null) { fail("No rear camera with a torch was found", true); return; }
                cameras.setTorchMode(id, "flashlight_on".equals(action));
                write(true, "Flashlight command accepted; Android does not provide a portable read-back state", null, null);
                finish();
            } catch (Exception e) { fail(e.getMessage(), true); }
        } else if ("capture".equals(action)) open(true);
        else fail("Unsupported companion action", true);
    }

    private void open(boolean capture) {
        try {
            if (checkSelfPermission(Manifest.permission.CAMERA) != PackageManager.PERMISSION_GRANTED) { fail("Camera permission was not granted", true); return; }
            String id = findCamera();
            if (id == null) { fail("Requested camera was not found", true); return; }
            cameras.openCamera(id, new CameraDevice.StateCallback() {
                public void onOpened(CameraDevice device) { camera = device; if (capture) capture(); else showPreview(); }
                public void onDisconnected(CameraDevice device) { device.close(); fail("Camera disconnected", true); }
                public void onError(CameraDevice device, int error) { device.close(); fail("Camera open failed: " + error, true); }
            }, handler());
        } catch (Exception e) { fail(e.getMessage(), true); }
    }

    private void showPreview() {
        try {
            Surface surface = new Surface(preview.getSurfaceTexture());
            CaptureRequest.Builder builder = camera.createCaptureRequest(CameraDevice.TEMPLATE_PREVIEW);
            builder.addTarget(surface);
            CaptureRequest request = builder.build();
            ArrayList<Surface> outputs = new ArrayList<>(); outputs.add(surface);
            camera.createCaptureSession(outputs, new CameraCaptureSession.StateCallback() {
                public void onConfigured(CameraCaptureSession s) { session = s; try { s.setRepeatingRequest(request, null, handler()); write(true, "Requested camera preview opened", null, null); } catch (Exception e) { fail(e.getMessage(), true); } }
                public void onConfigureFailed(CameraCaptureSession s) { fail("Camera preview configuration failed", true); }
            }, handler());
        } catch (Exception e) { fail(e.getMessage(), true); }
    }

    private void capture() {
        try {
            reader = ImageReader.newInstance(1920, 1080, ImageFormat.JPEG, 2);
            reader.setOnImageAvailableListener(r -> {
                Image image = r.acquireLatestImage();
                if (image == null) return;
                try { save(image); } catch (Exception e) { fail(e.getMessage(), true); } finally { image.close(); }
            }, handler());
            ArrayList<Surface> outputs = new ArrayList<>(); outputs.add(reader.getSurface());
            camera.createCaptureSession(outputs, new CameraCaptureSession.StateCallback() {
                public void onConfigured(CameraCaptureSession s) {
                    session = s;
                    try {
                        CaptureRequest.Builder request = camera.createCaptureRequest(CameraDevice.TEMPLATE_STILL_CAPTURE);
                        request.addTarget(reader.getSurface());
                        s.capture(request.build(), null, handler());
                    } catch (Exception e) {
                        fail(e.getMessage(), true);
                    }
                }
                public void onConfigureFailed(CameraCaptureSession s) { fail("Photo capture configuration failed", true); }
            }, handler());
        } catch (Exception e) { fail(e.getMessage(), true); }
    }

    private void save(Image image) throws Exception {
        String name = "JARVIS_" + new SimpleDateFormat("yyyyMMdd_HHmmss", Locale.US).format(new Date()) + ".jpg";
        ByteBuffer buffer = image.getPlanes()[0].getBuffer(); byte[] bytes = new byte[buffer.remaining()]; buffer.get(bytes);
        if (bytes.length < 4 || (bytes[0] & 0xff) != 0xff || (bytes[1] & 0xff) != 0xd8) throw new IllegalStateException("Camera returned an invalid JPEG");
        ContentValues values = new ContentValues(); values.put(MediaStore.Images.Media.DISPLAY_NAME, name); values.put(MediaStore.Images.Media.MIME_TYPE, "image/jpeg"); values.put(MediaStore.Images.Media.RELATIVE_PATH, Environment.DIRECTORY_PICTURES + "/JARVIS"); values.put(MediaStore.Images.Media.IS_PENDING, 1);
        Uri uri = getContentResolver().insert(MediaStore.Images.Media.EXTERNAL_CONTENT_URI, values);
        if (uri == null) throw new IllegalStateException("Gallery storage rejected the photo");
        try (FileOutputStream out = (FileOutputStream) getContentResolver().openAssetFileDescriptor(uri, "w").createOutputStream()) { out.write(bytes); }
        values.clear(); values.put(MediaStore.Images.Media.IS_PENDING, 0); getContentResolver().update(uri, values, null, null);
        write(true, "Photo captured and verified", uri.toString(), name); finish();
    }

    private String findCamera() throws CameraAccessException {
        boolean wantFront = "front".equalsIgnoreCase(facing);
        for (String id : cameras.getCameraIdList()) { CameraCharacteristics c = cameras.getCameraCharacteristics(id); Integer lens = c.get(CameraCharacteristics.LENS_FACING); if (lens != null && lens == (wantFront ? CameraCharacteristics.LENS_FACING_FRONT : CameraCharacteristics.LENS_FACING_BACK)) return id; }
        return null;
    }
    private String backCamera() throws CameraAccessException { facing = "rear"; String id = findCamera(); return id; }
    private Handler handler() { if (handler == null) { thread = new HandlerThread("jarvis-camera"); thread.start(); handler = new Handler(thread.getLooper()); } return handler; }
    private void write(boolean ok, String message, String location, String packageName) { try { JSONObject o = new JSONObject(); o.put("ok", ok); o.put("request_id", requestId); o.put("message", message == null ? "" : message); o.put("location", location == null ? JSONObject.NULL : location); o.put("package", packageName == null ? JSONObject.NULL : packageName); o.put("supported", true); FileOutputStream out = openFileOutput("last_result.json", MODE_PRIVATE); out.write(o.toString().getBytes("UTF-8")); out.close(); } catch (Exception ignored) {} }
    private void fail(String message, boolean finish) { write(false, message == null ? "Android companion operation failed" : message, null, null); if (finish) finish(); }
    @Override protected void onDestroy() { if (session != null) session.close(); if (camera != null) camera.close(); if (reader != null) reader.close(); if (thread != null) thread.quitSafely(); super.onDestroy(); }
}
