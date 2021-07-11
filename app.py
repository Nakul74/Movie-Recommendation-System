import pandas as pd
import numpy as np
from flask import Flask
from pywebio.output import put_table,put_image,put_link,put_markdown,put_text
from pywebio.input import input,TEXT,NUMBER,FLOAT,select,input_group
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from youtubesearchpython import VideosSearch
import json, requests
from pywebio.platform.flask import webio_view
from pywebio import start_server
import argparse

api_key = 'ae425b92085fb0baed654d771acaed36'
app = Flask(__name__)

def metascore(mylist,df,vect):
    name=[]
    vectorizer = CountVectorizer(lowercase = False)
    for i in mylist:
        if i == 'genre':
            vectorizer = CountVectorizer(lowercase = False,ngram_range=(1,3))
        data_vect = vectorizer.fit_transform(df[i].fillna('None'))
        vect1 = vectorizer.transform(vect[i])
        sim_score = cosine_similarity(data_vect,vect1)
        name.append('sim_score_'+i)
        df['sim_score_'+i] = sim_score
    return name, df

def string_match(name, th = 0.8):
    name = np.array(name)
    vectorizer = CountVectorizer(lowercase = False)
    i = 0
    while(1):
        s1 = name[[i]]
        s2 = name[i+1:]
        try:
            vec1 = vectorizer.fit_transform(s1)
        except:
            i+=1
            continue
        vec2 = vectorizer.transform(s2)
        sim_score = list(enumerate(cosine_similarity(vec1,vec2).ravel(),start=i+1))
        idx = []
        for j in sim_score:
            if j[1]>th:
                idx.append(j[0])
        if idx:
            name = np.delete(name,idx)
            
        i+=1
        if (len(name)-1)<=i:
            break
            
    return name.tolist()

def movie_posters(names):
    posters = {}
    for i in names:
        s = i.replace(' ','%20')
        url = 'https://api.themoviedb.org/3/search/'+'movie'+'?api_key='+api_key+'&language=en-US&query=%27'+s+'%27&page=1&include_adult=false'
        response = requests.get(url)
        val = json.loads(response.text)
        try:
            posters[val['results'][0]['title'] + '(' + val['results'][0]['release_date'][:4] + ')'] = 'https://image.tmdb.org/t/p/w185/' + val['results'][0]['poster_path']
        except:
            pass
        if len(posters) == 10:
            break
        
    return posters

def trending_movies():
    url='https://api.themoviedb.org/3/movie/popular?api_key='+api_key+'&language=en-US&page=1'
    response = requests.get(url)
    val = json.loads(response.text)
    
    trending = {}
    for i in range(len(val['results'])):
        trending[val['results'][i]['original_title'] + '(' + val['results'][i]['release_date'][:4] + ')'] = 'https://image.tmdb.org/t/p/w185/' + val['results'][i]['poster_path']
        if i == 9:
            break
    return trending

def tmdb_recommendation(idx,s,e):
    tmdb = []
    
    for j in range(5):
        url='https://api.themoviedb.org/3/movie/'+str(idx)+'/recommendations?api_key='+api_key+'&language=en-US&page='+str(j+1)
        response = requests.get(url)
        val = json.loads(response.text)
        if not val['results']:
            break
        for i in range(len(val['results'])):
            if (int(val['results'][i]['release_date'][:4]) >= s) and (int(val['results'][i]['release_date'][:4]) <= e):
                tmdb.append(val['results'][i]['original_title'])
            if len(tmdb) == 20:
                return tmdb      

def get_cast_dict(df,name,n):
    d = {}
    for i in range(n):
        if df['profile_path'].values[i]:
            profile_path = 'https://image.tmdb.org/t/p/w185/' + df['profile_path'].values[i]
        else:
            profile_path = 'https://www.canadaid.ca/wp-content/uploads/2019/02/no-image-available-180x300.jpg'
        d[df[name].values[i]] = profile_path
        if i == (df.shape[0]-1):
            break 
    return d

