import requests
import time
import sys

URL = "https://tubes-jemuran-andesis.vercel.app/api/update"

SIMULATION_STATES = [
    # (status_cuaca, kondisi_jemuran, warna, peringatan, durasi_detik)
    ("CERAH / KERING", "Aman Ditinggal", "green", "Aman", 10),
    ("GERIMIS", "Aman Ditinggal", "yellow", "Aman", 8),
    ("HUJAN", "Segera Angkat Pakaian", "red", "Jemuran terkena hujan!", 15),
    ("GERIMIS", "Segera Angkat Pakaian", "yellow", "Aman", 8),
    ("CERAH / KERING", "Segera Angkat Pakaian", "green", "Aman", 5),
    ("CERAH / KERING", "Aman Ditinggal", "green", "Aman", 10),
]

def main():
    print("==================================================")
    print("      SIMULATOR TRANSMITTER SENSOR JEMURAN        ")
    print("==================================================")
    print(f"Mengirim simulasi data ke: {URL}")
    print("Program ini meniru data dari Arduino & Transmitter")
    print("Tekan Ctrl+C untuk menghentikan simulasi.")
    print("--------------------------------------------------")
    
    try:
        state_idx = 0
        while True:
            status, kondisi, warna, warning, duration = SIMULATION_STATES[state_idx]
            print(f"\n[+] Memulai State Simulasi: {status} | {kondisi} | {duration} detik")
            
            payload = {
                'status_cuaca': status,
                'kondisi_jemuran': kondisi,
                'warna': warna,
                'peringatan': warning
            }
            
            # Kirim data setiap 1.5 detik selama durasi state berlangsung
            end_time = time.time() + duration
            while time.time() < end_time:
                try:
                    response = requests.post(URL, json=payload, timeout=2)
                    if response.status_code == 200:
                        res_data = response.json()
                        logged = "Disimpan ke Database" if res_data.get('logged_to_history') else "Hanya Update UI"
                        print(f"  -> Kirim: {status} | {kondisi} | Respon: {response.status_code} ({logged})")
                    else:
                        print(f"  -> [✕] Gagal. HTTP Status: {response.status_code}")
                except requests.exceptions.RequestException as e:
                    print(f"  -> [✕] Gagal menghubungi server: {e}")
                    print("     Pastikan server backend Flask (app.py) sudah dijalankan.")
                    
                time.sleep(1.5)
                
            # Lanjut ke state berikutnya
            state_idx = (state_idx + 1) % len(SIMULATION_STATES)
            
    except KeyboardInterrupt:
        print("\n[+] Simulasi dihentikan.")

if __name__ == "__main__":
    main()
