import serial
import serial.tools.list_ports
import requests
import time
import sys

# Konfigurasi Default
DEFAULT_URL = "http://127.0.0.1:5000/api/update"
BAUDRATE = 9600

def list_serial_ports():
    """Mendapatkan daftar semua port serial yang tersedia."""
    ports = serial.tools.list_ports.comports()
    return [port.device for port in ports]

def select_port():
    """Meminta pengguna memilih port serial jika ada banyak, atau auto-select jika cuma satu."""
    ports = list_serial_ports()
    if not ports:
        print("[-] Tidak ada perangkat Serial/Arduino yang terdeteksi.")
        print("    Pastikan Arduino sudah dicolokkan ke laptop/PC Anda.")
        sys.exit(1)
        
    if len(ports) == 1:
        print(f"[+] Hanya terdeteksi satu port: {ports[0]}. Memilih otomatis.")
        return ports[0]
        
    print("\n=== Daftar Port Serial Tersedia ===")
    for index, port in enumerate(ports):
        print(f"[{index + 1}] {port}")
        
    while True:
        try:
            choice = input(f"Pilih port (1-{len(ports)}): ").strip()
            idx = int(choice) - 1
            if 0 <= idx < len(ports):
                return ports[idx]
            else:
                print("[-] Pilihan tidak valid.")
        except ValueError:
            print("[-] Harap masukkan angka.")

def main():
    print("==================================================")
    print("      TRANSMITTER SERIAL ARDUINO -> WEB DATABASE  ")
    print("==================================================")
    
    server_url = input(f"Masukkan URL server API [{DEFAULT_URL}]: ").strip()
    if not server_url:
        server_url = DEFAULT_URL
        
    port = select_port()
    
    print(f"\n[+] Membuka koneksi Serial di {port} dengan baudrate {BAUDRATE}...")
    try:
        ser = serial.Serial(port, BAUDRATE, timeout=2)
        # Berikan waktu Arduino untuk reset setelah koneksi terbuka
        time.sleep(2)
        print("[+] Koneksi berhasil dibuat.")
    except Exception as e:
        print(f"[-] Gagal membuka port {port}. Error: {e}")
        sys.exit(1)
        
    print("\n[+] Memulai transmisi data. Tekan Ctrl+C untuk berhenti.")
    print("--------------------------------------------------")
    
    try:
        while True:
            try:
                # Membaca data serial baris demi baris
                if ser.in_waiting > 0:
                    raw_line = ser.readline()
                    line = raw_line.decode('utf-8', errors='ignore').strip()
                    
                    if not line:
                        continue
                        
                    print(f"-> Serial Data: {line}")
                    
                    # Memecah string dengan separator '|'
                    # Format: STATUS_CUACA|KONDISI_JEMURAN|WARNA_INDIKATOR|PERINGATAN
                    parts = line.split('|')
                    if len(parts) < 4:
                        print("   [!] Format data tidak valid. Dilewati.")
                        continue
                        
                    payload = {
                        'status_cuaca': parts[0].strip(),
                        'kondisi_jemuran': parts[1].strip(),
                        'warna': parts[2].strip(),
                        'peringatan': parts[3].strip()
                    }
                    
                    # Mengirim data ke Flask API
                    try:
                        response = requests.post(server_url, json=payload, timeout=3)
                        if response.status_code == 200:
                            res_data = response.json()
                            status_db = "Disimpan ke Riwayat" if res_data.get('logged_to_history') else "Hanya Update Status"
                            print(f"   [✓] Terkirim ke server. Respon: {response.status_code} ({status_db})")
                        else:
                            print(f"   [✕] Gagal kirim. HTTP Status: {response.status_code}")
                    except requests.exceptions.RequestException as req_err:
                        print(f"   [✕] Gagal koneksi ke server API: {req_err}")
                        
            except serial.SerialException as ser_err:
                print(f"\n[-] Kehilangan koneksi serial: {ser_err}")
                print("[+] Mencoba menghubungkan kembali dalam 5 detik...")
                time.sleep(5)
                # Mencoba buka kembali serial
                try:
                    ser.close()
                    ser = serial.Serial(port, BAUDRATE, timeout=2)
                    time.sleep(2)
                    print("[+] Koneksi serial tersambung kembali.")
                except Exception:
                    pass
            
            # Istirahat sejenak agar CPU tidak sibuk 100% saat tidak ada data
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\n[+] Menghentikan program transmitter...")
    finally:
        if 'ser' in locals() and ser.is_open:
            ser.close()
            print("[+] Port serial ditutup.")
        print("[+] Program selesai.")

if __name__ == "__main__":
    main()
