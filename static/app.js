// Global state
let currentTrack = null;
let isPlaying = false;
let moodData = null;

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    initializeDashboard();
    initializeVisualizer();
});

function initializeDashboard() {
    // Start auto-refresh for Now Playing
    updateNowPlaying();
    setInterval(updateNowPlaying, 3500);

    // Load mood data
    updateMood();
    setInterval(updateMood, 10000);

    // Setup control buttons
    setupControlButtons();

    // Setup playlist form
    setupPlaylistForm();
}

// Now Playing Functions
async function updateNowPlaying() {
    try {
        const response = await fetch('/api/now');
        const data = await response.json();

        if (data.playing && data.track_name) {
            displayTrack(data);
            currentTrack = data;
            isPlaying = data.is_playing;
            updatePlayButton(data.is_playing);
        } else {
            displayNoTrack();
        }
    } catch (error) {
        console.error('Error fetching now playing:', error);
    }
}

function displayTrack(track) {
    const noTrack = document.getElementById('no-track');
    const trackInfo = document.getElementById('track-info');
    
    noTrack.style.display = 'none';
    trackInfo.style.display = 'block';

    document.getElementById('album-art').src = track.album_art || '/static/placeholder.png';
    document.getElementById('track-name').textContent = track.track_name;
    document.getElementById('track-artist').textContent = track.artists;
    document.getElementById('track-album').textContent = track.album;

    // Update progress bar
    if (track.duration_ms && track.progress_ms) {
        const progress = (track.progress_ms / track.duration_ms) * 100;
        document.getElementById('progress').style.width = `${progress}%`;
    }
}

function displayNoTrack() {
    const noTrack = document.getElementById('no-track');
    const trackInfo = document.getElementById('track-info');
    
    noTrack.style.display = 'block';
    trackInfo.style.display = 'none';
}

function updatePlayButton(playing) {
    const playPauseBtn = document.getElementById('play-pause-btn');
    if (playPauseBtn) {
        playPauseBtn.textContent = playing ? '⏸️' : '▶️';
    }
}

// Control Button Functions
function setupControlButtons() {
    const playPauseBtn = document.getElementById('play-pause-btn');
    const prevBtn = document.getElementById('prev-btn');
    const nextBtn = document.getElementById('next-btn');
    const shuffleBtn = document.getElementById('shuffle-btn');

    if (playPauseBtn) {
        playPauseBtn.addEventListener('click', togglePlayPause);
    }

    if (prevBtn) {
        prevBtn.addEventListener('click', previousTrack);
    }

    if (nextBtn) {
        nextBtn.addEventListener('click', nextTrack);
    }

    if (shuffleBtn) {
        shuffleBtn.addEventListener('click', () => {
            alert('Shuffle toggle requires device selection. This feature shows how to interact with Spotify API for playback controls.');
        });
    }
}

async function togglePlayPause() {
    try {
        const endpoint = isPlaying ? '/api/pause' : '/api/play';
        const response = await fetch(endpoint, { method: 'POST' });
        const data = await response.json();

        if (data.success) {
            isPlaying = !isPlaying;
            updatePlayButton(isPlaying);
            // Immediate update
            setTimeout(updateNowPlaying, 500);
        }
    } catch (error) {
        console.error('Error toggling playback:', error);
    }
}

async function previousTrack() {
    try {
        const response = await fetch('/api/previous', { method: 'POST' });
        const data = await response.json();

        if (data.success) {
            setTimeout(updateNowPlaying, 500);
        }
    } catch (error) {
        console.error('Error skipping to previous:', error);
    }
}

async function nextTrack() {
    try {
        const response = await fetch('/api/next', { method: 'POST' });
        const data = await response.json();

        if (data.success) {
            setTimeout(updateNowPlaying, 500);
        }
    } catch (error) {
        console.error('Error skipping to next:', error);
    }
}

// Mood Analyzer Functions
async function updateMood() {
    try {
        const response = await fetch('/api/mood');
        const data = await response.json();

        if (data.mood) {
            displayMood(data);
            moodData = data;
        }
    } catch (error) {
        console.error('Error fetching mood:', error);
    }
}

function displayMood(data) {
    const moodEmoji = document.getElementById('mood-emoji');
    const moodText = document.getElementById('mood-text');
    
    if (moodEmoji) {
        moodEmoji.textContent = getMoodEmoji(data.mood);
    }
    
    if (moodText) {
        moodText.textContent = data.mood;
    }

    // Update stat bars
    updateStatBar('energy', data.energy);
    updateStatBar('valence', data.valence);
    updateStatBar('danceability', data.danceability);
    updateStatBar('tempo', Math.min(data.tempo / 200, 1)); // Normalize tempo to 0-1
}

function updateStatBar(name, value) {
    const bar = document.getElementById(`${name}-bar`);
    const valueSpan = document.getElementById(`${name}-value`);
    
    if (bar) {
        bar.style.width = `${value * 100}%`;
    }
    
    if (valueSpan) {
        if (name === 'tempo') {
            // Show actual tempo value
            valueSpan.textContent = Math.round(value * 200) + ' BPM';
        } else {
            valueSpan.textContent = (value * 100).toFixed(0) + '%';
        }
    }
}

