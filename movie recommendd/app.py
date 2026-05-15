import streamlit as st
import pickle
import requests
import pandas as pd
from typing import Optional
import urllib.parse
import urllib.request
import re
import random
import ast
import time
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor, as_completed

# ── Page config ────────────────────────────────────────────
st.set_page_config(
    page_title="CinematchFlix",
    page_icon="🍿",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize Session State
if 'view' not in st.session_state:
    st.session_state.view = "home"
if 'selected_genre' not in st.session_state:
    st.session_state.selected_genre = "All Movies"

# ── Load model ─────────────────────────────────────────────
@st.cache_resource
def load_model():
    try:
        with st.status("🚀 Initializing AI Engine...", expanded=False) as status:
            st.write("Loading movie database...")
            with open("movie_dict.pkl", "rb") as f:
                movies_dict = pickle.load(f)
            movies = pd.DataFrame(movies_dict)
            
            st.write("Loading similarity matrix (184MB)...")
            with open("similarity.pkl", "rb") as f:
                similarity = pickle.load(f)
            
            st.write("Enriching movie metadata...")
            # Enrich data inside cache
            if 'genres_display' not in movies.columns:
                try:
                    tmdb = pd.read_csv("tmdb_5000_movies.csv")
                    tmdb['id'] = pd.to_numeric(tmdb['id'], errors='coerce').fillna(0).astype(int)
                    movies['movie_id'] = pd.to_numeric(movies['movie_id'], errors='coerce').fillna(0).astype(int)
                    tmdb_subset = tmdb[['id', 'genres', 'vote_average', 'release_date', 'overview']].rename(columns={'id': 'movie_id'})
                    movies = movies.merge(tmdb_subset, on='movie_id', how='left')
                    
                    def parse_gen(s):
                        try: 
                            if isinstance(s, str) and s.startswith('['):
                                return [g['name'] for g in ast.literal_eval(s)]
                            return []
                        except: return []
                    movies['genres_display'] = movies['genres'].apply(parse_gen)
                except Exception as e:
                    print(f"Enrichment error: {e}")
            
            status.update(label="✅ System Ready!", state="complete", expanded=False)
            return movies, similarity
    except Exception as e:
        st.error(f"FATAL ERROR: Could not load models. Please ensure 'movie_dict.pkl' and 'similarity.pkl' are in the same folder. Error: {e}")
        st.stop()

movies, similarity = load_model()

# ── CSS ────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&display=swap');

*, html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

/* True Netflix Dark Background */
.stApp { background: #141414; color: #e5e5e5; }
.block-container { padding-top: 1rem !important; padding-bottom: 2rem !important; max-width: 1400px; }

/* ── NAVBAR ── */
.navbar {
    display: flex; align-items: center; justify-content: space-between;
    padding: 10px 0 20px 0; margin-bottom: 10px;
}
.nav-logo {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 3rem; font-weight: 400; letter-spacing: 1.5px;
    color: #e50914; margin: 0; padding: 0; line-height: 1;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
}

/* ── SEARCH BOX STYLING ── */
div[data-testid="stTextInput"] > div > div > input {
    background: rgba(0,0,0,0.8) !important;
    border: 1px solid #444 !important;
    color: #fff !important;
    font-size: 1.1rem !important;
    padding: 12px 16px !important;
    border-radius: 4px !important;
}
div[data-testid="stTextInput"] > div > div > input:focus {
    border-color: #e50914 !important;
    box-shadow: none !important;
}

/* ── HORIZONTAL SCROLL ROW (NETFLIX STYLE) ── */
.row-header { font-size: 1.5rem; font-weight: 700; color: #e5e5e5; margin: 30px 0 15px 0; }
.scrolling-wrapper {
    display: flex; flex-wrap: nowrap; overflow-x: auto;
    padding-bottom: 20px; gap: 15px;
    -webkit-overflow-scrolling: touch;
}
.scrolling-wrapper::-webkit-scrollbar { height: 8px; }
.scrolling-wrapper::-webkit-scrollbar-track { background: #141414; }
.scrolling-wrapper::-webkit-scrollbar-thumb { background: #333; border-radius: 4px; }
.scrolling-wrapper::-webkit-scrollbar-thumb:hover { background: #555; }

/* Movie Card */
.card-container {
    flex: 0 0 auto; width: 220px; position: relative;
    border-radius: 8px; overflow: hidden;
    transition: transform 0.3s ease; cursor: pointer;
}
.card-container:hover { transform: scale(1.05); z-index: 10; box-shadow: 0 10px 20px rgba(0,0,0,0.8); }
.card-container img {
    width: 100%; height: 330px; object-fit: cover; display: block; border-radius: 8px;
}
.card-ph {
    width: 100%; height: 330px; background: #222; border-radius: 8px;
    display: flex; align-items: center; justify-content: center;
    color: #666; font-size: 1rem; text-align: center; padding: 10px;
}
.card-overlay {
    position: absolute; bottom: 0; left: 0; right: 0;
    background: linear-gradient(to top, rgba(0,0,0,0.95) 0%, rgba(0,0,0,0) 100%);
    padding: 30px 10px 15px 10px; opacity: 0; transition: opacity 0.3s ease;
}
.card-container:hover .card-overlay { opacity: 1; }
.card-title { font-size: 1rem; font-weight: 700; color: #fff; line-height: 1.2; margin-bottom: 5px;}
.card-meta { font-size: 0.8rem; color: #46d369; font-weight: 600; }
.card-meta span { color: #a3a3a3; font-weight: 400; margin-left: 6px; }

/* Hero Banner */
.hero-banner {
    position: relative; width: 100%; height: 550px; background: #000;
    border-radius: 12px; overflow: hidden; margin-bottom: 40px;
    display: flex; align-items: flex-end; padding: 50px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.5);
    cursor: pointer;
}
.hero-bg-container {
    position: absolute; top: 0; left: 0; width: 100%; height: 100%; z-index: 1;
}
.hero-video-iframe {
    position: absolute; top: 0; left: 0; width: 100%; height: 100%;
    opacity: 0; transition: opacity 0.5s ease; pointer-events: none;
}
.hero-banner:hover .hero-video-iframe {
    opacity: 1; pointer-events: auto;
}
.hero-video-iframe iframe {
    pointer-events: none; /* Prevent accidental clicks inside the iframe */
}
.hero-banner:hover .hero-bg {
    opacity: 0;
}
.hero-bg {
    position: absolute; top: 0; left: 0; width: 100%; height: 100%;
    object-fit: cover; opacity: 0.6; transition: opacity 0.5s ease;
    mask-image: linear-gradient(to top, transparent 5%, black 60%);
    -webkit-mask-image: linear-gradient(to top, transparent 5%, black 60%);
}
.hero-content { position: relative; z-index: 2; max-width: 650px; }
.hero-title { font-size: 3.5rem; font-weight: 800; color: #fff; margin-bottom: 10px; line-height: 1.1; text-shadow: 0 2px 4px rgba(0,0,0,0.8); }
.hero-meta { font-size: 1.2rem; font-weight: 600; color: #46d369; margin-bottom: 15px; text-shadow: 0 2px 4px rgba(0,0,0,0.8); }
.hero-meta span { color: #ccc; font-weight: 400; margin-left: 10px; }
.hero-desc { font-size: 1.1rem; color: #fff; line-height: 1.5; text-shadow: 0 2px 4px rgba(0,0,0,0.8); }

</style>
""", unsafe_allow_html=True)

# ── Sidebar Navigation ──────────────────────────────────────────────
# ── Poster & Data Fetch (TMDB & OMDb) ───────────────────────────────
# ── Poster & Data Fetch (Multi-Key Rotation) ─────────────────────────
TMDB_KEYS = ["8265bd1679663a7ea12ac168da84d2e8", "c7e30514a303649520a06a6c4c5b161f", "f0e213322d7a221f7ec880907d47228a"]
OMDB_KEYS = ["a9118a3a", "60e945c7", "9d638708"]

# Global session and circuit breaker (Global to be thread-safe)
_SESSION = requests.Session()
TMDB_IS_BLOCKED = False 
API_KEY_IDX = 0

def get_current_tmdb_key():
    return TMDB_KEYS[API_KEY_IDX % len(TMDB_KEYS)]

def get_current_omdb_key():
    return OMDB_KEYS[API_KEY_IDX % len(OMDB_KEYS)]

@st.cache_data(show_spinner=False, ttl=604800)
def get_poster_url(movie_id, title, release_date) -> Optional[str]:
    global TMDB_IS_BLOCKED, API_KEY_IDX
    title_str = str(title)
    
    # 1. Try OMDb FIRST (since TMDB is blocked for the user)
    for _ in range(len(OMDB_KEYS)):
        key = OMDB_KEYS[API_KEY_IDX % len(OMDB_KEYS)]
        try:
            year = str(release_date)[:4] if release_date else ""
            url = f"https://www.omdbapi.com/?apikey={key}&t={urllib.parse.quote(title_str)}"
            if year: url += f"&y={year}"
            r = _SESSION.get(url, timeout=2.0)
            if r.status_code == 200:
                data = r.json()
                if data.get("Response") == "True":
                    poster = data.get("Poster")
                    if poster and poster != "N/A": 
                        return poster.replace("http://", "https://")
                elif "limit" in data.get("Error", "").lower():
                    API_KEY_IDX += 1
                    continue
            break
        except:
            break

    # 2. Try TMDB as secondary
    if not TMDB_IS_BLOCKED:
        for _ in range(len(TMDB_KEYS)):
            key = TMDB_KEYS[API_KEY_IDX % len(TMDB_KEYS)]
            try:
                if movie_id and str(movie_id) != "nan" and int(float(movie_id)) > 0:
                    mid = int(float(movie_id))
                    url = f"https://api.themoviedb.org/3/movie/{mid}?api_key={key}"
                    r = _SESSION.get(url, timeout=1.0)
                    if r.status_code == 200:
                        path = r.json().get("poster_path")
                        if path: return f"https://image.tmdb.org/t/p/w500{path}"
                
                s_url = f"https://api.themoviedb.org/3/search/movie?api_key={key}&query={urllib.parse.quote(title_str)}"
                r = _SESSION.get(s_url, timeout=1.0)
                if r.status_code == 200:
                    res = r.json().get("results", [])
                    if res and res[0].get("poster_path"):
                        return f"https://image.tmdb.org/t/p/w500{res[0].get('poster_path')}"
                break
            except:
                TMDB_IS_BLOCKED = True
                break
    
    return None

@st.cache_data(show_spinner=False, ttl=86400)
def fetch_omdb_data(title: str, year: str = "") -> dict:
    global API_KEY_IDX
    key = OMDB_KEYS[API_KEY_IDX % len(OMDB_KEYS)]
    url = f"https://www.omdbapi.com/?apikey={key}&t={urllib.parse.quote(str(title))}"
    if year: url += f"&y={year}"
    try:
        r = _SESSION.get(url, timeout=5)
        if r.status_code == 200:
            data = r.json()
            if data.get("Response") == "True": return data
    except: pass
    return {}

@st.cache_data(show_spinner=False, ttl=300)
def search_omdb(query: str) -> list:
    global API_KEY_IDX
    key = OMDB_KEYS[API_KEY_IDX % len(OMDB_KEYS)]
    url = f"https://www.omdbapi.com/?apikey={key}&s={urllib.parse.quote(str(query))}"
    try:
        r = _SESSION.get(url, timeout=5)
        if r.status_code == 200:
            data = r.json()
            if data.get("Response") == "True": return data.get("Search", [])
    except: pass
    return []

@st.cache_data(show_spinner=False, ttl=86400)
def get_trailer_id(movie_title: str) -> Optional[str]:
    try:
        # Try multiple search patterns for better reliability
        search_queries = [
            f"{movie_title} official trailer",
            f"{movie_title} movie trailer",
            f"{movie_title} trailer"
        ]
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        for sq in search_queries:
            try:
                query = urllib.parse.quote(sq)
                url = f"https://www.youtube.com/results?search_query={query}"
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=5) as response:
                    html = response.read().decode()
                    
                # Pattern 1: standard videoId in JSON
                video_ids = re.findall(r'"videoId":"([^"]+)"', html)
                if not video_ids:
                    # Pattern 2: watch?v= pattern
                    video_ids = re.findall(r'watch\?v=([a-zA-Z0-9_-]{11})', html)
                
                if video_ids:
                    # Return the first 11-char ID found
                    for vid in video_ids:
                        if len(vid) == 11: return vid
            except:
                continue
    except Exception as e:
        print(f"Trailer fetch error: {e}")
    return None

# ── Sidebar Navigation ──────────────────────────────────────────────
with st.sidebar:
    st.markdown("<h1 style='color:#e50914; font-family:Bebas Neue, sans-serif; font-size:2.5rem; margin-bottom:0;'>CINEMATCHFLIX</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:#46d369; font-weight:600; margin-top:0;'>AI-Powered Recommender</p>", unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("### 🎬 Navigation")
    
    # Navigation Buttons
    if st.button("🏠 Home Overview", use_container_width=True):
        st.session_state.view = "home"
        st.query_params.clear()
        st.rerun()
        
    if st.button("🎲 Random AI Pick", use_container_width=True):
        random_movie = movies.sample(n=1).iloc[0]["title"]
        st.session_state.view = "movie"
        st.query_params.movie = random_movie
        st.rerun()

    st.markdown("---")
    
    # ML Parameters Section
    st.markdown("### ⚙️ ML Parameters")
    st.markdown("<small style='color:#888;'>Filter recommendations by genres using Machine Learning classification.</small>", unsafe_allow_html=True)
    
    all_genres = ["All Movies"]
    if 'genres_display' in movies.columns:
        # Extract all unique genres
        unique_genres = sorted(list(set([g for sublist in movies['genres_display'].tolist() if isinstance(sublist, list) for g in sublist])))
        all_genres.extend(unique_genres)
    
    # Use index to persist selection
    current_genre_idx = all_genres.index(st.session_state.selected_genre) if st.session_state.selected_genre in all_genres else 0
    selected_genre = st.selectbox("Select a Genre", all_genres, index=current_genre_idx)
    
    if selected_genre != st.session_state.selected_genre:
        st.session_state.selected_genre = selected_genre
        st.session_state.view = "genre" if selected_genre != "All Movies" else "home"
        st.rerun()

    if st.session_state.view == "genre":
        if st.button("❌ Clear Genre Filter", use_container_width=True):
            st.session_state.view = "home"
            st.session_state.selected_genre = "All Movies"
            st.rerun()
    
    st.markdown("---")
    st.markdown("### 📈 App Stats")
    st.info(f"Total Movies: {len(movies)}")
    
    st.markdown("---")
    st.markdown("### 🌟 Popular Picks")
    
    # Show 3 random posters in sidebar for visual flair
    sidebar_samples = movies.sample(3)
    for idx, row in sidebar_samples.iterrows():
        poster = get_poster_url(row.get("movie_id"), row["title"], row.get("release_date"))
        if poster:
            st.image(poster, use_container_width=True, caption=row["title"])
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("<small style='color:#555;'>© 2026 CineMatch Flix AI<br>Powered by TMDB & OMDb</small>", unsafe_allow_html=True)

# ── Logic Functions ────────────────────────────────────────

def build_results(df_slice):
    results = []
    rows = []
    for _, row in df_slice.iterrows():
        rows.append({
            "id": row.get("movie_id"),
            "title": row["title"],
            "date": row.get("release_date"),
            "vote": row.get("vote_average", 0),
            "gen": row.get("genres_display", [])[:2]
        })
    
    # Parallel fetch with generous timeout
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_movie = {executor.submit(get_poster_url, r["id"], r["title"], r["date"]): r for r in rows}
        for future in as_completed(future_to_movie):
            r = future_to_movie[future]
            try:
                poster = future.result(timeout=5) # Increased to 5s for reliability
            except:
                poster = None
            
            results.append({
                "title": r["title"],
                "movie_id": r["id"],
                "year": str(r["date"])[:4] if r["date"] else "",
                "rating": r["vote"],
                "genres": r["gen"],
                "poster": poster,
            })
    return results

@st.cache_data(show_spinner=False, ttl=3600)
def recommend(title: str, n: int = 10):
    if title in movies["title"].values:
        idx = movies[movies["title"] == title].index[0]
        distances = sorted(enumerate(similarity[idx]), key=lambda x: x[1], reverse=True)[1:n+1]
        df_slice = movies.iloc[[i for i, _ in distances]]
        return build_results(df_slice)
    return get_trending(n)

@st.cache_data(show_spinner=False, ttl=3600)
def get_trending(n=10):
    return build_results(movies.sample(n=min(n, len(movies)), random_state=42))

@st.cache_data(show_spinner=False, ttl=3600)
def get_movies_by_genre(genre, n=15):
    if not genre or genre == "All Movies":
        return get_trending(n)
    
    # Robust genre filtering
    def matches_genre(g_list):
        if not isinstance(g_list, list): return False
        return any(genre.lower() in g.lower() for g in g_list)
        
    df = movies[movies['genres_display'].apply(matches_genre)]
    
    if df.empty:
        # Fallback to fuzzy search in strings if list matching fails
        df = movies[movies['genres'].str.contains(genre, case=False, na=False)]
        
    if df.empty: 
        return get_trending(n)
        
    return build_results(df.sample(n=min(n, len(df)), random_state=random.randint(1, 1000)))

# ── HTML Generators ────────────────────────────────────────
def generate_html_row(movie_list):
    html = '<div class="scrolling-wrapper">'
    for m in movie_list:
        encoded_title = urllib.parse.quote(m["title"])
        link = f"/?movie={encoded_title}"
        
        genres_str = " · ".join(m["genres"])
        if m["poster"]:
            img_html = f'<img src="{m["poster"]}" alt="{m["title"]}" loading="lazy">'
        else:
            img_html = f'<div class="card-ph">{m["title"]}</div>'
            
        html += f"""<a href="{link}" target="_self" style="text-decoration: none;">
<div class="card-container">
{img_html}
<div class="card-overlay">
<div class="card-title">{m["title"]}</div>
<div class="card-meta">⭐ {m["rating"]} <span>{m["year"]}</span></div>
</div>
</div>
</a>"""
    html += '</div>'
    return html

import streamlit.components.v1 as components

def render_hero_banner(movie_name):
    # Fetch Data
    with st.spinner(f"Preparing {movie_name}..."):
        omdb_data = fetch_omdb_data(movie_name)
        trailer_id = get_trailer_id(movie_name)
        
    if omdb_data.get("Response") == "True":
        sel_year, sel_rating = omdb_data.get("Year", ""), omdb_data.get("imdbRating", "N/A")
        sel_genres, sel_overview = omdb_data.get("Genre", "").replace(",", " ·"), omdb_data.get("Plot", "")
        sel_dir, sel_cast = omdb_data.get("Director", ""), omdb_data.get("Actors", "")
        poster_url = omdb_data.get("Poster", "").replace("http://", "https://") if omdb_data.get("Poster") != "N/A" else ""
    else:
        sel_year, sel_rating, sel_genres, sel_overview, poster_url = "", "N/A", "", "Details not available.", ""
        sel_dir, sel_cast = "Unknown", "Unknown"
        if movie_name in movies["title"].values:
            row = movies[movies["title"] == movie_name].iloc[0]
            poster_url = get_poster_url(row.get("movie_id"), row["title"], row.get("release_date"))

    search_terms = urllib.parse.quote(f"watch {movie_name} online where to stream netflix prime hulu disney")
    watch_link = f"https://www.google.com/search?q={search_terms}"
    
    # Use isolated component for 100% reliable JS and audio
    banner_html = f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800&display=swap');
        * {{ box-sizing: border-box; font-family: 'Inter', sans-serif; }}
        body {{ margin: 0; padding: 0; background: transparent; overflow: hidden; }}
        
        .hero-banner {{
            position: relative; width: 100%; height: 530px; background: #000;
            border-radius: 12px; overflow: hidden;
            display: flex; align-items: flex-end; padding: 40px;
            cursor: pointer;
        }}
        .hero-bg {{
            position: absolute; top: 0; left: 0; width: 100%; height: 100%;
            object-fit: cover; opacity: 0.6; transition: opacity 0.6s ease;
            mask-image: linear-gradient(to top, transparent 5%, black 60%);
            -webkit-mask-image: linear-gradient(to top, transparent 5%, black 60%);
            z-index: 1;
        }}
        .video-container {{
            position: absolute; top: 0; left: 0; width: 100%; height: 100%;
            opacity: 0; transition: opacity 0.6s ease; z-index: 2; pointer-events: none;
        }}
        .hero-content {{ position: relative; z-index: 10; max-width: 650px; color: #fff; }}
        .hero-title {{ font-size: 3rem; font-weight: 800; margin-bottom: 8px; line-height: 1.1; text-shadow: 0 2px 4px rgba(0,0,0,0.8); }}
        .hero-meta {{ font-size: 1.1rem; font-weight: 600; color: #46d369; margin-bottom: 12px; }}
        .hero-meta span {{ color: #ccc; font-weight: 400; margin-left: 10px; }}
        .hero-desc {{ font-size: 1rem; line-height: 1.4; text-shadow: 0 2px 4px rgba(0,0,0,0.8); opacity: 0.9; }}
        .watch-btn {{
            margin-top:20px; background:#e50914; color:#fff; border:none; 
            padding:12px 30px; font-weight:bold; border-radius:4px; cursor:pointer;
            font-size: 1rem; transition: background 0.3s;
        }}
        .watch-btn:hover {{ background: #b20710; }}
        .sound-tip {{
            position: absolute; top: 20px; right: 20px; z-index: 20;
            background: rgba(0,0,0,0.6); color: #fff; padding: 5px 12px;
            border-radius: 20px; font-size: 0.8rem; opacity: 0; transition: opacity 0.3s;
        }}
        .hero-banner:hover .sound-tip {{ opacity: 1; }}
    </style>

    <div class="hero-banner" id="banner">
        <img class="hero-bg" src="{poster_url}" id="bg-img">
        <div class="video-container" id="video-div">
            <iframe id="player" width="100%" height="100%" frameborder="0" 
                allow="autoplay; encrypted-media" src=""></iframe>
        </div>
        <div class="sound-tip">🔈 Click banner once for sound</div>
        <div class="hero-content">
            <div class="hero-title">{movie_name}</div>
            <div class="hero-meta">{sel_rating} Match <span>{sel_year}</span> <span>{sel_genres}</span></div>
            <div class="hero-desc">{sel_overview}</div>
            <button class="watch-btn" onclick="window.open('{watch_link}', '_top')">▶ Watch Now</button>
        </div>
    </div>

    <script>
        var banner = document.getElementById('banner');
        var player = document.getElementById('player');
        var videoDiv = document.getElementById('video-div');
        var bgImg = document.getElementById('bg-img');
        var videoId = "{trailer_id}";
        var videoSrc = "https://www.youtube.com/embed/" + videoId + "?autoplay=1&mute=0&controls=0&loop=1&playlist=" + videoId + "&rel=0";

        if (videoId) {{
            banner.onmouseenter = function() {{
                player.src = videoSrc;
                videoDiv.style.opacity = "1";
                bgImg.style.opacity = "0.2";
            }};
            banner.onmouseleave = function() {{
                player.src = "";
                videoDiv.style.opacity = "0";
                bgImg.style.opacity = "0.6";
            }};
        }}
    </script>
    """
    
    components.html(banner_html, height=530)

# ═══════════════════════════════════════════════════════════
#  UI MAIN
# ═══════════════════════════════════════════════════════════

# Navbar
st.markdown('<div class="navbar"><div class="nav-logo">CINEMATCHFLIX</div></div>', unsafe_allow_html=True)

# Safe query params
try:
    url_movie = st.query_params.get("movie", "")
except:
    url_movie = ""

# ── SMART AUTOCOMPLETE SEARCH ──
search_query = st.text_input("🔍 Search for a movie, show, etc.", value="", placeholder="e.g. Inception, Batman, Avatar...")

selected_movie = None

# If user typed something in search, show Netflix-style visual rows instead of buttons!
if search_query:
    omdb_results = search_omdb(search_query)
    
    if len(omdb_results) > 0:
        st.markdown(f'<div class="row-header">Search Results for "{search_query}"</div>', unsafe_allow_html=True)
        results = []
        for item in omdb_results[:15]:
            results.append({
                "title": item.get("Title", "Unknown"),
                "year": item.get("Year", ""),
                "rating": "N/A",
                "genres": [],
                "poster": item.get("Poster") if item.get("Poster") != "N/A" else None
            })
        st.markdown(generate_html_row(results), unsafe_allow_html=True)
    else:
        # Fallback to local
        matches = movies[movies['title'].str.contains(search_query, case=False, na=False)]
        if len(matches) > 0:
            st.markdown(f'<div class="row-header">Search Results for "{search_query}"</div>', unsafe_allow_html=True)
            results = []
            for idx, row in matches.head(15).iterrows():
                results.append({
                    "title": row["title"],
                    "year": str(row.get("release_date", ""))[:4],
                    "rating": round(float(row.get("vote_average", 0)), 1),
                    "genres": row.get("genres_display", [])[:2] if 'genres_display' in movies.columns else [],
                    "poster": get_poster_url(row.get("movie_id"), row["title"], row.get("release_date"))
                })
            st.markdown(generate_html_row(results), unsafe_allow_html=True)
        else:
            st.markdown("<div style='color: #888; font-size:0.9rem;'>No matches found.</div>", unsafe_allow_html=True)

# If no movie selected via search, check if URL param has a movie
if not selected_movie and url_movie:
    selected_movie = url_movie

# ── Main UI Logic ──────────────────────────────────────────────────
if selected_movie:
    render_hero_banner(selected_movie)
    st.markdown(f'<div class="row-header">Because you liked {selected_movie}</div>', unsafe_allow_html=True)
    st.markdown(generate_html_row(recommend(selected_movie)), unsafe_allow_html=True)

elif st.session_state.view == "genre":
    st.markdown(f'<div class="row-header">{st.session_state.selected_genre} Collection</div>', unsafe_allow_html=True)
    st.markdown(generate_html_row(get_movies_by_genre(st.session_state.selected_genre)), unsafe_allow_html=True)
    st.markdown('<div class="row-header">Popular Trending</div>', unsafe_allow_html=True)
    st.markdown(generate_html_row(get_trending()), unsafe_allow_html=True)

else:
    # Home Page - Featured Hero Banner
    trending_movies = movies.sample(1) # Get a featured movie
    if not trending_movies.empty:
        featured_movie = trending_movies.iloc[0]["title"]
        render_hero_banner(featured_movie)

    st.markdown('<div class="row-header" style="margin-top:20px;">🔥 Trending Now</div>', unsafe_allow_html=True)
    st.markdown(generate_html_row(get_trending()), unsafe_allow_html=True)
    
    st.markdown('<div class="row-header">💥 Action Hits</div>', unsafe_allow_html=True)
    st.markdown(generate_html_row(get_movies_by_genre("Action")), unsafe_allow_html=True)

    st.markdown('<div class="row-header">🛸 Sci-Fi Adventures</div>', unsafe_allow_html=True)
    st.markdown(generate_html_row(get_movies_by_genre("Science Fiction")), unsafe_allow_html=True)

    st.markdown('<div class="row-header">🎭 Drama & Emotions</div>', unsafe_allow_html=True)
    st.markdown(generate_html_row(get_movies_by_genre("Drama")), unsafe_allow_html=True)

st.markdown("<br><br><br>", unsafe_allow_html=True)
