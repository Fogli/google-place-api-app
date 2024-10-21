from flask import Flask, render_template, request, redirect, url_for, Response, send_file
import requests, json , time , sys, math , csv, os 

app = Flask(__name__)

# Load credentials from external file
def load_credentials():
    with open('credentials.json') as f:
        credentials = json.load(f)
    return credentials

# Initialize credentials
credentials = load_credentials()

# Store username and password in app config
app.config['USERNAME'] = credentials['username']
app.config['PASSWORD'] = credentials['password']
app.config['API_GOOGLE_KEY'] = credentials['api_key_google']


def haversine_distance(lat1, lon1, lat2, lon2):
    # Radius of the Earth in meters
    R = 6371000

    # Convert latitude and longitude from degrees to radians
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    # Haversine formula
    a = math.sin(delta_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    # Distance in meters
    distance = R * c
    return distance

def get_details_info(api_key, place_id):
    
    details_url = f'https://maps.googleapis.com/maps/api/place/details/json?place_id={place_id}&fields=name,formatted_phone_number,website&key={api_key}'
    details_response = requests.get(details_url)
    if details_response.status_code == 200:
        obj = details_response.json().get('result', {})
    else:
        print(f'Errore nella richiesta details: {details_response.status_code}')
        obj = {}
    return obj 

def get_nearby_places(api_key, lat, lon, radius, type_place, pagetoken, fileout, list_place_id):
    
    counter = 0
    if list_place_id is None or len(list_place_id)==0:
        list_place_id = []
        # Initialize the JSON file (clear content)
        fw_clean = open(fileout, 'w')
        fw_clean.write('') # Clear the file at the beginning
        fw_clean.close()

    with open(fileout, "a") as fw:
        
        while True:
            print(f"pagetoken:{pagetoken}")
            location = f"{lat},{lon}"
            nearbysearch_url = f'https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={location}&radius={radius}&type={type_place}&key={api_key}&pagetoken={pagetoken}&rankBy=DISTANCE'
            response = requests.get(nearbysearch_url)
            
            #print(place)
            if response.status_code == 200:
                
                results = response.json().get('results', [])
                pagetoken = response.json().get('next_page_token', None)
                for place in results:
                    obj = {}
                    name = place.get('name')
                    address = place.get('vicinity')
                    place_id = place.get('place_id')
                    
                    obj["name"] = name
                    obj["place_id"] =  place_id
                    obj["address"] = address
                    obj["rating_count"] = place.get('user_ratings_total')
                    obj["rating"] = place.get('rating')
                    obj["lat"] = place['geometry'].get('location').get('lat')
                    obj["long"] = place['geometry'].get('location').get('lng')
                    obj["types"] = '|'.join(place.get('types'))
                    print(f'Nome: {name}, Indirizzo: {address}, Place_id: {place_id}, ({round(obj["lat"],5)},{round(obj["long"],5)})')
                    
                    # avoid calling again details of place already called
                    if place_id in list_place_id:
                        continue
                    details_obj = get_details_info(api_key, place_id)
                    obj.update(details_obj)
                    fw.write(json.dumps(obj) + '\n')
                    list_place_id.append(place_id)     
                    counter += 1
                    print(f"list_place_id LENGTH: {len(list_place_id)}") 
                    
                    
            else:
                print(f'Errore nella richiesta nearbysearch: {response.status_code}')
                break
            time.sleep(2) 
            print(f"{counter} risto salvati")
            
            if not pagetoken:
                break
                
            return list_place_id

def calculate_centers(lat, lon, radius, expected_results, results_per_query=20):
    # Calculate the number of centers required
    num_centers = math.ceil(expected_results / results_per_query)
    
    # Calculate the distance in degrees for the given radius
    # Earth's radius in meters
    earth_radius = 6371000  
    
    # Convert radius from meters to degrees
    delta_lat = radius / earth_radius * (180 / math.pi)
    delta_lon = radius / earth_radius * (180 / math.pi) / math.cos(lat * math.pi / 180)
    
    # Calculate the grid size (number of rows/columns needed)
    grid_size = math.ceil(math.sqrt(num_centers))
    
    # Calculate the distance between centers to cover the area
    step_lat = 2 * delta_lat / grid_size
    step_lon = 2 * delta_lon / grid_size
    
    # Generate the centers
    centers = []
    
    print(f"grid_size: {grid_size}, delta_lat : {delta_lat}, delta_long : {delta_lon}, step_lat: {step_lat}, step_long: {step_lon}")
    for i in range(grid_size):
        for j in range(grid_size):
            new_lat = lat - (grid_size // 2) * step_lat + i * step_lat
            new_lon = lon - (grid_size // 2) * step_lon + j * step_lon
            centers.append((new_lat, new_lon))
    
    intermediate_distance_in_meters = 0
    if grid_size > 1:
        intermediate_distance_in_meters = haversine_distance(centers[0][0], centers[0][1], centers[1][0], centers[1][1])
        print(f"distance between two adjacent centers: {intermediate_distance_in_meters} ")
    else:
        print("only 1 center, no grid needed")
    return centers, intermediate_distance_in_meters

def write_output_csv(input_json,output_csv):

    final_obj = {}
    with open(input_json, "r") as fr:
        for restaurant in fr:
            rest = json.loads(restaurant)
            name = rest["name"]
            if rest["name"] in final_obj:
                continue
            else:
                final_obj[name] = rest
    
    with open(output_csv, 'w', newline='', encoding='utf-8') as outcsv:

        #header = list(list(final_obj.values())[0].keys())
        header = ["name","place_id", "address", "rating_count", "rating", "formatted_phone_number", "website", "lat", "long", "types"]
        writer = csv.DictWriter(outcsv, fieldnames=header, delimiter = ",")
        writer.writeheader()
        writer.writerows(final_obj.values())
        #for restaurant_data in list(final_obj.values()):
        #    writerows(restaurant_data)
     
# Home route to display the form
@app.route('/')
def home():
    return render_template('index.html')

# Route for handling login
@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    if username == app.config['USERNAME'] and password == app.config['PASSWORD']:
        return redirect(url_for('form'))
    else:
        return "Unauthorized", 401

# Route to display the form for input
@app.route('/form')
def form():
    return render_template('form.html')

@app.route('/estimate', methods=['POST'])
def estimate_costs():
    # Retrieve input parameters from form
    place_type = request.form['place_type']
    center_lat = float(request.form['center_lat'])
    center_lon = float(request.form['center_lon'])
    radius = int(request.form['radius'])
    expected_results = int(request.form['expected_results'])
    place_api_nerby_search_price = float(request.form['place_api_nerby_search_price'])
    place_api_place_details_price = float(request.form['place_api_place_details_price'])
    
    # Calculate centers and estimate costs
    centers, intermediate_distance_in_meters = calculate_centers(center_lat, center_lon, radius, expected_results, results_per_query=20)
    num_centers = len(centers)
    estimated_cost_nerby_places = round(num_centers * place_api_nerby_search_price,4) 
    estimated_cost_place_details = round(expected_results * place_api_place_details_price,4)  # Example cost estimation
    
    # Store centers in a session or global variable (simplified for this example)
    app.config['CENTERS'] = centers
    app.config['CENTER_LAT'] = center_lat
    app.config['CENTER_LON'] = center_lon
    
    # Render the estimate page with parameters and costs
    return render_template('estimate.html', place_type=place_type, center_lat=center_lat, center_lon=center_lon,
                           radius=radius, expected_results=expected_results, num_centers=num_centers,
                           estimated_cost_nerby_places=estimated_cost_nerby_places,
                           estimated_cost_place_details=estimated_cost_place_details)

# Route to handle form submission and run the script
@app.route('/run', methods=['POST'])
def run_script():
    
    place_type = request.form['place_type']
    center_lat = float(request.form['center_lat'])
    center_lon = float(request.form['center_lon'])
    radius = int(request.form['radius'])
    expected_results = int(request.form['expected_results'])
    api_key_google = app.config['API_GOOGLE_KEY']

    centers, intermediate_distance_in_meters = calculate_centers(center_lat, center_lon, radius, expected_results, results_per_query=20)
    num_centers = len(centers)
    
    # Stream response with log updates
    
    csv_file = 'results.csv'
    file_out_json = 'results.json'
    pagetoken = ''

    center = 1
    list_place_id = []
    radius_single_center = intermediate_distance_in_meters
    for location in centers: 
         lat = location[0]
         lon = location[1]
         msg = f"processing center: {center}, ({lat}, {lon})"
         list_place_id = get_nearby_places(api_key=api_key_google, lat=lat, lon=lon, radius=radius_single_center, 
                                           type_place=place_type, pagetoken=pagetoken, fileout=file_out_json, list_place_id=list_place_id)
         center += 1
         print(f"iterating on center : {center}")
        
    write_output_csv(file_out_json,csv_file)
    return render_template('download.html', filename=csv_file)
    # Route to handle file download

@app.route('/download/<filename>')
def download_file(filename):
    return send_file(filename, as_attachment=True)

@app.route('/print_centers')
def print_centers():
    centers = app.config.get('CENTERS', [])
    # Retrieve the center latitude and longitude from the app configuration
    center_lat = app.config.get('CENTER_LAT', 0.0)  # Default to 0 if not set
    center_lon = app.config.get('CENTER_LON', 0.0)  # Default to 0 if not set



    if not centers:
        return "No centers to display.", 400

    # Render the print centers page
    # Render the print centers page with the list of centers and the center lat/lon
    return render_template('print_centers.html', centers=centers, center_lat=center_lat, center_lon=center_lon)



if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
    


    