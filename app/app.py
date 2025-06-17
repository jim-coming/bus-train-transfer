from flask import Flask, render_template, request
import requests
from datetime import datetime

app = Flask(__name__)

APP_ID = 'b11213017-958e6f5b-cb34-4641'
APP_KEY = '4ea8cbb4-1fec-4782-9aea-9d00cb4f4e0d'

def get_token():
    url = 'https://tdx.transportdata.tw/auth/realms/TDXConnect/protocol/openid-connect/token'
    payload = {
        'grant_type': 'client_credentials',
        'client_id': APP_ID,
        'client_secret': APP_KEY
    }
    response = requests.post(url, data=payload, headers={'Accept': 'application/json'})
    return response.json().get('access_token') if response.status_code == 200 else None

def fetch_bus_routes(token, city):
    url = f'https://tdx.transportdata.tw/api/basic/v2/Bus/FirstLastTripInfo/City/{city}?$format=JSON'
    headers = {'Authorization': f'Bearer {token}'}
    res = requests.get(url, headers=headers)
    return res.json() if res.status_code == 200 else []

def fetch_train_after_time(token, station_code, after_time):
    today = datetime.today().strftime('%Y-%m-%d')
    url = f'https://tdx.transportdata.tw/api/basic/v2/Rail/TRA/DailyTimetable/Station/{station_code}/{today}?$format=JSON'
    headers = {'Authorization': f'Bearer {token}'}
    res = requests.get(url, headers=headers)
    if res.status_code != 200:
        return []
    result = []
    for train in res.json():
        dep_time = train.get('DepartureTime')
        if dep_time and dep_time > after_time:
            result.append({
                'TrainNo': train.get('TrainNo'),
                'DepartureTime': dep_time,
                'TrainType': train.get('TrainTypeName', {}).get('Zh_tw', '未知車種'),
                'Destination': train.get('DestinationStationName', {}).get('Zh_tw', '未知')
            })
    return result

@app.route('/', methods=['GET', 'POST'])
def index():
    station_map = {'Keelung': '0900', 'Chiayi': '5000', 'Hsinchu': '1020'}
    cities = ['Keelung', 'Chiayi', 'Hsinchu']
    selected_city = request.form.get('city')
    selected_route_id = request.form.get('route_id')
    token = get_token()
    bus_routes = []
    selected_route = None
    last_time = ''
    trains = []

    if token and selected_city:
        bus_routes = fetch_bus_routes(token, selected_city)
        route_id_to_route = {f"{r['RouteName']['Zh_tw']} ({r['RouteID']}) [{r['Direction']}]": r for r in bus_routes}
        if selected_route_id and selected_route_id in route_id_to_route:
            selected_route = route_id_to_route[selected_route_id]
            trip_info = selected_route['FirstLastTrips'][0]
            last_time = trip_info['LastTripDepTime']
            trains = fetch_train_after_time(token, station_map[selected_city], last_time)

    return render_template('index.html', cities=cities, selected_city=selected_city,
                           bus_routes=bus_routes, selected_route=selected_route,
                           last_time=last_time, trains=trains)

if __name__ == '__main__':
    app.run(debug=True)
