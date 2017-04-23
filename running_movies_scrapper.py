from bs4 import BeautifulSoup
import requests, json

POSTER_SIZE_SMALL = 'w92'
POSTER_SIZE_LARGE = 'w154'
POSTER_SIZE_XLARGE = 'w500'

RUNNING_MOVIES_URL = 'http://www.moviesrunning.com/kanchipuram/'

TMDB_API_KEY = '721d3e3e99b7ccc880ea363f749d6471'


def get_soup_with_html_loaded():
    resp = requests.get(RUNNING_MOVIES_URL)
    return BeautifulSoup(resp.text, 'html.parser')


def get_tmdb_movie_data(movie_name):
    params = {'api_key': TMDB_API_KEY,
              'query': movie_name}
    resp = requests.get('https://api.themoviedb.org/3/search/movie', params)
    tmdb_search_result = resp.json()
    if tmdb_search_result['total_results'] == 0:
        return None
    tmdb_id = tmdb_search_result['results'][0]['id']
    movie_url = "https://api.themoviedb.org/3/movie/{0}?api_key={1}&append_to_response=videos".format(tmdb_id, TMDB_API_KEY)
    resp = requests.get(movie_url)
    return resp.json()

def get_runtime_from_tmdb_movie_data(tmdb_movie_data):
    return int(tmdb_movie_data.get('runtime', 0))


def get_posterurl_from_tmdb_movie_data(tmdb_movie_data):
    def key_from_partial_url(partial_url):
        if partial_url:
            return partial_url.split('.')[0][1:]
        else:
            return ''

    def build_image_url(key, size):
        if not key or key == '':
            return ''
        return "https://image.tmdb.org/t/p/{0}/{1}.jpg".format(size, key)

    poster_partial_url = tmdb_movie_data.get('poster_path', '')
    poster_key = key_from_partial_url(poster_partial_url)

    poster_url = {}
    poster_url['small'] = build_image_url(poster_key, POSTER_SIZE_SMALL)
    poster_url['normal'] = build_image_url(poster_key, POSTER_SIZE_LARGE)
    return poster_url


def get_genres_from_tmdb_movie_data(tmdb_movie_data):
    def convert_genres_dict_to_list(genre_dicts):
        genre_list = []
        for genre in genre_dicts:
            genre_list.append(genre['name'].strip())
        return genre_list

    return convert_genres_dict_to_list(tmdb_movie_data['genres'])

def get_movie_dict_from_table_row(row):
    movie = {}
    tds = row.find_all('td')
    for ele1, ele2 in zip(tds[0::2], tds[1::2]):
        """
        For reference:
        <td>Babu Theatre - Screen 1<div><span>Madam Street</span></div></td>
        <td class="movieName">Shivalinga<br/><div class="showTime">10:30 AM | 1:30 PM | 5:30 PM | 9:30 PM</div></td>
        """
        ele1.find('div').extract()  # ignore theatre location
        movie['theatre'] = ele1.text.strip()
        show_time = ele2.find('div').extract().text.strip()
        i = show_time.find('Next release')
        if i != -1:
            show_time = show_time[:i]
        movie['show_times'] = show_time.split(' | ')
        movie['movie'] = ele2.text.strip().replace('Book Online', '')
        tmdb_movie_data = get_tmdb_movie_data(movie['movie'])
        movie['runtime'] = get_runtime_from_tmdb_movie_data(tmdb_movie_data) if tmdb_movie_data else None
        movie['poster_url'] = get_posterurl_from_tmdb_movie_data(tmdb_movie_data) if tmdb_movie_data else None
        movie['genres'] = get_genres_from_tmdb_movie_data(tmdb_movie_data) if tmdb_movie_data else None
    return movie


def main():
    soup = get_soup_with_html_loaded()
    table = soup.find('table', attrs={'class':'showTimeTable'})

    # ignore for row  of table, as it contains headers
    all_movies = [get_movie_dict_from_table_row(row) for row in table.find_all('tr')[1:]]
    print json.dumps(all_movies, sort_keys=True, indent=4)


if __name__ == '__main__':
    main()
