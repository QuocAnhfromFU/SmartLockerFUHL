#include <ESP8266HTTPClient.h>
#include <ArduinoJson.h> // Để phân tích cú pháp JSON

const char* ssid = "Redmi56";
const char* password = "01234den8";
const char* firebaseHost = "gggg-fda6e-default-rtdb.firebaseio.com";
const char* firebaseToken = "AIzaSyBSb7-FNYpkwxo94aXoLx5GAuBvIfzIL-w";
const char* databasePath = "/lockers.json"; // Đường dẫn đến trường "lockers" trong cơ sở dữ liệu Firebase của bạn

void setup() {
  Serial.begin(115200);

  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected");

  // Send HTTP GET request to Firebase
  HTTPClient http;
 WiFiClient client;
http.begin(client, "https://" + String(firebaseHost) + databasePath + "?auth=" + String(firebaseToken));
  int httpCode = http.GET();

  // Check for a successful request
  if (httpCode == HTTP_CODE_OK) {
    String payload = http.getString();
    // Parse JSON
    DynamicJsonDocument doc(1024); // 1024 là kích thước bộ nhớ đệm cho tài liệu JSON
    deserializeJson(doc, payload);
    // Truy cập trường "lockers"
    const char* lockers = doc["lockers"];
    Serial.println(lockers); // In ra giá trị của trường "lockers"
  } else {
    Serial.println("Failed to get data from Firebase");
  }

  http.end(); // Free resources
}

void loop() {
  // Nothing to do here for this example
}
