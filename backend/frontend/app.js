/* ==========================================================================
   JAVASCRIPT UNTUK DASHBOARD JEMURAN
   Fungsi: Real-time API Polling, Audio Alarm Synthesis, & Animasi Partikel
   ========================================================================== */

// State Global
let currentStatus = {
    status_cuaca: '',
    kondisi_jemuran: '',
    warna: '',
    peringatan: ''
};
let soundEnabled = false;
let audioCtx = null;
let alarmInterval = null;
let previousWeather = '';

// DOM Elements
const bodyContainer = document.getElementById('body-container');
const connBadge = document.getElementById('conn-badge');
const connText = document.getElementById('conn-text');
const alertBanner = document.getElementById('alert-banner');
const alertText = document.getElementById('alert-text');
const btnSoundToggle = document.getElementById('btn-sound-toggle');
const soundStatusText = document.getElementById('sound-status-text');

// Cards & Badges
const cardCuaca = document.getElementById('card-cuaca');
const weatherBadge = document.getElementById('weather-badge');
const weatherValue = document.getElementById('weather-value');
const weatherIconContainer = document.getElementById('weather-icon-container');

const cardJemuran = document.getElementById('card-jemuran');
const laundryBadge = document.getElementById('laundry-badge');
const laundryValue = document.getElementById('laundry-value');
const laundryIconContainer = document.getElementById('laundry-icon-container');

const timeUpdate = document.getElementById('time-update');
const historyBody = document.getElementById('history-body');

// Rain & Mist Containers
const rainContainer = document.getElementById('rain-container');
const mistContainer = document.getElementById('mist-container');

/* ==========================================================================
   WEATHER ANIMATION EFFECTS (RAIN & MIST)
   ========================================================================== */

function setupRainOverlay(active) {
    rainContainer.innerHTML = '';
    if (!active) return;
    
    // Buat 40 partikel air jatuh dengan posisi horizontal & delay acak
    const dropCount = 45;
    for (let i = 0; i < dropCount; i++) {
        const drop = document.createElement('div');
        drop.className = 'rain-drop';
        drop.style.left = `${Math.random() * 100}%`;
        drop.style.top = `${Math.random() * -20}px`;
        drop.style.animationDelay = `${Math.random() * 2}s`;
        drop.style.animationDuration = `${0.6 + Math.random() * 0.8}s`;
        rainContainer.appendChild(drop);
    }
}

function setupMistOverlay(active) {
    mistContainer.innerHTML = '';
    if (!active) return;
    
    // Buat awan kabut tipis yang bergerak perlahan
    const cloudCount = 5;
    for (let i = 0; i < cloudCount; i++) {
        const cloud = document.createElement('div');
        cloud.className = 'mist-cloud';
        
        const size = 150 + Math.random() * 250;
        cloud.style.width = `${size}px`;
        cloud.style.height = `${size}px`;
        cloud.style.top = `${Math.random() * 60}%`;
        cloud.style.animationDelay = `${Math.random() * -10}s`;
        cloud.style.animationDuration = `${25 + Math.random() * 25}s`;
        
        mistContainer.appendChild(cloud);
    }
}

/* ==========================================================================
   WEB AUDIO API ALARM SYNTHESIS
   ========================================================================== */

function initAudio() {
    if (!audioCtx) {
        audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    }
}

function playBeep(frequency, duration) {
    if (!audioCtx || audioCtx.state === 'suspended') {
        try {
            audioCtx.resume();
        } catch (e) {
            console.error("Gagal mengaktifkan AudioContext:", e);
            return;
        }
    }
    
    try {
        const osc = audioCtx.createOscillator();
        const gain = audioCtx.createGain();
        
        osc.type = 'sine';
        osc.frequency.setValueAtTime(frequency, audioCtx.currentTime);
        
        gain.gain.setValueAtTime(0.08, audioCtx.currentTime); // volume rendah agar nyaman
        gain.gain.exponentialRampToValueAtTime(0.0001, audioCtx.currentTime + duration);
        
        osc.connect(gain);
        gain.connect(audioCtx.destination);
        
        osc.start();
        osc.stop(audioCtx.currentTime + duration);
    } catch (e) {
        console.error("Kesalahan Audio Synthesis:", e);
    }
}

