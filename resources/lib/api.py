import hashlib

from bs4 import BeautifulSoup

from matthuisman import userdata
from matthuisman.session import Session
from matthuisman.log import log

from .constants import HEADERS, API_URL, LOGIN_URL

class Error(Exception):
    pass

class API(object):
    def __init__(self):
        self.new_session()

    def new_session(self):
        self._logged_in = False
        self._session = Session(HEADERS, base_url=API_URL)
        self._set_access_token(userdata.get('access_token'))

    def _set_access_token(self, token):
        if token:
            self._session.headers.update({'Authorization': 'Bearer {}'.format(token)})
            self._logged_in = True

    @property
    def logged_in(self):
        return self._logged_in
        
    def login(self, username, password):
        log('API: Login')

        data = {
            'response_type': 'token',
            'lang': 'eng'
        }

        resp = self._session.get(LOGIN_URL, params=data)
        soup = BeautifulSoup(resp.text, 'html.parser')

        form = soup.find('form', id='new_signin')
        for e in form.find_all('input'):
            data[e.attrs['name']] = e.attrs.get('value')

        data.update({
            'signin[email]': username,
            'signin[password]': password,
        })

        resp = self._session.post(LOGIN_URL, data=data, allow_redirects=False)
        access_token = resp.cookies.get('showmax_oauth')
        
        if not access_token:
            self.logout()
            return False

        self._set_access_token(access_token)

        data = self._session.get('user/current', params={'lang':'eng'}).json()
        if 'error_code' in data:
            return False

        device_id = hashlib.sha1(username).hexdigest().upper()

        userdata.set('device_id', device_id)
        userdata.set('access_token', access_token)
        userdata.set('user_id', data['user_id'])
        return True

    def logout(self):
        log('API: Logout')
        userdata.delete('device_id')
        userdata.delete('access_token')
        userdata.delete('user_id')
        self.new_session()

    def _catalogue(self, _params):
        def process_page(start):
            params = {
                'field[]': ['id', 'images', 'title', 'items', 'total', 'type', 'description', 'videos'],
                'lang': 'eng',
                'showmax_rating': 'adults',
                'sort': 'alphabet',
                'start': start,
                'subscription_status': 'full'
            }

            params.update(_params)

            data = self._session.get('catalogue/assets', params=params).json()
            items = data['items']

            count     = int(data.get('count', 0))
            remaining = int(data.get('remaining', 0))
            if count > 0 and remaining > 0:
                items.extend(process_page(start + count))

            return items

        return process_page(start=0)

    def all_series(self):
        return self._catalogue({
            'type': 'tv_series',
            'exclude_section[]': ['kids'],
        })

    def movies(self):
        return self._catalogue({
            'type': 'movie',
            'exclude_section[]': ['kids'],
        })

    def kids(self):
        return self._catalogue({
            'section': 'kids',
        })

    def series(self, series_id):
        params = {
            'field[]': ['id', 'images', 'title', 'items', 'total', 'type', 'description', 'videos', 'number', 'seasons', 'episodes'],
            'lang': 'eng',
            'showmax_rating': 'adults',
            'subscription_status': 'full'
        }

        return self._session.get('catalogue/tv_series/{}'.format(series_id), params=params).json()

    def search(self, query):
        return self._catalogue({
            'q': query,
        })

    def play(self, video_id):
        params = {
            'encoding': 'mpd_widevine_modular',
            'subscription_status': 'full',
            'lang': 'eng',
        }

        data = self._session.get('playback/play/{}'.format(video_id), params=params).json()
        
        url        = data['url']
        task_id    = data['packaging_task_id']
        session_id = data['session_id']

        data = {
            'user_id': userdata.get('user_id'),
            'video_id': video_id,
            'hw_code': userdata.get('device_id'),
            'packaging_task_id': task_id,
            'session_id': session_id,
        }

        params = {'showmax_rating': 'adults', 'lang': 'eng'}
        data = self._session.post('playback/verify', params=params, data=data).json()

        license_request = data['license_request']
        license_url = API_URL.format('drm/widevine_modular?license_request={}'.format(license_request))

        return url, license_url