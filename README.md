## Facebook Simple Scraper

Welcome to the Facebook Post Scraper project! Our tool allows you to scrape posts from different Facebook pages, helping you gather crucial information flexibly and efficiently.
 
### 🚀 Features

- Post Scraping: Scrapes individual posts from a Facebook page, capturing all the details that accompany the post.
- Comment Scraping: Fetches the comments under each post. This can provide you with valuable audience feedback and participation related to each post.
- **Marketplace Vehicle Search**: Search vehicle listings on Facebook Marketplace filtered by location, condition (new/used) and an optional free-text query.

 
### 📄Usage

Using our scraping tool is extremely simple. After setting up your environment correctly, you can start scraping right away!

```python
user, password = "your_user_email", "your_password"
opts = ScraperOptions(
    credentials=[LoginCredentials(
        username=user,
        password=password
    )],
    max_comments_per_post=10,
    sleep_time_min=2,
    sleep_time_max=5,
    stop_conditions=[StopAfterNPosts(5)],
)
scraper = Scraper(opts)
post = scraper.get_posts("NintendoLatAm")
print(list(post))
```

#### 🚗 Marketplace vehicle search

Search vehicle listings in Facebook Marketplace filtered by location,
condition and (optionally) a search text:

```python
from facebook_simple_scraper.scraper import Scraper
from facebook_simple_scraper.entities import ScraperOptions, LoginCredentials
from facebook_simple_scraper.stop_conditions import StopAfterNPosts
from facebook_simple_scraper.marketplace.entities import (
    MarketplaceVehicleFilters,
    VehicleCondition,
)

opts = ScraperOptions(
    credentials=[LoginCredentials(username="me@example.com", password="***")],
    stop_conditions=[StopAfterNPosts(50)],
    sleep_time_min=2,
    sleep_time_max=5,
)
scraper = Scraper(opts)

filters = MarketplaceVehicleFilters(
    location="santiago",            # Facebook location slug
    condition=VehicleCondition.USED, # NEW | USED | ALL
    query="toyota corolla",          # optional
)

for listing in scraper.get_marketplace_vehicles(filters):
    print(listing.title, listing.price, listing.location, listing.url)
```
 
🔒 License
MIT License (Do whatever you want with this code, but don't blame me if something goes wrong)
 
We hope you find our Facebook Post Scraper helpful! Your feedback and contributions are always welcome. Enjoy scraping!

 
The Facebook Post Scraper Team
❗ Disclaimers: Please be aware of Facebook's terms and conditions pertaining to data scraping. It's your responsibility to use this tool in accordance with those terms.