def movies_cast(idx):
    url='https://api.themoviedb.org/3/movie/'+str(idx)+'/credits?api_key='+api_key+'&language=en-US'
    response = requests.get(url)
    val = json.loads(response.text) 
    gender = {1:'Female',2:'Male'}
    
    a = {}
    idx = []
    cast = pd.DataFrame(val['cast'])
    cast['character_name'] = cast['original_name'] + ' as ' + cast['character']
    cast = cast[cast['known_for_department']=='Acting']
    cast_dict = get_cast_dict(cast,'character_name',8)
    if cast['profile_path'].values[0]:
        profile_path = 'https://image.tmdb.org/t/p/w185/' + cast['profile_path'].values[0]
    else:
        profile_path = 'https://www.canadaid.ca/wp-content/uploads/2019/02/no-image-available-180x300.jpg'
    a['profile_path'] = profile_path
    a['name'] = ['Original_name : ' + '\'' + cast['original_name'].values[0] + '\'']
    a['gender'] = ['Gender : ' + gender[cast['gender'].values[0]]]
    a['department'] = ['Department : ' + cast['known_for_department'].values[0]]
    a['pop'] = ['Popularity : ' + str(cast['popularity'].values[0])]
    idx.append(cast['id'].values[0])
    
    d = {}
    cast = pd.DataFrame(val['crew'])
    directors = cast[cast['department']=='Directing']
    directors_dict = get_cast_dict(directors,'original_name',4)
    if directors['profile_path'].values[0]:
        profile_path = 'https://image.tmdb.org/t/p/w185/' + directors['profile_path'].values[0]
    else:
        profile_path = 'https://www.canadaid.ca/wp-content/uploads/2019/02/no-image-available-180x300.jpg'
    d['profile_path'] = profile_path
    d['name'] = ['Original_name : ' + '\'' + directors['original_name'].values[0] + '\'']
    d['gender'] = ['Gender : ' + gender[directors['gender'].values[0]]]
    d['department'] = ['Department : ' + directors['known_for_department'].values[0]]
    d['pop'] = ['Popularity : ' + str(directors['popularity'].values[0])]
    idx.append(directors['id'].values[0])
    
    w = {}
    writers = cast[cast['department']=='Writing']
    writers_dict = get_cast_dict(writers,'original_name',4)
    if writers['profile_path'].values[0]:
        profile_path = 'https://image.tmdb.org/t/p/w185/' + writers['profile_path'].values[0]
    else:
        profile_path = 'https://www.canadaid.ca/wp-content/uploads/2019/02/no-image-available-180x300.jpg'
    w['profile_path'] = profile_path
    w['name'] = ['Original_name : ' + '\'' + writers['original_name'].values[0] + '\'']
    w['gender'] = ['Gender : ' + gender[writers['gender'].values[0]]]
    w['department'] = ['Department : ' + writers['known_for_department'].values[0]]
    w['pop'] = ['Popularity : ' + str(writers['popularity'].values[0])]
    idx.append(writers['id'].values[0])
    
    return cast_dict,directors_dict,writers_dict,a,d,w,idx

def top_cast_details(idx,movie_name):
    url = 'https://api.themoviedb.org/3/person/'+str(idx)+'/movie_credits?api_key='+api_key+'&language=en-US'
    response = requests.get(url)
    val = json.loads(response.text)
    temp = pd.DataFrame(val['cast'])
    try:
        temp.sort_values(by = 'popularity',ascending=False,inplace=True,ignore_index=True)
        data = {}
        name = {}

        for i in range(30):
            if (temp['original_title'][i] == movie_name):
                continue
            title = temp['original_title'][i] + '(' + temp['release_date'][i][:4] + ')'
            if temp['poster_path'][i]:
                poster_path = 'https://image.tmdb.org/t/p/w185/' + temp['poster_path'][i]
            else:
                poster_path = 'https://www.canadaid.ca/wp-content/uploads/2019/02/no-image-available-180x300.jpg'
            data[title] = poster_path
            name[temp['original_title'][i]] = title

            if i == (temp.shape[0]-1):
                break

        s = list(name.keys())   
        s = string_match(s, th = 0.8)

        d = {}
        for i in name.keys():
            if i in s:
                d[name[i]] = data[name[i]]
            if len(d) >= 8:
                break

        return d
    except:
        return {}

