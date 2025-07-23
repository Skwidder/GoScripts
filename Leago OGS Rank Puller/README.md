# Leago Rank Checker

Compare player ranks between Leago tournaments and the Online Go Server (OGS).

## What it does

1. Logs into Leago through your browser
2. Gets player data from a Leago tournament
3. Looks up each player's OGS rank
4. Creates a CSV file comparing both ranks

## How to use

1. Run the script:
   ```bash
   python rank_checker.py
   ```

2. Sign into Leago when the browser opens

3. Paste the URL of the Leago tournament you want to check

4. The script creates `player_ranks.csv` with the results

## Output

The CSV file shows:
- Player name
- OGS username 
- Leago rank (converted to kyu/dan)
- OGS rank (converted to kyu/dan)

## Requirements

- Python 3.7+
- `httpx` (install with `pip install httpx`)
- `requests` (install with `pip install requests`)
- All other required modules are included with the script

## Notes

- Only works with single-tournament events
- Players without OGS handles show as "N/A"