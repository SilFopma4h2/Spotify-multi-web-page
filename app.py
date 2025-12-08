import json
import os
import base64
from io import BytesIO
from flask import Flask, render_template, redirect, request, jsonify, session
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotipy.cache_handler import CacheFileHandler
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image
import requests

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Load credentials from keys.json
def load_credentials():
    try:
        with open('keys.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("ERROR: keys.json not found. Please create it from keys.json.example")
        return None

credentials = load_credentials()
if not credentials:
    print("Please create keys.json with your Spotify credentials")
    exit(1)

CLIENT_ID = credentials['client_id']
CLIENT_SECRET = credentials['client_secret']
REDIRECT_URI = credentials['redirect_uri']

SCOPE = "user-read-playback-state user-modify-playback-state user-read-currently-playing " \
        "user-top-read playlist-modify-public playlist-modify-private user-library-read"

def get_spotify_oauth():
    """Get SpotifyOAuth instance with proper cache handler"""
    cache_handler = CacheFileHandler(cache_path='.cache')
    return SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        scope=SCOPE,
        cache_handler=cache_handler,
        show_dialog=False
    )

def get_spotify_client():
    """Get authenticated Spotify client"""
    sp_oauth = get_spotify_oauth()
    token_info = sp_oauth.get_cached_token()
    
    if not token_info:
        return None
    
    return spotipy.Spotify(auth=token_info['access_token'])

@app.route('/')
def index():
    """Main dashboard page"""
    sp_oauth = get_spotify_oauth()
    token_info = sp_oauth.get_cached_token()
    
    if not token_info:
        return redirect('/login')
    
    return render_template('index.html')

@app.route('/login')
def login():
    """Redirect to Spotify authorization"""
    sp_oauth = get_spotify_oauth()
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

@app.route('/callback')
def callback():
    """Handle Spotify OAuth callback"""
    sp_oauth = get_spotify_oauth()
    code = request.args.get('code')
    
    if code:
        token_info = sp_oauth.get_access_token(code)
        return redirect('/')
    
    return redirect('/login')

@app.route('/wrapped')
def wrapped():
    """Wrapped/stats page"""
    sp = get_spotify_client()
    if not sp:
        return redirect('/login')
    return render_template('wrapped.html')

@app.route('/similar')
def similar():
    """Similar tracks finder page"""
    sp = get_spotify_client()
    if not sp:
        return redirect('/login')
    return render_template('similar.html')

# API Endpoints

@app.route('/api/now')
def now_playing():
    """Get currently playing track"""
    sp = get_spotify_client()
    if not sp:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        current = sp.current_playback()
        
        if not current or not current.get('item'):
            return jsonify({'playing': False})
        
        track = current['item']
        return jsonify({
            'playing': True,
            'is_playing': current['is_playing'],
            'track_name': track['name'],
            'artists': ', '.join([artist['name'] for artist in track['artists']]),
            'album': track['album']['name'],
            'album_art': track['album']['images'][0]['url'] if track['album']['images'] else None,
            'duration_ms': track['duration_ms'],
            'progress_ms': current['progress_ms'],
            'track_id': track['id']
        })
    except Exception as e:
        return jsonify({'error': str(e), 'playing': False}), 500

@app.route('/api/play', methods=['POST'])
def play():
    """Resume playback"""
    sp = get_spotify_client()
    if not sp:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        sp.start_playback()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/pause', methods=['POST'])
def pause():
    """Pause playback"""
    sp = get_spotify_client()
    if not sp:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        sp.pause_playback()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/next', methods=['POST'])
def next_track():
    """Skip to next track"""
    sp = get_spotify_client()
    if not sp:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        sp.next_track()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/previous', methods=['POST'])
def previous_track():
    """Skip to previous track"""
    sp = get_spotify_client()
    if not sp:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        sp.previous_track()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/mood')