def similarity(movie, mylist = ['genre','full_cast'], weight='balanced', pop = 5, start_year = 2000, end_year = 2020, min_rating = 5.0, Total_votes = 100000):
    data = {}
    df = pd.read_csv(r'movies_data3.csv') 
    s = movie.replace(' ','%20')
    url = 'https://api.themoviedb.org/3/search/'+'movie'+'?api_key='+api_key+'&language=en-US&query=%27'+s+'%27&page=1&include_adult=false'
    response = requests.get(url)
    val = json.loads(response.text)
    if not val['results']:
        return [],[],[]
    data['id'] = val['results'][0]['id']
    if val['results'][0]['poster_path']:
        data['poster'] = 'https://image.tmdb.org/t/p/w185/' + val['results'][0]['poster_path']
    else:
        data['poster'] = 'https://upload.wikimedia.org/wikipedia/commons/1/16/No_image_available_450_x_600.svg'
    data['name'] = ['Name : ' + '\'' + val['results'][0]['title'] + '\'']
    movie_name = val['results'][0]['title']
    data['language'] = ['Language : ' + val['results'][0]['original_language']]
    data['release_date'] = ['Release Date : ' + val['results'][0]['release_date']]
    data['ratings'] = ['Ratings : ' + str(val['results'][0]['vote_average']) + ' (' + str(val['results'][0]['vote_count']) + ')']
    data['overview'] = [val['results'][0]['overview']]
    trailer_search = val['results'][0]['title'] + ' ' + val['results'][0]['release_date'][:4] + ' official' + ' trailer'
    videosSearch = VideosSearch(trailer_search, limit = 1)
    result = videosSearch.result()
    data['trailer_link'] = result['result'][0]['link']
    url = 'https://api.themoviedb.org/3/movie/'+str(data['id'])+'?api_key='+api_key+'&language=en-US'
    response = requests.get(url)
    val2 = json.loads(response.text)
    genres = []
    for i in range(len(val2['genres'])):
        genres.append(val2['genres'][i]['name'])
        
    data['genres'] = ['Genres : ' + ', '.join(genres)]
    data['imdb_id'] = val2['imdb_id']
    data['duration'] = ['Duration : ' + str(val2['runtime']) + ' minutes']
    data['tagline'] = ['Tagline : ' + val2['tagline']]
      
    vect = df.loc[df['imdb_title_id'] == str(data['imdb_id'])]
    if vect.empty:
        name = tmdb_recommendation(data['id'], start_year, end_year)
    else:
        min_rating = (min_rating/10.0)
        Total_votes = (Total_votes/2278845.0)
        df = df[((df.year >= start_year) & (df.year <= end_year)) & (df.votes >= Total_votes) & (df.avg_vote >= min_rating)]
        if df.empty:
            name = []
        else:
            name,df = metascore(mylist,df,vect)
            if (weight == 'balanced') | (len(mylist) == 1):
                weights=[(1.0 / len(mylist))] * len(mylist)
            else:
                s = sum(weight)
                weights = [i/s for i in weight]
            df['metascore2'] = 0.0
            for i in range(len(name)):
                df['metascore2'] = df['metascore2'] + df[name[i]]*weights[i]
            my_weight=(pop / 10.0)
            df['metascore'] = df['metascore1']*my_weight + df['metascore2']*(1.0-my_weight)
            sorted_data = df.sort_values(by = ['metascore'], ascending=False)
            name = sorted_data.iloc[:31,[1]].values.ravel().tolist() 
            if val['results'][0]['title'].lower() in name:
                name.remove(val['results'][0]['title'].lower())
    if name: 
        name = string_match(name,th=0.8)
        name = movie_posters(name)

    return data,name,movie_name

def print_image(name,path):
    if name:
        if len(name) == 1:
            put_table([[put_image(path[0])]],header = name[:1])

        elif len(name) == 2:
            put_table([[put_image(path[0]),
                        put_image(path[1])]],header = name[:2])

        elif len(name) == 3:
            put_table([[put_image(path[0]),
                        put_image(path[1]),
                        put_image(path[2])]],header = name[:3])

        elif len(name) == 4:
            put_table([[put_image(path[0]),
                        put_image(path[1]),
                        put_image(path[2]),
                        put_image(path[3])]],header = name[:4])
        else:
            put_table([[put_image(path[0]),
                        put_image(path[1]),
                        put_image(path[2]),
                        put_image(path[3]),
                        put_image(path[4])]],header = name[:5])


