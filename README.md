# nochill exchange
the first interactive app within the arena
tip the bot avax, bot sends you nochill back
performs a market trade on behalf of the tipper

cleaned up and sped up. but ser its not at 100m+ yet? gfy

## setup

install the requirements, copy env.sample to .env and give it your secrets

set up a schedule for it to run:

## schedule config 
### working cron entries

see the demo @nochillexchange in arena: https://starsarena.com/?ref=nochillexchange

#### * * * * * /usr/bin/python3 /path/to/exchange/dir/bot.py 2>&1 > /dev/null
#### 0 0 * * * /usr/bin/python3 /path/to/exchange/dir/leaderboard.py 2>&1 > /dev/null
#### * * * * * /usr/bin/python3 /path/to/exchange/dir/user_scraper.py 2>&1 > /dev/null


send donations to 0xAb0fb9ea07CC64703e7954611CF37903bF2Cacdf (the nochill eco wallet)