function startAlarm() {
    if (alarmInterval) return; // sudah berjalan
    
    // Alarm berbunyi beep ganda setiap 1.5 detik
    alarmInterval = setInterval(() => {
        if (!soundEnabled) {
            stopAlarm();
            return;
        }
        
        playBeep(880, 0.12); // Beep ke-1 (A5)
        setTimeout(() => {
            if (soundEnabled && currentStatus.status_cuaca === 'HUJAN') {
                playBeep(880, 0.12); // Beep ke-2
            }
        }, 180);
    }, 1500);
}

function stopAlarm() {
    if (alarmInterval) {
        clearInterval(alarmInterval);
        alarmInterval = null;
    }
}

// Event Handler: Klik tombol suara
btnSoundToggle.addEventListener('click', () => {
    initAudio();
    soundEnabled = !soundEnabled;
    
    if (soundEnabled) {
        soundStatusText.textContent = 'Mendengarkan Peringatan...';
        btnSoundToggle.classList.remove('sound-off');
        btnSoundToggle.classList.add('sound-on');
        
        // Bunyi konfirmasi beep pendek
        playBeep(1000, 0.1);
        
        // Jika sedang hujan saat suara diaktifkan, jalankan alarm
        if (currentStatus.status_cuaca === 'HUJAN') {
            btnSoundToggle.classList.add('sound-alarm');
            startAlarm();
        }
    } else {
        soundStatusText.textContent = 'Alarm Dinonaktifkan';
        btnSoundToggle.classList.remove('sound-on', 'sound-alarm');
        btnSoundToggle.classList.add('sound-off');
        stopAlarm();
    }
});

// Tutup Alert Banner manual
document.getElementById('alert-dismiss').addEventListener('click', () => {
    alertBanner.style.display = 'none';
});

/* ==========================================================================
   DOM MANIPULATION (SVG ICONS & CARDS)
   ========================================================================== */

// Kumpulan SVG Icons agar tidak perlu mengambil file gambar eksternal
const ICONS = {
    hujan: `
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="weather-icon rain-icon">
            <path d="M20 16.58A5 5 0 0018 7h-1.26A8 8 0 104 15.25" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M8 18v2M12 19v2M16 18v2M10 14l-2 2M14 14l-2 2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
    `,
    gerimis: `
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="weather-icon drizzle-icon">
            <path d="M20 16.58A5 5 0 0018 7h-1.26A8 8 0 104 15.25" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M8 18v1M12 18v1M16 18v1" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
    `,
    cerah: `
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="weather-icon clear-icon">
            <circle cx="12" cy="12" r="5" fill="rgba(255, 193, 7, 0.2)"/>
            <path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
    `,
    laundryDanger: `
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="laundry-icon">
            <path d="M20.37 4.65c-.32-.23-.74-.29-1.12-.17l-3.37 1.05C15.11 3.53 13.67 2.22 12 2.22s-3.11 1.31-3.88 3.31L4.75 4.48c-.38-.12-.8-.06-1.12.17-.32.23-.5.6-.49.99V19.5c0 1.24.97 2.28 2.21 2.28H18.6c1.24 0 2.21-1.04 2.21-2.28V5.64c.01-.39-.17-.76-.44-.99zM12 4.22c.98 0 1.77.78 1.96 1.83L10.04 6.05c.19-1.05.98-1.83 1.96-1.83z" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M8 12h8M8 16h8" stroke-linecap="round" stroke-linejoin="round"/>
            <circle cx="12" cy="14" r="3" fill="rgba(239, 68, 68, 0.1)"/>
        </svg>
    `,
    laundrySafe: `
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="laundry-icon">
            <path d="M20.37 4.65c-.32-.23-.74-.29-1.12-.17l-3.37 1.05C15.11 3.53 13.67 2.22 12 2.22s-3.11 1.31-3.88 3.31L4.75 4.48c-.38-.12-.8-.06-1.12.17-.32.23-.5.6-.49.99V19.5c0 1.24.97 2.28 2.21 2.28H18.6c1.24 0 2.21-1.04 2.21-2.28V5.64c.01-.39-.17-.76-.44-.99zM12 4.22c.98 0 1.77.78 1.96 1.83L10.04 6.05c.19-1.05.98-1.83 1.96-1.83z" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M9 14l2 2 4-4" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
    `
};

