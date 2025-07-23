import requests

def OGSPlayerRankLookup(online_handle):

    url = 'https://online-go.com/api/v1/players?username=' + online_handle
    response = requests.get(url)
    response = response.json()

    return response["results"][0]["ranking"]









