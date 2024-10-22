import unittest, json, os 
from unittest.mock import patch, MagicMock
from maps_api_app import haversine_distance, get_details_info, get_nearby_places

TEST_FILES_DIR = os.path.join(os.path.dirname(__file__), 'test_files')

class TestMapsAPIApp(unittest.TestCase):

    def test_haversine_distance(self):
        # Test known distance between two points
        lat1, lon1 = 52.2296756, 21.0122287  # Warsaw
        lat2, lon2 = 41.8919300, 12.5113300  # Rome
        distance = haversine_distance(lat1, lon1, lat2, lon2)
        self.assertAlmostEqual(distance, 1318026, delta=3000)  # 1318 km approximately

    @patch('maps_api_app.requests.get')
    def test_get_details_info(self, mock_get):
        # Load the sample data from the JSON file
        details_file_path = os.path.join(TEST_FILES_DIR, 'sample_results_place_details_api.json')
        with open(details_file_path, 'r') as f:
            sample_data = json.load(f)

        # Mock the response from requests.get
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_data
        mock_get.return_value = mock_response

        # Test the get_details_info function
        api_key = 'fake-api-key'
        place_id = 'fake-place-id'
        result = get_details_info(api_key, place_id)

        # Assertions based on the sample data
        self.assertEqual(result['name'], 'I Soliti Ignoti')
        self.assertEqual(result['formatted_phone_number'], '011 438 6213')
        self.assertEqual(result['website'], 'http://www.isolitiignoti.com/')

    @patch('maps_api_app.requests.get')
    def test_get_nearby_places(self, mock_get):
        # Load the sample data from the JSON file
        nearby_file_path = os.path.join(TEST_FILES_DIR, 'sample_results_nerby_search_api.json')
        with open(nearby_file_path, 'r') as f:
            sample_data = json.load(f)
        # Mock the response from requests.get
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_data
        mock_get.return_value = mock_response

        api_key = 'fake-api-key'
        lat = 40.712776
        lon = -74.005974
        radius = 1500
        type_place = 'restaurant'
        pagetoken = None
        fileout = 'output.csv'
        list_place_id = []

        with patch('builtins.open', unittest.mock.mock_open()) as mock_file:
            list_place_id = get_nearby_places(api_key, lat, lon, radius, type_place, pagetoken, fileout, list_place_id)
            
            # Ensure that the requests.get was called
            mock_get.assert_called()

            # Ensure the file was written to
            mock_file().write.assert_called()

            # Test that two places were processed and written to file
            self.assertEqual(len(list_place_id), 3)
            self.assertEqual(list_place_id[0], 'ChIJ_wMn6_xsiEcRfUrBAmPwZEs')
    

if __name__ == '__main__':
    unittest.main()