DEFAULT_HEADER = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,'
              'image/avif,image/webp,image/apng,*/*;q=0.8,'
              'application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'es,en-US;q=0.9,en;q=0.8,pt;q=0.7',
    # NOTE: do NOT set "accept-encoding: ..., br, zstd" — `requests` cannot
    # decode br/zstd by default and the body comes back as binary garbage.
    'accept-encoding': 'gzip, deflate',
    'cache-control': 'max-age=0',
    'sec-ch-ua': '"Google Chrome";v="147", "Chromium";v="147", "Not?A_Brand";v="99"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'none',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'
                  ' AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36',
    'referer': 'https://www.facebook.com/marketplace/',
}
