// Definisi Pin Output
const int pinBuzzer = 7;
const int pinLedMerah = 6;
const int pinLedKuning = 5;
const int pinLedHijau = 4;

// Definisi Pin Analog (Gunakan Arduino yang punya minimal 2 pin analog, seperti UNO/Nano)
const int raindrop1_A = A1; // Sensor Cuaca
const int raindrop2_A = A2; // Sensor Jemuran

// Batas Nilai Ambang (Threshold)
const int batasHujanLebat = 400;
const int batasGerimis    = 700;

void setup() {
  // Inisialisasi komunikasi Serial via USB-C
  Serial.begin(9600);
  
  pinMode(pinBuzzer, OUTPUT);
  pinMode(pinLedMerah, OUTPUT);
  pinMode(pinLedKuning, OUTPUT);
  pinMode(pinLedHijau, OUTPUT);
}

void loop() {
  int nilaiCuaca = analogRead(raindrop1_A);
  int nilaiJemuran = analogRead(raindrop2_A);
  
  String statusCuaca = "";
  String kondisiJemuran = "";
  String warna = "";
  String peringatan = "Aman";

  // LOGIKA STATUS & KONTROL HARDWARE LOKAL
  if (nilaiCuaca < batasHujanLebat) {
    statusCuaca = "HUJAN";
    warna = "red";
    peringatan = "Jemuran terkena hujan!";
    digitalWrite(pinLedMerah, HIGH);
    digitalWrite(pinLedKuning, LOW);
    digitalWrite(pinLedHijau, LOW);
    digitalWrite(pinBuzzer, HIGH); 
  } 
  else if (nilaiCuaca >= batasHujanLebat && nilaiCuaca < batasGerimis) {
    statusCuaca = "GERIMIS";
    warna = "yellow";
    digitalWrite(pinLedMerah, LOW);
    digitalWrite(pinLedKuning, HIGH);
    digitalWrite(pinLedHijau, LOW);
    digitalWrite(pinBuzzer, LOW);
  } 
  else {
    statusCuaca = "CERAH / KERING";
    warna = "green";
    digitalWrite(pinLedMerah, LOW);
    digitalWrite(pinLedKuning, LOW);
    digitalWrite(pinLedHijau, HIGH);
    digitalWrite(pinBuzzer, LOW);
  }

  // LOGIKA SENSOR JEMURAN
  if (nilaiJemuran < batasGerimis) {
    kondisiJemuran = "Segera Angkat Pakaian";
  } else {
    kondisiJemuran = "Aman Ditinggal";
  }

  // Kirim data ke USB-C dalam bentuk satu baris teks terstruktur
  // Format: STATUS_CUACA|KONDISI_JEMURAN|WARNA_INDIKATOR|PERINGATAN
  Serial.print(statusCuaca);     Serial.print("|");
  Serial.print(kondisiJemuran);   Serial.print("|");
  Serial.print(warna);           Serial.print("|");
  Serial.println(peringatan);

  delay(1000); // Update data setiap 1 detik
}
