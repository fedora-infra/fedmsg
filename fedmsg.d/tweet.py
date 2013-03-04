config = dict(
    tweet_intermessage_pause=1,  # seconds
    tweet_hibernate_duration=60 * 3,  # seconds
    tweet_endpoints=[
        # Actually using twitter.com is unlikely due to their daily
        # tweet limit.
        #dict(
        #    base_url="http://api.twitter.com",
        #    consumer_key="get",
        #    consumer_secret="these",
        #    access_token_key="from",
        #    access_token_secret="dev.twitter.com",
        #),

        # However, statusnet seems to be more permissive.
        dict(
            base_url="http://identi.ca/api",
            consumer_key="get this from",
            consumer_secret="http://identi.ca/",
            access_token_key="generate these with",
            access_token_secret="https://gist.github.com/4070630",
        ),
    ],
    bitly_settings=dict(
        api_user="get this from",
        api_key="http://bit.ly/"
    ),
)
