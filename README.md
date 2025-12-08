# Spotify Dashboard 🎵

A complete local Spotify Dashboard web application built with Python (Flask), Spotipy, HTML, CSS, and JavaScript. Control your Spotify playback, analyze your music mood, create smart playlists, and discover similar tracks - all running locally on your machine.

## Features

### Core Features
- **Now Playing**: Real-time display of currently playing track with album art
- **Playback Controls**: Play/Pause, Next, Previous, and Shuffle buttons
- **Mood Analyzer**: Analyzes your top 20 tracks to determine your music mood (Energetic, Calm, Happy, Sad, Dance/Party, etc.)
- **Audio Visualizer**: Animated canvas visualizer that reacts to your music mood

### Advanced Features
- **Smart Playlist Generator**: Create custom playlists based on mood and tempo preferences
- **Wrapped Stats**: View your top 20 tracks and top 10 artists with duration charts
- **Similar Tracks Finder**: Discover tracks similar to any song based on audio features

## Prerequisites

1. **Spotify Developer Account**: You need a Spotify account and a registered application
   - Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
   - Create a new app
   - Note your Client ID and Client Secret
   - Add `http://localhost:5000/callback` as a Redirect URI

2. **Python 3.8+**: Make sure Python is installed on your system

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/SilFopma4h2/Spotify-multi-web-page.git
   cd Spotify-multi-web-page
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Create keys.json**:
   Create a `keys.json` file in the root directory with your Spotify credentials:
   ```json
   {
     "client_id": "your_spotify_client_id_here",
     "client_secret": "your_spotify_client_secret_here",
     "redirect_uri": "http://localhost:5000/callback"
   }
   ```
   
   You can copy from the example:
   ```bash
   cp keys.json.example keys.json
   # Then edit keys.json with your credentials
   ```

## Usage

1. **Start the Flask server**:
   ```bash
   python app.py
   ```

2. **Open your browser**:
   Navigate to `http://localhost:5000`

3. **Authenticate**:
   - You'll be redirected to Spotify to authorize the app
   - After authorization, you'll be redirected back to the dashboard
   - Your tokens are cached in the `.cache/` directory

## Features Overview

### Dashboard (/)
The main dashboard displays:
- **Now Playing Card**: Current track info with album art and playback controls
- **Mood Analyzer Card**: Real-time analysis of your music taste
- **Visualizer Card**: Animated bars reacting to your mood metrics
- **Smart Playlist Generator Card**: Create custom playlists with mood and tempo filters

### Wrapped (/wrapped)
View your listening statistics:
- Top 20 tracks with album art
- Top 10 artists with genres
- Duration chart visualization

### Similar Tracks (/similar)
Find tracks similar to any song:
- Enter a track ID or use currently playing
- Get 12 most similar tracks with similarity scores
- Based on audio features: danceability, energy, valence, tempo, acousticness, instrumentalness

## API Endpoints

- `GET /api/now` - Get currently playing track
- `POST /api/play` - Resume playback
- `POST /api/pause` - Pause playback
- `POST /api/next` - Skip to next track
- `POST /api/previous` - Go to previous track
- `GET /api/mood` - Get mood analysis
- `POST /api/create_playlist` - Create smart playlist
- `GET /api/wrapped` - Get wrapped statistics
- `GET /api/similar` - Get similar tracks

## Project Structure

```
Spotify-multi-web-page/
├── app.py                 # Flask backend application
├── keys.json             # Spotify API credentials (create this)
├── keys.json.example     # Example credentials file
├── requirements.txt      # Python dependencies
├── .gitignore           # Git ignore rules
├── templates/           # HTML templates
│   ├── index.html       # Main dashboard
│   ├── wrapped.html     # Wrapped/stats page
│   └── similar.html     # Similar tracks page
├── static/              # Static assets
│   ├── style.css        # Stylesheet
│   ├── app.js          # JavaScript
│   └── placeholder.png  # Placeholder image
└── .cache/             # Token cache (auto-created)
```

## Technologies Used

- **Backend**: Flask, Spotipy, Matplotlib
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **APIs**: Spotify Web API
- **Visualization**: Canvas API, Matplotlib

## Features in Detail

### Mood Analyzer
Analyzes your top 20 tracks using Spotify's audio features:
- **Energy**: How intense and active the music is
- **Valence**: Musical positiveness (happy vs sad)
- **Danceability**: How suitable for dancing
- **Tempo**: Speed in beats per minute

### Smart Playlist Generator
Creates playlists using:
- Mood-based targeting (energetic, calm, happy, sad, dance)
- Tempo range filtering
- Recommendation algorithm based on your top tracks

### Similar Tracks
Finds similar tracks using a custom similarity algorithm that compares:
- Danceability, Energy, Valence
- Tempo, Acousticness, Instrumentalness
- Returns similarity score (0-100%)

## Troubleshooting

### "keys.json not found"
Make sure you've created `keys.json` with your Spotify credentials.

### "Authentication failed"
1. Check that your Client ID and Client Secret are correct
2. Verify that `http://localhost:5000/callback` is added to your app's Redirect URIs in Spotify Developer Dashboard

### "No track playing"
Make sure you have Spotify open and playing music on one of your devices.

### Port already in use
If port 5000 is already in use, modify the last line in `app.py`:
```python
app.run(host='0.0.0.0', port=5001, debug=True)  # Changed to 5001
```

## License

MIT License - feel free to use this project for personal or educational purposes.

## Contributing

Pull requests are welcome! For major changes, please open an issue first to discuss what you would like to change.

## Acknowledgments

- Built with [Spotipy](https://spotipy.readthedocs.io/) - Spotify Web API Python library
- Uses [Spotify Web API](https://developer.spotify.com/documentation/web-api/) for all music data
- Inspired by Spotify Wrapped and music visualization projects