def get_mood():
    """Calculate mood from top tracks"""
    sp = get_spotify_client()
    if not sp:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        # Get top 20 tracks
        top_tracks = sp.current_user_top_tracks(limit=20, time_range='short_term')
        
        if not top_tracks['items']:
            return jsonify({'error': 'No top tracks found'}), 404
        
        # Get audio features for tracks
        track_ids = [track['id'] for track in top_tracks['items']]
        audio_features = sp.audio_features(track_ids)
        
        # Filter out None values
        audio_features = [f for f in audio_features if f]
        
        if not audio_features:
            return jsonify({'error': 'No audio features found'}), 404
        
        # Calculate averages
        avg_energy = sum(f['energy'] for f in audio_features) / len(audio_features)
        avg_valence = sum(f['valence'] for f in audio_features) / len(audio_features)
        avg_danceability = sum(f['danceability'] for f in audio_features) / len(audio_features)
        avg_tempo = sum(f['tempo'] for f in audio_features) / len(audio_features)
        
        # Determine mood
        mood = determine_mood(avg_energy, avg_valence, avg_danceability)
        
        return jsonify({
            'mood': mood,
            'energy': round(avg_energy, 2),
            'valence': round(avg_valence, 2),
            'danceability': round(avg_danceability, 2),
            'tempo': round(avg_tempo, 2)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def determine_mood(energy, valence, danceability):
    """Determine mood based on audio features"""
    if energy > 0.7 and valence > 0.6:
        return "Energetic & Happy"
    elif energy > 0.7 and danceability > 0.7:
        return "Dance/Party"
    elif energy > 0.6 and valence < 0.4:
        return "Intense"
    elif energy < 0.4 and valence < 0.4:
        return "Sad/Melancholic"
    elif energy < 0.5 and valence > 0.5:
        return "Calm & Happy"
    elif energy < 0.4:
        return "Calm/Chill"
    elif valence > 0.6:
        return "Happy"
    elif valence < 0.4:
        return "Sad"
    else:
        return "Balanced"

@app.route('/api/create_playlist', methods=['POST'])
def create_playlist():
    """Create a smart playlist based on mood and tempo"""
    sp = get_spotify_client()
    if not sp:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        data = request.json
        playlist_name = data.get('name', 'Smart Playlist')
        mood = data.get('mood', 'energetic')
        tempo_min = int(data.get('tempo_min', 100))
        tempo_max = int(data.get('tempo_max', 150))
        
        # Get user ID
        user = sp.current_user()
        user_id = user['id']
        
        # Create playlist
        playlist = sp.user_playlist_create(user_id, playlist_name, public=False)
        playlist_id = playlist['id']
        
        # Get seed tracks from top tracks
        top_tracks = sp.current_user_top_tracks(limit=5, time_range='short_term')
        seed_tracks = [track['id'] for track in top_tracks['items'][:5]]
        
        # Set target features based on mood
        target_features = get_mood_features(mood)
        
        # Get recommendations
        recommendations = sp.recommendations(
            seed_tracks=seed_tracks,
            limit=25,
            min_tempo=tempo_min,
            max_tempo=tempo_max,
            **target_features
        )
        
        # Add tracks to playlist
        track_uris = [track['uri'] for track in recommendations['tracks']]
        if track_uris:
            sp.playlist_add_items(playlist_id, track_uris)
        
        return jsonify({
            'success': True,
            'playlist_name': playlist_name,
            'playlist_id': playlist_id,
            'tracks_added': len(track_uris),
            'url': playlist['external_urls']['spotify']
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def get_mood_features(mood):
    """Get target audio features for different moods"""
    mood_map = {
        'energetic': {'target_energy': 0.8, 'target_valence': 0.7},
        'calm': {'target_energy': 0.3, 'target_valence': 0.5},
        'happy': {'target_energy': 0.6, 'target_valence': 0.8},
        'sad': {'target_energy': 0.3, 'target_valence': 0.2},
        'dance': {'target_energy': 0.8, 'target_danceability': 0.8}
    }
    return mood_map.get(mood.lower(), {'target_energy': 0.5})

@app.route('/api/wrapped')
def wrapped_data():
    """Get wrapped/stats data (top tracks, artists, chart)"""
    sp = get_spotify_client()
    if not sp:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        # Get top tracks
        top_tracks_data = sp.current_user_top_tracks(limit=20, time_range='medium_term')
        top_tracks = [{
            'name': track['name'],
            'artists': ', '.join([artist['name'] for artist in track['artists']]),
            'duration_ms': track['duration_ms'],
            'album_art': track['album']['images'][0]['url'] if track['album']['images'] else None
        } for track in top_tracks_data['items']]
        
        # Get top artists
        top_artists_data = sp.current_user_top_artists(limit=10, time_range='medium_term')
        top_artists = [{
            'name': artist['name'],
            'genres': ', '.join(artist['genres'][:3]),
            'image': artist['images'][0]['url'] if artist['images'] else None
        } for artist in top_artists_data['items']]
        
        # Create chart
        chart_base64 = create_duration_chart(top_tracks)
        
        return jsonify({
            'top_tracks': top_tracks,
            'top_artists': top_artists,
            'chart': chart_base64
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def create_duration_chart(tracks):
    """Create a base64 encoded bar chart of track durations"""
    if not tracks:
        return None
    
    try:
        # Take top 10 for chart
        chart_tracks = tracks[:10]
        names = [t['name'][:20] + '...' if len(t['name']) > 20 else t['name'] 
                 for t in chart_tracks]
        durations = [t['duration_ms'] / 60000 for t in chart_tracks]  # Convert to minutes
        
        plt.figure(figsize=(10, 6))
        plt.barh(names, durations, color='#1DB954')
        plt.xlabel('Duration (minutes)')
        plt.title('Top Tracks Duration')
        plt.gca().invert_yaxis()
        plt.tight_layout()
        
        # Convert to base64
        buf = BytesIO()
        plt.savefig(buf, format='png', facecolor='#191414', edgecolor='none')
        buf.seek(0)
        chart_base64 = base64.b64encode(buf.read()).decode('utf-8')
        plt.close()
        
        return f"data:image/png;base64,{chart_base64}"
    except Exception as e:
        print(f"Chart error: {e}")
        return None

@app.route('/api/similar')
def similar_tracks():
    """Get similar tracks based on audio features"""
    sp = get_spotify_client()
    if not sp:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        track_id = request.args.get('track_id')
        
        # If no track_id, use currently playing
        if not track_id:
            current = sp.current_playback()
            if current and current.get('item'):
                track_id = current['item']['id']
            else:
                return jsonify({'error': 'No track playing and no track_id provided'}), 400
        
        # Get track info and audio features
        track = sp.track(track_id)
        features = sp.audio_features([track_id])[0]
        
        if not features:
            return jsonify({'error': 'Could not get audio features'}), 404
        
        # Get recommendations based on audio features
        recommendations = sp.recommendations(
            seed_tracks=[track_id],
            limit=12,
            target_danceability=features['danceability'],
            target_energy=features['energy'],
            target_valence=features['valence'],
            target_tempo=features['tempo'],
            target_acousticness=features['acousticness'],
            target_instrumentalness=features['instrumentalness']
        )
        
        # Get audio features for recommended tracks
        rec_track_ids = [t['id'] for t in recommendations['tracks']]
        rec_features = sp.audio_features(rec_track_ids)
        
        # Calculate similarity scores
        similar = []
        for i, rec_track in enumerate(recommendations['tracks']):
            if rec_features[i]:
                similarity = calculate_similarity(features, rec_features[i])
                similar.append({
                    'name': rec_track['name'],
                    'artists': ', '.join([artist['name'] for artist in rec_track['artists']]),
                    'album': rec_track['album']['name'],
                    'album_art': rec_track['album']['images'][0]['url'] if rec_track['album']['images'] else None,
                    'similarity': round(similarity * 100, 1),
                    'track_id': rec_track['id']
                })
        
        # Sort by similarity
        similar.sort(key=lambda x: x['similarity'], reverse=True)
        
        return jsonify({
            'original_track': {
                'name': track['name'],
                'artists': ', '.join([artist['name'] for artist in track['artists']])
            },
            'similar_tracks': similar
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def calculate_similarity(features1, features2):
    """Calculate similarity score between two tracks based on audio features"""
    # Features to compare with their weights
    feature_weights = {
        'danceability': 1.0,
        'energy': 1.0,
        'valence': 1.0,
        'tempo': 0.5,  # Less weight as it varies more
        'acousticness': 0.8,
        'instrumentalness': 0.8
    }
    
    total_similarity = 0
    total_weight = 0
    
    for feature, weight in feature_weights.items():
        if feature == 'tempo':
            # Normalize tempo difference (typical range: 50-200 bpm)
            diff = abs(features1[feature] - features2[feature]) / 150
            similarity = max(0, 1 - diff)
        else:
            # Other features are already 0-1
            diff = abs(features1[feature] - features2[feature])
            similarity = 1 - diff
        
        total_similarity += similarity * weight
        total_weight += weight
    
    return total_similarity / total_weight if total_weight > 0 else 0

if __name__ == '__main__':
    # Ensure .cache directory exists
    os.makedirs('.cache', exist_ok=True)
    print("Starting Spotify Dashboard on http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)
