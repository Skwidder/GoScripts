import asyncio
from leagoAPI import LeagoAuth, AuthClient
import csv
import json
from OGS import OGSPlayerRankLookup


async def run_auth_flow():
    auth = LeagoAuth()
    await auth.login()

    client = AuthClient(auth)
    return client

def RankConversion(rank):
    """
    Convert an integer OGS rank to a traditional Go rank (kyu or dan).
    This uses a fixed scale:
        OGS 13 = 17k
        OGS 29 = 1k
        OGS 30 = 1d
        OGS 33 = 4d

        Leago Also uses this same conversion
    """
    # print("RANK: " + rank)
    rank = round(rank)
    
    if rank <= 29:
        kyu_rank = 30 - rank
        return f"{kyu_rank}k"
    else:
        dan_rank = rank - 29
        return f"{dan_rank}d"


def lookupAndSave(json):
    output_csv = "player_ranks.csv"
    with open(output_csv, "w", newline='', encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Name", "Online Handle", "Leago Rank", "OGS Rank"])

        for player in json:
            name = f"{player.get('givenName', '')} {player.get('familyName', '')}".strip()

            leagoRank = RankConversion(player.get('rankId'))

            handle = player.get("onlineHandle", "").strip()
            if not handle:
                writer.writerow([name, "N/A", leagoRank, "N/A"])
                continue

            try:
                OGSRank = RankConversion(OGSPlayerRankLookup(handle))
            except Exception as e:
                OGSRank = f"Error: {e}"

            print(f"{name} ({handle}): {leagoRank}:{OGSRank}")
            writer.writerow([name, handle, leagoRank, OGSRank])





async def main():
    print("Sign Into Leago in your web-browser")
    client = await run_auth_flow()

    url = input("Welcome to Rank Checker(tm) \nPlease input the URL of the Leago Event/Tournament you would like to check:")
    event = url[url.rfind("/") + 1:]

    response = await client.get(f"https://api.leago.gg/api/v1/events/{event}/tournaments?owned=false")
    response = response.json()

    if len(response) == 0:
        print("Event Not Found: Check to make sure you copied the URL right")
        exit
    elif len(response) > 1:
        print("Event Has More than 1 Tournment, Is this possible?")
        exit
    
    tournment = response[0]["key"]

    response = await client.get(f"https://api.leago.gg/api/v1/tournaments/{tournment}/players")
    response = response.json()

    lookupAndSave(response)


asyncio.run(main())




