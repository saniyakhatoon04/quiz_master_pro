// QuizMaster Pro - Global Utility & Web Audio Engine

let audioContext = null;
let soundEnabled = true;

// Initialize sound preference from localStorage
try {
    const saved = localStorage.getItem('quizmaster_sound');
    if (saved !== null) {
        soundEnabled = (saved === 'true');
    }
} catch (e) {}

function getAudioContext() {
    if (!audioContext) {
        const AudioContextClass = window.AudioContext || window.webkitAudioContext;
        if (AudioContextClass) {
            audioContext = new AudioContextClass();
        }
    }
    if (audioContext && audioContext.state === 'suspended') {
        audioContext.resume();
    }
    return audioContext;
}

function updateSoundIcon() {
    const icon = document.getElementById('soundIcon');
    if (icon) {
        icon.className = soundEnabled ? 'fa-solid fa-volume-high' : 'fa-solid fa-volume-xmark text-slate-500';
    }
}

function toggleSoundEffect() {
    soundEnabled = !soundEnabled;
    try {
        localStorage.setItem('quizmaster_sound', soundEnabled.toString());
    } catch (e) {}
    updateSoundIcon();
    if (soundEnabled) {
        playSelectSound();
    }
}

// 1. Pleasant subtle click / select sound
function playSelectSound() {
    if (!soundEnabled) return;
    try {
        const ctx = getAudioContext();
        if (!ctx) return;
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();

        osc.type = 'sine';
        osc.frequency.setValueAtTime(587.33, ctx.currentTime); // D5
        osc.frequency.exponentialRampToValueAtTime(880, ctx.currentTime + 0.08); // A5

        gain.gain.setValueAtTime(0.12, ctx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.08);

        osc.connect(gain);
        gain.connect(ctx.destination);

        osc.start();
        osc.stop(ctx.currentTime + 0.08);
    } catch (e) {}
}

// 2. Timer tick sound (countdown last 5s)
function playTickSound() {
    if (!soundEnabled) return;
    try {
        const ctx = getAudioContext();
        if (!ctx) return;
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();

        osc.type = 'triangle';
        osc.frequency.setValueAtTime(750, ctx.currentTime);

        gain.gain.setValueAtTime(0.08, ctx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.04);

        osc.connect(gain);
        gain.connect(ctx.destination);

        osc.start();
        osc.stop(ctx.currentTime + 0.04);
    } catch (e) {}
}

// 3. Timeout Boop
function playTimeoutSound() {
    if (!soundEnabled) return;
    try {
        const ctx = getAudioContext();
        if (!ctx) return;
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();

        osc.type = 'sawtooth';
        osc.frequency.setValueAtTime(220, ctx.currentTime);
        osc.frequency.exponentialRampToValueAtTime(110, ctx.currentTime + 0.25);

        gain.gain.setValueAtTime(0.15, ctx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.25);

        osc.connect(gain);
        gain.connect(ctx.destination);

        osc.start();
        osc.stop(ctx.currentTime + 0.25);
    } catch (e) {}
}

// 4. Celebration fanfare sound for Quiz Complete
function playFanfareSound() {
    if (!soundEnabled) return;
    try {
        const ctx = getAudioContext();
        if (!ctx) return;

        const notes = [523.25, 659.25, 783.99, 1046.50]; // C5, E5, G5, C6
        notes.forEach((freq, idx) => {
            const osc = ctx.createOscillator();
            const gain = ctx.createGain();

            osc.type = 'sine';
            osc.frequency.setValueAtTime(freq, ctx.currentTime + (idx * 0.1));

            gain.gain.setValueAtTime(0.15, ctx.currentTime + (idx * 0.1));
            gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + (idx * 0.1) + 0.25);

            osc.connect(gain);
            gain.connect(ctx.destination);

            osc.start(ctx.currentTime + (idx * 0.1));
            osc.stop(ctx.currentTime + (idx * 0.1) + 0.25);
        });
    } catch (e) {}
}

// User Profile dropdown menu toggle
function toggleUserMenu() {
    const dropdown = document.getElementById('userDropdown');
    if (dropdown) {
        dropdown.classList.toggle('hidden');
    }
}

// Close user menu when clicking outside
document.addEventListener('click', (e) => {
    const container = document.getElementById('userMenuContainer');
    const dropdown = document.getElementById('userDropdown');
    if (container && dropdown && !container.contains(e.target)) {
        dropdown.classList.add('hidden');
    }
});

// Password visibility toggle
function togglePasswordVisibility(inputId, iconId) {
    const input = document.getElementById(inputId);
    const icon = document.getElementById(iconId);
    if (input && icon) {
        if (input.type === 'password') {
            input.type = 'text';
            icon.className = 'fa-solid fa-eye-slash';
        } else {
            input.type = 'password';
            icon.className = 'fa-solid fa-eye';
        }
    }
}

document.addEventListener('DOMContentLoaded', () => {
    updateSoundIcon();
});