function updateUI(data) {
    // 1. Update Connection Badge
    connBadge.className = 'status-connection-badge connected';
    connText.textContent = 'Tersambung ke Sensor';
    
    // 2. Olah Variabel Cuaca
    const rawWeather = data.status_cuaca.toUpperCase();
    let displayWeatherClass = 'weather-none';
    let badgeClass = 'badge-gray';
    let cardWeatherClass = '';
    let weatherIconSvg = '';
    
    if (rawWeather.includes('HUJAN')) {
        displayWeatherClass = 'weather-hujan';
        badgeClass = 'badge-red';
        cardWeatherClass = 'card-hujan';
        weatherIconSvg = ICONS.hujan;
    } else if (rawWeather.includes('GERIMIS')) {
        displayWeatherClass = 'weather-gerimis';
        badgeClass = 'badge-yellow';
        cardWeatherClass = 'card-gerimis';
        weatherIconSvg = ICONS.gerimis;
    } else if (rawWeather.includes('CERAH') || rawWeather.includes('KERING')) {
        displayWeatherClass = 'weather-cerah';
        badgeClass = 'badge-green';
        cardWeatherClass = 'card-cerah';
        weatherIconSvg = ICONS.cerah;
    }
    
    // Update theme & animations jika cuaca berubah
    if (previousWeather !== displayWeatherClass) {
        bodyContainer.className = `theme-dark ${displayWeatherClass}`;
        
        setupRainOverlay(displayWeatherClass === 'weather-hujan');
        setupMistOverlay(displayWeatherClass === 'weather-gerimis');
        
        previousWeather = displayWeatherClass;
    }
    
    // Update teks & visual Card Cuaca
    weatherValue.textContent = data.status_cuaca;
    weatherBadge.className = `badge ${badgeClass}`;
    weatherBadge.textContent = data.status_cuaca.includes('CERAH') ? 'Normal' : 'Siaga';
    cardCuaca.className = `card status-card ${cardWeatherClass}`;
    weatherIconContainer.innerHTML = weatherIconSvg;
    
    // 3. Olah Variabel Jemuran
    const rawLaundry = data.kondisi_jemuran.toLowerCase();
    let badgeLaundryClass = 'badge-green';
    let cardLaundryClass = 'card-laundry-safe';
    let laundryIconSvg = ICONS.laundrySafe;
    
    if (rawLaundry.includes('angkat') || rawLaundry.includes('segera')) {
        badgeLaundryClass = 'badge-red';
        cardLaundryClass = 'card-laundry-danger';
        laundryIconSvg = ICONS.laundryDanger;
    }
    
    laundryValue.textContent = data.kondisi_jemuran;
    laundryBadge.className = `badge ${badgeLaundryClass}`;
    laundryBadge.textContent = rawLaundry.includes('angkat') ? 'Segera Angkat' : 'Aman';
    cardJemuran.className = `card laundry-card ${cardLaundryClass}`;
    laundryIconContainer.innerHTML = laundryIconSvg;
    
    // 4. Update Alarm Keadaan Hujan
    if (rawWeather.includes('HUJAN')) {
        // Tampilkan Banner Alert
        alertBanner.style.display = 'flex';
        alertText.textContent = `PERINGATAN: ${data.peringatan || 'Jemuran terkena hujan!'}`;
        
        if (soundEnabled) {
            btnSoundToggle.classList.add('sound-alarm');
            startAlarm();
        }
    } else {
        alertBanner.style.display = 'none';
        btnSoundToggle.classList.remove('sound-alarm');
        stopAlarm();
    }
    
    // 5. Update Metadata Update Terakhir
    if (data.timestamp && data.timestamp !== '-') {
        // Memformat timestamp YYYY-MM-DD HH:MM:SS menjadi HH:MM WIB
        try {
            const timePart = data.timestamp.split(' ')[1];
            const hm = timePart.substring(0, 5);
            timeUpdate.textContent = `${hm} WIB`;
        } catch (e) {
            timeUpdate.textContent = data.timestamp;
        }
    } else {
        timeUpdate.textContent = '-';
    }
}

