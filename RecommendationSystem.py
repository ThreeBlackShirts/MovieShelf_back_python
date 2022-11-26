from email.quoprimime import unquote
from urllib.parse import unquote_plus
import cx_Oracle

cx_Oracle.init_oracle_client(lib_dir=r"Instant Client 경로") 
# 본인이 Instant Client 넣어놓은 경로를 입력해준다

connection = cx_Oracle.connect(user='DB 사용자이름', password='비밀번호', dsn='dsn')
# 본인이 접속할 오라클 클라우드 DB 사용자이름, 비밀번호, dsn을 넣어준다.

from flask import Flask, request
from flask_restx import Api, Resource, reqparse  #swagger
import pandas as pd 
import numpy as np 
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity 

app = Flask(__name__)

api = Api(app, version='1.0', title='API_python', description='Swagger 문서', doc="/api-docs")

movie_api = api.namespace('movie', description='추천 시스템')

@movie_api.route('/recommend/<string:target>', methods=['POST'])
class Movie(Resource): 
    def post(self, target):
        """특정 영화와 비슷한 장르의 영화 리스트를 가져옵니다."""

        cursor = connection.cursor()

        movies = "SELECT movie_title, movie_poster, movie_genres FROM movies ORDER BY movie_rate"
        cursor.execute(movies)
        all_movies = cursor.fetchall()
        movies = pd.DataFrame(all_movies, columns=['movie_title', 'movie_poster', 'movie_genres']) 

        movies["genres_literal"] = movies["movie_genres"].apply(lambda x : x.replace(',',''))

        count_vect = CountVectorizer(min_df=0, ngram_range=(1,2))
        genre_mat = count_vect.fit_transform(movies['genres_literal'])
        genre_sim = cosine_similarity(genre_mat, genre_mat)
        genre_sim_sorted_ind = genre_sim.argsort()[:, ::-1]
        
        title_movie = movies[movies['movie_title'] == target] 
        title_index = title_movie.index.values 

        similar_indexes = genre_sim_sorted_ind[title_index, :(16)] 
        
        similar_indexes = similar_indexes.reshape(-1) 

        similar_indexes = similar_indexes[similar_indexes!=title_index]
        
        similar_movies = movies.iloc[similar_indexes] 
        movies_recommend = similar_movies[['movie_poster']]
        movies_recommend_json = movies_recommend.to_json(orient = 'records', force_ascii=False)

        return movies_recommend_json

if __name__ == '__main__': 
    app.run()
