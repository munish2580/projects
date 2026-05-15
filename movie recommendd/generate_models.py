import pandas as pd
import ast
import warnings
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import nltk
from nltk.stem.porter import PorterStemmer
import pickle
import os

warnings.filterwarnings("ignore")

print("Loading datasets...")
mv = pd.read_csv("tmdb_5000_movies.csv")
cr = pd.read_csv("tmdb_5000_credits.csv")

print("Merging and cleaning data...")
mv = mv.merge(cr, on="title")
mv = mv[['movie_id', 'title', 'overview', 'genres', 'keywords', 'cast', 'crew']]
mv.dropna(inplace=True)

def convert(a):
    ls = []
    for i in ast.literal_eval(a):
        ls.append(i["name"])
    return ls

def convert2(a):
    n = 0
    ls = []
    for i in ast.literal_eval(a):
        if n != 3:
            ls.append(i["name"])
            n += 1
        else:
            break
    return ls

def convert3(a):
    ls = []
    for i in ast.literal_eval(a):
        if i['job'] == "Director":
            ls.append(i["name"])
    return ls

mv["genres"] = mv["genres"].apply(convert)
mv["keywords"] = mv["keywords"].apply(convert)
mv["cast"] = mv["cast"].apply(convert2)
mv["crew"] = mv["crew"].apply(convert3)

mv["overview"] = mv["overview"].apply(lambda x: x.split())

mv["genres"] = mv["genres"].apply(lambda x: [i.replace(" ", "") for i in x])
mv["keywords"] = mv["keywords"].apply(lambda x: [i.replace(" ", "") for i in x])
mv["crew"] = mv["crew"].apply(lambda x: [i.replace(" ", "") for i in x])
mv["cast"] = mv["cast"].apply(lambda x: [i.replace(" ", "") for i in x])

mv["tags"] = mv["overview"] + mv["genres"] + mv["keywords"] + mv["crew"] + mv["cast"]

newdf = mv[['movie_id', 'title', 'tags']]
newdf["tags"] = newdf["tags"].apply(lambda x: " ".join(x))
newdf["tags"] = newdf["tags"].apply(lambda x: x.lower())

print("Applying stemming...")
ps = PorterStemmer()

def stem(a):
    ls = []
    for i in a.split():
        ls.append(ps.stem(i))
    return " ".join(ls)

newdf['tags'] = newdf['tags'].apply(stem)

print("Vectorizing and computing similarity...")
cv = CountVectorizer(max_features=5000, stop_words="english")
vectors = cv.fit_transform(newdf["tags"]).toarray()

similarity = cosine_similarity(vectors)

print("Saving models to pickle files...")
pickle.dump(newdf.to_dict(), open('movie_dict.pkl', 'wb'))
pickle.dump(similarity, open('similarity.pkl', 'wb'))

print("Models generated successfully!")
