import flask
import random
from flask_cors import cross_origin
import requests
import json
from datetime import datetime
from dateutil import parser
from ampel import ampel_info, ampel_data
from util import plz_to_gkz

app = flask.Flask(__name__)

@app.route('/coord')
@cross_origin()
def coord():
    lat = flask.request.args.get('lat', default = -1, type = float)
    lon = flask.request.args.get('lon', default = -1, type = float)

    if not validate_request(lat, lon):
        return 'INVALID_REQUEST', 400
    
    r = requests.get(f'https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json')
    
    coord = r.json()
    if not validate_coord(coord):
        return 'INVALID_COORD', 400
    
    postcode = coord['address']['postcode']
    ampel_status, stand = get_ampel_status(postcode)
    if ampel_status == -1:
        return 'OUT_OF_REGION', 400

    ampel_info = get_ampel_info(ampel_status)

    return {
        'postcode': postcode,
        'ampel_status': ampel_status,
        'stand': stand,
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

    data = get_ampel_data()
    warnstufen = data['Warnstufen']
    stand = int(parser.parse(data['Stand']).timestamp())
    
    if postcode not in plz_to_gkz:
        return -1, stand

    for region in warnstufen:
        # If the region code is part of the postcode we have a match
        #if region['GKZ'] == postcode[:len(region['GKZ'])]:
        if region['GKZ'] == plz_to_gkz[postcode][:len(region['GKZ'])]:
            return region['Warnstufe'], stand

    # If there's no entry, there's no threat
    return -1, stand

def get_ampel_info(ampel_status):
    return ampel_info[ampel_status]


def get_ampel_data():
    timestamp = datetime.now().timestamp()

    # The data is too old, we need to update
    if timestamp - ampel_data['lastUpdate'] > 60 * 60 * 1: #Update every hour
        print('UPDATING AMPEL DATA')
        r = requests.get('https://corona-ampel.gv.at/sites/corona-ampel.gv.at/files/assets/Warnstufen_Corona_Ampel_aktuell.json')

        response = r.json()

        newestTime = 0
        newestEntry = None
        for entry in response:
            entryTime = parser.parse(entry['Stand']).timestamp()
            if entryTime > newestTime:
                newestTime = entryTime
                newestEntry = entry
        
        ampel_data['lastUpdate'] = timestamp
        ampel_data['data'] = newestEntry
    
    return ampel_data['data']