def recommend_movies():
    recommend_type = ['genre' ,'genre + original_title', 'genre + full_cast', 'genre + description']
    
    movie = input_group("Movie Recommendation System",[
            input('Enter the name of the movie',placeholder = "(eg: Iron man)", type = TEXT, name = 'movie_name'),
            input('Start year of movies to recommend',placeholder = "(eg: 2000)", name='start_date', type = NUMBER),
            input('End year of movies to recommend',placeholder = "(eg: 2021)", name='end_date', type = NUMBER),
            input('Enter popularity score of movies to recommend',placeholder = 'Number between 0 to 1 (weightage) eg: 0.3', name='pop_score', type = FLOAT),
            input('Enter minimum ratings of movies to recommend',placeholder = 'Number between 0 to 10 (min rating) eg: 5.0', name='min_rating', type = FLOAT),
            input('Enter minimum number of votes for movies to recommend (eg:100000)', name='votes', type = NUMBER),
            select("Select the type of recommendation：",recommend_type,name='type')
            ])
    
    start_date = movie['start_date']
    end_date = movie['end_date']
    popularity = movie['pop_score']
    rating = movie['min_rating']
    no_votes = movie['votes']
    mylist = movie['type'].split(' + ')
    myweight = 'balanced'
    movie_name = movie['movie_name']
    
    data,name,movie_name = similarity(movie_name, mylist, myweight, popularity, start_date, end_date, rating, no_votes)

    if not data:
        put_markdown(r""" ### No movies to recommend check the movie name entered""")
    else:
        temp = []
        for i in ['name','genres','language','release_date','ratings','duration','tagline']:
            temp.append(data[i])

        put_table([[put_table([[put_image(data['poster']),put_table(temp)]],header = ['Movie Poster','Details'])] , 
                   [put_link(name = 'Click here to view trailer',url = data['trailer_link'])],
                   [put_table([data['overview']],header=['Overview'])] ])
        
        cast_dict, directors_dict, writers_dict, a, d, w, idx = movies_cast(data['id'])
        del data
        
        if cast_dict:
            put_markdown(r""" # Top cast from the movie :""")
            names = list(cast_dict.keys())
            path = list(cast_dict.values())
            print_image(names[:4],path[:4])
            print_image(names[4:],path[4:])
            del cast_dict
            
        if directors_dict:
            put_markdown(r""" # Directors of the movie :""")
            names = list(directors_dict.keys())
            path = list(directors_dict.values())
            print_image(names,path)
            del directors_dict
            
        if writers_dict:
            put_markdown(r""" # Writers of the movie :""")
            names = list(writers_dict.keys())
            path = list(writers_dict.values())
            print_image(names,path)
            del writers_dict
        
        actor = top_cast_details(idx[0],movie_name)
        if actor:
            put_markdown(r""" # Top movies of the lead({}) :""".format(a['name'][0].split(' : ')[1]))
            temp = list(a.values())[1:]
            put_table([[put_image(a['profile_path']),put_table(temp)]],header = ['Actor Poster','Details'])
            names = list(actor.keys())
            path = list(actor.values())
            print_image(names[:4],path[:4])
            print_image(names[4:],path[4:])
            del actor
        
        director = top_cast_details(idx[1],movie_name)
        if director:
            if idx[1] == idx[2]:
                put_markdown(r""" # Top movies of the director and writer({}) :""".format(d['name'][0].split(' : ')[1]))
            else:   
                put_markdown(r""" # Top movies of the director({}) :""".format(d['name'][0].split(' : ')[1]))
            temp = list(d.values())[1:]
            put_table([[put_image(d['profile_path']),put_table(temp)]],header = ['Director Poster','Details'])
            names = list(director.keys())
            path = list(director.values())
            print_image(names[:4],path[:4])
            print_image(names[4:],path[4:])
            del director
         
        if idx[1] != idx[2]:
            writer = top_cast_details(idx[2],movie_name) 
            
            if writer:
                put_markdown(r""" # Top movies of the writer({}) :""".format(w['name'][0].split(' : ')[1]))
                temp = list(w.values())[1:]
                put_table([[put_image(w['profile_path']),put_table(temp)]],header = ['Writer Poster','Details'])
                names = list(writer.keys())
                path = list(writer.values())
                print_image(names[:4],path[:4])
                print_image(names[4:],path[4:])
                del writer

        if not name:
            put_markdown(r""" ### No movies to recommend try again with different parameters""")
        else:
            s = 'for movie \'' + movie_name + '\''
            put_markdown(r""" # Recommended Movies({}) :""".format(s))
            names = list(name.keys())
            path = list(name.values())
            print_image(names[:5],path[:5])
            print_image(names[5:],path[5:])
            
        put_markdown(r""" # Trending Movies :""")
        name = trending_movies()
        names = list(name.keys())
        path = list(name.values())
        print_image(names[:5],path[:5])
        print_image(names[5:],path[5:])
        
        put_markdown(r""" ### Created by Nakul Chamariya """)
        put_link(name = 'Github Code Link', url = 'https://github.com/Nakul74/Movie-Recommendation-System')
        put_markdown(r""" #### Contact details : """)
        put_text('Email id : nakulchamariya74@gmail.com')
        put_text('LinkedIn link : www.linkedin.com/in/nakul-chamariya')

app.add_url_rule('/tool', 'webio_view', webio_view(recommend_movies), methods=['GET', 'POST', 'OPTIONS'])

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--port", type=int, default=8080)
    args = parser.parse_args()

    start_server(recommend_movies, port=args.port)