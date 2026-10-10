#include <WiFi.h>
#include <WebServer.h>

// --- Wi-Fi Credentials ---
const char* ssid     = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";

// --- Hardware Pin Definitions ---
const int RELAY_LIGHT = 23; // GPIO connected to Light relay module
const int RELAY_FAN   = 22; // GPIO connected to Fan relay module

// --- Relay Logic Configuration ---
// Set to true if your relay module is Active LOW (common for relay boards)
// Set to false if your relay module is Active HIGH
const bool RELAY_ACTIVE_LOW = true; 

// --- System State Variables ---
bool lightState = false;
bool fanState   = false;

WebServer server(80);

// Helper function to set physical GPIO state based on active logic
void setHardwareRelay(int pin, bool state) {
  if (RELAY_ACTIVE_LOW) {
    digitalWrite(pin, state ? LOW : HIGH);
  } else {
    digitalWrite(pin, state ? HIGH : LOW);
  }
}

// --- HTTP Route Handlers ---

void handleRoot() {
  String html = "<h1>ESP32 Control Hub</h1>";
  html += "<p>Light: " + String(lightState ? "ON" : "OFF") + "</p>";
  html += "<p>Fan: " + String(fanState ? "ON" : "OFF") + "</p>";
  server.send(200, "text/html", html);
}

// Route: /light/ON or /light/OFF
void handleLight() {
  String uri = server.uri();
  if (uri.endsWith("/ON") || uri.endsWith("/on")) {
    lightState = true;
    setHardwareRelay(RELAY_LIGHT, true);
    Serial.println("[ESP32] Hardware Action: LIGHT -> ON");
    server.send(200, "text/plain", "OK: LIGHT IS ON");
  } else if (uri.endsWith("/OFF") || uri.endsWith("/off")) {
    lightState = false;
    setHardwareRelay(RELAY_LIGHT, false);
    Serial.println("[ESP32] Hardware Action: LIGHT -> OFF");
    server.send(200, "text/plain", "OK: LIGHT IS OFF");
  } else {
    server.send(400, "text/plain", "Bad Request: Specify /ON or /OFF");
  }
}

// Route: /fan/ON or /fan/OFF
void handleFan() {
  String uri = server.uri();
  if (uri.endsWith("/ON") || uri.endsWith("/on")) {
    fanState = true;
    setHardwareRelay(RELAY_FAN, true);
    Serial.println("[ESP32] Hardware Action: FAN -> ON");
    server.send(200, "text/plain", "OK: FAN IS ON");
  } else if (uri.endsWith("/OFF") || uri.endsWith("/off")) {
    fanState = false;
    setHardwareRelay(RELAY_FAN, false);
    Serial.println("[ESP32] Hardware Action: FAN -> OFF");
    server.send(200, "text/plain", "OK: FAN IS OFF");
  } else {
    server.send(400, "text/plain", "Bad Request: Specify /ON or /OFF");
  }
}

// Route: /status (Returns JSON for JARVIS query checks)
void handleStatus() {
  String json = "{";
  json += "\"light\":\"" + String(lightState ? "ON" : "OFF") + "\",";
  json += "\"fan\":\"" + String(fanState ? "ON" : "OFF") + "\",";
  json += "\"rssi\":" + String(WiFi.RSSI());
  json += "}";
  server.send(200, "application/json", json);
}

void handleNotFound() {
  server.send(404, "text/plain", "404: Endpoint Not Found");
}

void setup() {
  Serial.begin(115200);
  delay(500);

  // Initialize GPIO pins
  pinMode(RELAY_LIGHT, OUTPUT);
  pinMode(RELAY_FAN, OUTPUT);

  // Ensure relays start OFF on boot
  setHardwareRelay(RELAY_LIGHT, false);
  setHardwareRelay(RELAY_FAN, false);

  // Connect to Wi-Fi
  Serial.println();
  Serial.print("[ESP32] Connecting to Wi-Fi: ");
  Serial.println(ssid);
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\n[ESP32] Wi-Fi Connected!");
  Serial.print("[ESP32] Assigned IP Address: ");
  Serial.println(WiFi.localIP());

  // Define HTTP endpoints matching Python BASE_URL routes
  server.on("/", handleRoot);
  server.on("/light/ON", handleLight);
  server.on("/light/OFF", handleLight);
  server.on("/light/on", handleLight);
  server.on("/light/off", handleLight);
  
  server.on("/fan/ON", handleFan);
  server.on("/fan/OFF", handleFan);
  server.on("/fan/on", handleFan);
  server.on("/fan/off", handleFan);
  
  server.on("/status", handleStatus);
  server.onNotFound(handleNotFound);

  server.begin();
  Serial.println("[ESP32] HTTP Web Server initialized and listening on port 80.");
}

void loop() {
  // Handle client requests
  server.handleClient();

  // Non-blocking auto-reconnect if Wi-Fi drops
  static unsigned long lastCheck = 0;
  if (millis() - lastCheck > 10000) {
    lastCheck = millis();
    if (WiFi.status() != WL_CONNECTED) {
      Serial.println("[ESP32] Wi-Fi connection lost! Attempting reconnect...");
      WiFi.reconnect();
    }
  }
}