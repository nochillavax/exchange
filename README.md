# nochill exchange
the first interactive app within the arena. tip the bot avax, bot sends you nochill back. performs a market trade on behalf of the tipper

powers @nochillexchange in the arena: https://arena.social/?ref=nochillexchange

cleaned up and sped up. but ser its not at 100m+ yet? gfy

## setup

install the requirements, copy env.sample to .env and give it your secrets

set up a schedule for it to run:

#### * * * * * /usr/bin/python3 /path/to/exchange/dir/bot.py 2>&1 > /dev/null
#### 0 0 * * * /usr/bin/python3 /path/to/exchange/dir/leaderboard.py 2>&1 > /dev/null
#### * * * * * /usr/bin/python3 /path/to/exchange/dir/user_scraper.py 2>&1 > /dev/null

## known issues:

* wallet must have some gas in it to start - first tips don't collect enough fees to cover gas (likely due to an order of operations error)
* arenabook woes cause user list to be outdated often. the scraper collects them in json, util_load_db_wallets.py pushes them into the database
* "NOCHILL" in messages is not configurable via .env

  
send donations to 0xAb0fb9ea07CC64703e7954611CF37903bF2Cacdf (the nochill eco wallet)


# Attribution

If you use this bot or any components internally in any way, please make sure to credit @nochillexchange or the NOCHILL project 
