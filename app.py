import flask
import requests
import json
from ampel import ampel_info

app = flask.Flask(__name__)

@app.route('/coord')
def coord():
    bad_request = flask.Response(status=400)

    lat = flask.request.args.get('lat', default = -1, type = float)
    lon = flask.request.args.get('lon', default = -1, type = float)

    if not validate_request(lat, lon):
        return bad_request
    
    r = requests.get(f'https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json')
    
    coord = r.json()
    if not validate_coord(coord):
        return bad_request
    
    postcode = coord['address']['postcode']
    ampel_status = get_ampel_status(postcode)
    ampel_info = get_ampel_info(ampel_status)

    return {
        'postcode': postcode,
        'ampel_status': ampel_status,
        'ampel_info': ampel_info,
    }

def validate_request(lat, lon):
    if (lat < 0 or lon < 0):
        return False
    return True

def validate_coord(coord):
    if not 'address' in coord:
        print('bad address')
        return False
    if not 'postcode' in coord['address']:
        print('bad postcode')
        return False

    return True

def get_ampel_status(postcode):

    r = requests.get('https://corona-ampel.gv.at/sites/corona-ampel.gv.at/files/assets/Warnstufen_Corona_Ampel_aktuell.json')

    response = r.json()
    warnstufen = response[0]['Warnstufen']
    
    for region in warnstufen:
        # If the region code is part of the postcode we have a match
        if region['GKZ'] == postcode[:len(region['GKZ'])]:
            return region['Warnstufe']

    # If there's not entry, there's no threat
    return 1

def get_ampel_info(ampel_status):
    return ampel_info[ampel_status]
