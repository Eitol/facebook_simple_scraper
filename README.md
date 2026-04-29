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
    DaysSinceListed,
    MarketplaceVehicleFilters,
    VehicleAvailability,
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
    # Location: prefer lat/lng (works for any city). The slug is only honored
    # by Facebook for vanity URLs; arbitrary slugs are silently ignored.
    latitude=-33.4489, longitude=-70.6693, radius_km=80,   # Santiago, Chile
    # location="santiago",                        # optional FB vanity slug
    condition=VehicleCondition.USED,              # NEW | USED | ALL
    query="toyota corolla",                       # optional
    availability=VehicleAvailability.IN_STOCK,    # IN_STOCK | OUT_OF_STOCK | ALL
    days_since_listed=DaysSinceListed.LAST_WEEK,  # LAST_DAY | LAST_WEEK | LAST_MONTH | ANY
)

for listing in scraper.get_marketplace_vehicles(filters):
    print(listing.title, listing.price, listing.location,
          "SOLD" if listing.is_sold else "", listing.url)
```

#### 🔍 Marketplace listing detail

Fetch the full detail for a single listing — all photos, description text,
publication date and vehicle attributes:

```python
from facebook_simple_scraper.marketplace.entities import MarketplaceListingDetail

# listing_id can come from a MarketplaceVehicleListing.id returned above
detail: MarketplaceListingDetail = scraper.get_marketplace_vehicle_detail("1234567890")

print(detail.title)
print(detail.price, detail.currency)
print(detail.description)
print(detail.location)
print(detail.creation_time)
for url in detail.images:
    print(url)          # full-resolution photo URLs
```

> ⚠️ Facebook ignores the `latitude`/`longitude` parameters for unauthenticated
> requests and falls back to IP-based geolocation. Provide valid login
> credentials in `ScraperOptions` so the session location is honored.
 
🔒 License
MIT License (Do whatever you want with this code, but don't blame me if something goes wrong)
 
We hope you find our Facebook Post Scraper helpful! Your feedback and contributions are always welcome. Enjoy scraping!

 
The Facebook Post Scraper Team
❗ Disclaimers: Please be aware of Facebook's terms and conditions pertaining to data scraping. It's your responsibility to use this tool in accordance with those terms.