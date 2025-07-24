import cv2
import numpy as np
import requests
from io import BytesIO
from pyproj import Transformer
import math
import json


s3_survey_border = "https://s3.ap-south-2.amazonaws.com/prod-assets.mypropertyqr.in/survey_border/"

import requests
import numpy as np
import cv2

def get_image(init_tile_x, init_tile_y):
    try:
        # Construct URL
        url = f'https://s3.ap-south-2.amazonaws.com/prod-assets.mypropertyqr.in/survey_border/{init_tile_x}/{init_tile_y}.png'
        
        # Make the request
        response = requests.get(url)
        response.raise_for_status()  # Raises error for HTTP codes >= 400

        # Process the image content
        image_array = np.asarray(bytearray(response.content), dtype=np.uint8)
        image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

        if image is None:
            raise ValueError(f"Could not decode image from URL: {url}")

        return image

    except requests.exceptions.HTTPError as e:
        # Specific handling for 403 errors
        if e.response.status_code == 403:
            print(f"Access Forbidden (403): You do not have permission to access the URL: {url}")
            # Explicitly re-raise the 403 error to notify calling code
            return None
        else:
            print(f"HTTP error occurred: {e}")
            raise e

    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        raise

    except ValueError as e:
        print(f"Value error: {e}")
        raise

    except Exception as e:
        print(f"Unexpected error: {e}")
        raise

transformer_to_3857 = Transformer.from_crs("EPSG:4326", "EPSG:3857")
def convert_4326_to_3857(lat, lon):
    x, y = transformer_to_3857.transform(lat, lon)
    return {'x': x, 'y': y}

def get_tile_coordinates(lat, lon, zoom):
    coords = convert_4326_to_3857(lat, lon)
    x, y = coords['x'], coords['y']

    tile_size = 256  # Size of each tile in pixels
    initial_resolution = 2 * math.pi * 6378137 / tile_size  # Resolution at zoom level 0
    resolution = initial_resolution / (2 ** zoom)

    tile_x = math.floor((x + 20037508.3427892) / (resolution * tile_size))
    tile_y = math.floor((20037508.3427892 - y) / (resolution * tile_size))

    pixel_x = math.floor(((x + 20037508.3427892) % (resolution * tile_size)) / resolution)
    pixel_y = math.floor(((20037508.3427892 - y) % (resolution * tile_size)) / resolution)

    return {
        "tx":tile_x,
        "ty":tile_y,
        "pix_cord_X":pixel_x,
        "pix_cord_Y":pixel_y
    }

def survey_num_init(lat,lon):
    try:
        result = get_tile_coordinates(lat, lon, 18)
        return json.dumps(result)
    except (TypeError, ValueError) as e:
        return json.dumps({"error": str(e)}), 400
    
def distance(x1, y1, x2, y2):
    # Calculate the Euclidean distance
    distance = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
    return distance

def relative_cord(x_, y_):
    tilex, tiley, pixx, pixy = 0, 0, 0, 0
    r = 0.0
    
    if x_ < 0:
        r = x_ / 256 - 1
        pixx = (x_ - 256) % 256
        if r == int(r):
            tilex = int(r + 1)
        else:
            tilex = int(r)
    else:
        tilex = int(x_ / 256)
        pixx = (x_ - 256) % 256

    if y_ < 0:
        r = y_ / 256 - 1
        pixy = (y_ - 256) % 256
        if r == int(r):
            tiley = int(r + 1)
        else:
            tiley = int(r)
    else:
        tiley = int(y_ / 256)
        pixy = (y_ - 256) % 256

    return [pixx, pixy, tilex, tiley]


import math

def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # Earth radius in kilometers
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    a = math.sin(delta_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c  # Distance in kilometers

def calculate_area(points):
    # Convert dictionary to a list of (lat, lon) tuples
    coordinates = [(data['lat'], data['lon']) for key, data in points.items()]
    
    # Shoelace Theorem for calculating area of a polygon
    area = 0
    n = len(coordinates)
    for i in range(n):
        lat1, lon1 = coordinates[i]
        lat2, lon2 = coordinates[(i + 1) % n]  # Connect the last point to the first one
        area += lon1 * lat2 - lon1 * lat2  # Cross-product sum
    
    area = abs(area) / 2.0
    
    # Convert to square kilometers using haversine distance between adjacent points
    total_distance = 0
    for i in range(n):
        lat1, lon1 = coordinates[i]
        lat2, lon2 = coordinates[(i + 1) % n]
        total_distance += haversine(lat1, lon1, lat2, lon2)
    
    return total_distance

def calculate_scale_ratio(lat_lon1, lat_lon2, pixel1, pixel2):
    
    # Calculate the geographical distance (latitude, longitude) in kilometers
    lat1, lon1 = lat_lon1
    lat2, lon2 = lat_lon2
    
    # Calculate the geographical distance in both latitude and longitude
    geo_distance = haversine(lat1, lon1, lat2, lon2)
    
    # Calculate the pixel distance
    x1, y1 = pixel1
    x2, y2 = pixel2
    pixel_distance = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
    
    # Calculate the scale ratio (pixels per km)
    scale_ratio = pixel_distance / geo_distance
    return scale_ratio