function getMoodEmoji(mood) {
    const emojiMap = {
        'Energetic & Happy': '🎉',
        'Dance/Party': '💃',
        'Intense': '🔥',
        'Sad/Melancholic': '😢',
        'Calm & Happy': '😊',
        'Calm/Chill': '😌',
        'Happy': '😄',
        'Sad': '😔',
        'Balanced': '⚖️'
    };
    return emojiMap[mood] || '🎵';
}

// Visualizer Functions
function initializeVisualizer() {
    const canvas = document.getElementById('visualizer');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    const barCount = 64;
    const barWidth = canvas.width / barCount;
    let bars = new Array(barCount).fill(0);
    let targetBars = new Array(barCount).fill(0);

    function animate() {
        // Clear canvas
        ctx.fillStyle = 'rgba(25, 20, 20, 0.3)';
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        // Use mood data to influence visualization
        const energy = moodData ? moodData.energy : 0.5;
        const danceability = moodData ? moodData.danceability : 0.5;
        const valence = moodData ? moodData.valence : 0.5;

        // Update target heights based on mood
        for (let i = 0; i < barCount; i++) {
            // Create wave patterns influenced by mood
            const time = Date.now() / 1000;
            const waveSpeed = 1 + energy * 2;
            const amplitude = 0.3 + energy * 0.5;
            
            const wave1 = Math.sin(time * waveSpeed + i * 0.1) * amplitude;
            const wave2 = Math.sin(time * waveSpeed * 1.5 - i * 0.15) * amplitude * 0.5;
            const wave3 = Math.cos(time * waveSpeed * 0.8 + i * 0.2) * amplitude * 0.3;
            
            targetBars[i] = (wave1 + wave2 + wave3 + 1) / 2;
            
            // Add random spikes based on danceability
            if (Math.random() < danceability * 0.02) {
                targetBars[i] = Math.min(targetBars[i] + Math.random() * 0.3, 1);
            }
        }

        // Smooth interpolation
        for (let i = 0; i < barCount; i++) {
            bars[i] += (targetBars[i] - bars[i]) * 0.1;
            
            const height = bars[i] * canvas.height * 0.8;
            const x = i * barWidth;
            const y = canvas.height - height;

            // Color gradient based on valence (happiness)
            const hue = 120 + valence * 60; // Green to yellow based on valence
            const saturation = 70 + energy * 30;
            const lightness = 40 + bars[i] * 30;
            
            ctx.fillStyle = `hsl(${hue}, ${saturation}%, ${lightness}%)`;
            ctx.fillRect(x, y, barWidth - 2, height);

            // Add glow effect
            ctx.shadowBlur = 10 + bars[i] * 20;
            ctx.shadowColor = `hsl(${hue}, 100%, 50%)`;
        }

        requestAnimationFrame(animate);
    }

    animate();
}

// Playlist Generator Functions
function setupPlaylistForm() {
    const createBtn = document.getElementById('create-playlist-btn');
    
    if (createBtn) {
        createBtn.addEventListener('click', createPlaylist);
    }
}

async function createPlaylist() {
    const name = document.getElementById('playlist-name').value;
    const mood = document.getElementById('playlist-mood').value;
    const tempoMin = document.getElementById('tempo-min').value;
    const tempoMax = document.getElementById('tempo-max').value;
    const resultDiv = document.getElementById('playlist-result');
    const createBtn = document.getElementById('create-playlist-btn');

    // Validation
    if (!name.trim()) {
        showResult(resultDiv, 'Please enter a playlist name', 'error');
        return;
    }

    if (parseInt(tempoMin) >= parseInt(tempoMax)) {
        showResult(resultDiv, 'Min tempo must be less than max tempo', 'error');
        return;
    }

    // Disable button and show loading
    createBtn.disabled = true;
    createBtn.textContent = 'Creating...';

    try {
        const response = await fetch('/api/create_playlist', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                name,
                mood,
                tempo_min: parseInt(tempoMin),
                tempo_max: parseInt(tempoMax)
            })
        });

        const data = await response.json();

        if (data.success) {
            showResult(
                resultDiv,
                `✅ Created "${data.playlist_name}" with ${data.tracks_added} tracks!`,
                'success'
            );
        } else {
            showResult(resultDiv, `Error: ${data.error}`, 'error');
        }
    } catch (error) {
        console.error('Error creating playlist:', error);
        showResult(resultDiv, 'Error creating playlist. Please try again.', 'error');
    } finally {
        // Re-enable button
        createBtn.disabled = false;
        createBtn.textContent = 'Create Playlist';
    }
}

function showResult(element, message, type) {
    element.textContent = message;
    element.className = `result-message ${type}`;
    element.style.display = 'block';

    // Auto-hide after 5 seconds
    setTimeout(() => {
        element.style.display = 'none';
    }, 5000);
}
