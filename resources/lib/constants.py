HEADERS = {
    'User-Agent': 'Mozilla/5.0 (PlayStation 0 5.55) AppleWebKit/537.73 (KHTML, like Gecko)',
    'X-Requested-With': 'com.showmax.app',
}

API_URL   = 'https://api.showmax.com/v97.3/android/{}'
LOGIN_URL = 'https://secure.showmax.com/v97.3/android/signin'

LIST_EXPIRY    = (60*60*48) #48 hours
EPISODE_EXPIRY = (60*60*6)  #6 hours

THUMB_HEIGHT  = 500
FANART_HEIGHT = 720