function handleDisconnect() {
    connBadge.className = 'status-connection-badge disconnected';
    connText.textContent = 'Menghubungkan kembali...';
}

/* ==========================================================================
   API DATA FETCHING
   ========================================================================== */

async function fetchStatus() {
    try {
        const response = await fetch('/api/status');
        if (!response.ok) throw new Error('Network error');
        
        const data = await response.json();
        
        // Bandingkan apakah ada pembaruan data
        if (JSON.stringify(currentStatus) !== JSON.stringify(data)) {
            currentStatus = data;
            updateUI(data);
            // Ambil riwayat terbaru jika ada perubahan
            fetchHistory();
        }
    } catch (error) {
        console.warn("Koneksi API gagal:", error);
        handleDisconnect();
    }
}

async function fetchHistory() {
    try {
        const response = await fetch('/api/history');
        if (!response.ok) throw new Error('Network error');
        
        const logs = await response.json();
        renderHistory(logs);
    } catch (error) {
        console.warn("Gagal mengambil riwayat:", error);
    }
}

function renderHistory(logs) {
    if (!logs || logs.length === 0) {
        historyBody.innerHTML = `
            <tr>
                <td colspan="5" class="table-empty">Belum ada riwayat tercatat.</td>
            </tr>
        `;
        return;
    }
    
    let html = '';
    logs.forEach((log, index) => {
        // Tentukan warna badge cuaca di tabel
        let badgeClass = 'table-badge-gray';
        const weather = log.status_cuaca.toUpperCase();
        if (weather.includes('HUJAN')) badgeClass = 'table-badge-red';
        else if (weather.includes('GERIMIS')) badgeClass = 'table-badge-yellow';
        else if (weather.includes('CERAH') || weather.includes('KERING')) badgeClass = 'table-badge-green';
        
        // Format tanggal/jam agar lebih manusiawi
        // YYYY-MM-DD HH:MM:SS
        let formattedTime = log.timestamp;
        try {
            const parts = log.timestamp.split(' ');
            const dateParts = parts[0].split('-');
            const timeParts = parts[1].substring(0, 5);
            formattedTime = `${dateParts[2]}/${dateParts[1]} - ${timeParts} WIB`;
        } catch (e) {}

        const peringatanHtml = log.peringatan.toLowerCase().includes('aman') 
            ? `<span class="text-success">${log.peringatan}</span>` 
            : `<span class="text-danger" style="font-weight:600;">${log.peringatan}</span>`;
            
        html += `
            <tr>
                <td>${index + 1}</td>
                <td>${formattedTime}</td>
                <td><span class="table-badge ${badgeClass}">${log.status_cuaca}</span></td>
                <td>${log.kondisi_jemuran}</td>
                <td>${peringatanHtml}</td>
            </tr>
        `;
    });
    
    historyBody.innerHTML = html;
}

// Jalankan Polling saat halaman dimuat
window.addEventListener('DOMContentLoaded', () => {
    // Jalankan pemanggilan pertama
    fetchStatus();
    fetchHistory();
    
    // Polling setiap 1.5 detik
    setInterval(fetchStatus, 1500);
});
