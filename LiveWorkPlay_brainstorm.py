import pandas as pd
import requests
import json



api_key='VwHJ6rrU7iPL4amYfQlPlprDwbj1OdfOrKqCz4GKHjOIMWWshM4Z7KAG_BmYmEW-tlNtcpHlRwK8bIksnXf2YEM71LCSHVB_pEzfW8vdWbm5taUYen-5b1b17AniXHYx'
headers = {'Authorization': 'Bearer %s' % api_key}




url='https://api.yelp.com/v3/businesses/search'

# In the dictionary, term can take values like food, cafes or businesses like McDonalds
params = {'term':'cafe',
          'latitude': 41.799327,
          'longitude': -87.583625,
          'radius': 1000,
          'limit': 50}


# Making a get request to the API
req = requests.get(url, params=params, headers=headers)

# proceed only if the status code is 200
if req.status_code == 200:
    # printing the text from the response
    bus = json.loads(req.text)

bus.keys()

for business in bus['businesses']:
    print(business['name'])
