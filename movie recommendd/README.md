# 🍿 CineMatchFlix: AI-Powered Movie Recommender

CineMatchFlix is a premium, Netflix-inspired movie recommendation platform built with **Python**, **Streamlit**, and **Machine Learning**. It features an immersive UI with background trailers, auto-voice on hover, and personalized recommendations using Cosine Similarity.

## 🌟 Key Features
- **Netflix UI/UX**: Immersive dark mode design with horizontal scrolling carousels.
- **Smart Search**: Real-time movie search powered by TMDB and OMDb APIs.
- **Interactive Trailers**: Auto-playing background trailers with voice control on hover.
- **AI Recommendation Engine**: Uses Natural Language Processing (NLP) and Cosine Similarity to suggest movies based on your interests.
- **Genre Filtering**: Browse movies by specific genres using ML-based classification.

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- Git LFS (for large model files)

### Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/YOUR_USERNAME/movie-recommendation-system.git
   cd movie-recommendation-system
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   streamlit run app.py
   ```

## 🛠️ Tech Stack
- **Frontend**: Streamlit, HTML5, CSS3, JavaScript
- **Backend**: Python
- **Machine Learning**: Scikit-learn (Cosine Similarity), Pandas, Pickle
- **APIs**: TMDB API, OMDb API, YouTube IFrame API

## 📂 Project Structure
- `app.py`: Main application logic and UI.
- `similarity.pkl`: Pre-computed similarity matrix for AI recommendations.
- `movie_dict.pkl`: Processed movie database.
- `generate_models.py`: Script to generate the ML models.

## 📝 License
This project is for portfolio purposes. Data provided by TMDB and OMDb.

---
Developed with ❤️ by [Your Name]
