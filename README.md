First of all, before to run the app add your YOUR_API_KEY_GOOGLE in the credentials.json file (and username and password to access the app)
Then run the app with the command:

```
python maps_api_app.py
```


Then, it depends on what data you are searching for. You need to insert a latitude and longitude center of your search. Then, it depends on how many results you espect (es 3k restaurant results) and radius of the search. The app will calculate a list of several centers to send the `place/nearbysearch` API of Google. 
When all the places are collected, then the system will collect info using the `place/details` API of Google.

Before to run the script you can setup and have a preview on how much the API will cost you. And where are all the calculated centers.







