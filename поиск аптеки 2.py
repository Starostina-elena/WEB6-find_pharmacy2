import sys
from io import BytesIO
import requests
from PIL import Image

from count_zoom_for_map import count_zoom_for_map
from Samples import distance


def get_input_address_coords(toponym_to_find):
    geocoder_params = {
        "apikey": "40d1649f-0493-4b70-98ba-98533de7710b",
        "geocode": toponym_to_find,
        "format": "json"}

    response = requests.get(geocoder_api_server, params=geocoder_params)

    json_response = response.json()

    toponym = json_response["response"]["GeoObjectCollection"][
        "featureMember"][0]["GeoObject"]

    toponym_coordinates = toponym["Point"]["pos"]
    toponym_longitude, toponym_lattitude = toponym_coordinates.split(" ")

    lower_corner = [float(i) for i in toponym['boundedBy']['Envelope']['lowerCorner'].split()]
    upper_corner = [float(i) for i in toponym['boundedBy']['Envelope']['upperCorner'].split()]

    return [toponym_longitude, toponym_lattitude], lower_corner, upper_corner


def find_business_near(api_key, toponym_coords, type_business):
    search_params = {
        "apikey": api_key,
        "text": type_business,
        "lang": "ru_RU",
        "ll": ",".join(toponym_coords),
        "type": "biz"
    }

    response = requests.get(search_api_server, params=search_params)

    json_response = response.json()

    organization = json_response["features"][0]
    org_name = organization["properties"]["CompanyMetaData"]["name"]
    org_address = organization["properties"]["CompanyMetaData"]["address"]
    org_time_opened = organization['properties']['CompanyMetaData']['Hours']['text']
    point = organization["geometry"]["coordinates"]
    org_upper_corner = organization['properties']['boundedBy'][0]
    org_lower_corner = organization['properties']['boundedBy'][1]
    org_point = "{0},{1}".format(point[0], point[1])

    return org_upper_corner, org_lower_corner, org_point, point, org_name, org_address, org_time_opened


def get_cart(org_upper_corner, org_lower_corner, lower_corner, upper_corner, toponym_longitude, toponym_lattitude,
             org_point):
    width_degrees = max([org_upper_corner[0], org_lower_corner[0], lower_corner[0], upper_corner[0]]) - \
                    min([org_upper_corner[0], org_lower_corner[0], lower_corner[0], upper_corner[0]])
    height_degrees = max([org_upper_corner[1], org_lower_corner[1], lower_corner[1], upper_corner[1]]) - \
                     min([org_upper_corner[1], org_lower_corner[1], lower_corner[1], upper_corner[1]])

    delta = str(count_zoom_for_map(width_degrees, height_degrees))

    cart_center = [
        str(min([org_upper_corner[0], org_lower_corner[0], lower_corner[0], upper_corner[0]]) + width_degrees / 2),
        str(min([org_upper_corner[1], org_lower_corner[1], lower_corner[1], upper_corner[1]]) + height_degrees / 2)
    ]

    map_params = {
        "ll": ",".join(cart_center),
        "spn": ",".join([delta, delta]),
        'pt': f'{",".join([toponym_longitude, toponym_lattitude])},pmwtm~{org_point},pmblm',
        "l": "map"
    }

    response = requests.get(map_api_server, params=map_params)

    Image.open(BytesIO(
        response.content)).show()


def create_snippet(title, address, time, distance):

    print(f'Аптека "{title}"')
    print(f'Адрес: {address}')
    print(f'Открыто {time}')
    print(f'Расстояние: {distance} метров')


if __name__ == '__main__':

    toponym_to_find = 'Саратов, Университетская, 67/73'

    geocoder_api_server = "http://geocode-maps.yandex.ru/1.x/"
    search_api_server = "https://search-maps.yandex.ru/v1/"
    search_api_key = "dda3ddba-c9ea-4ead-9010-f43fbc15c6e3"
    map_api_server = "http://static-maps.yandex.ru/1.x/"

    input_address_coords, input_address_lower_corner, input_address_upper_corner = get_input_address_coords(
        toponym_to_find)

    pharmacy_upper_corner, pharmacy_lower_corner, pharmacy_coords, int_pharmacy_coords, pharmacy_name, \
        pharmacy_address, pharmacy_time_opened = find_business_near(
            search_api_key, input_address_coords, 'аптека')

    get_cart(pharmacy_upper_corner, pharmacy_lower_corner, input_address_lower_corner, input_address_upper_corner,
             *input_address_coords, pharmacy_coords)

    distance = int(distance.lonlat_distance(int_pharmacy_coords, [float(i) for i in input_address_coords]))

    create_snippet(pharmacy_name, pharmacy_address, pharmacy_time_opened, distance)
