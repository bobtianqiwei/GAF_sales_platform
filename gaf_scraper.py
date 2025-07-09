import requests
import json
import time
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from apscheduler.schedulers.background import BackgroundScheduler
from etl import clean_and_insert

# GAF Coveo API endpoint
API_URL = "https://platform.cloud.coveo.com/rest/search/v2?organizationId=gafmaterialscorporationproduction3yalqk12"

# Set up logging
logging.basicConfig(
    filename='scraper.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s'
)

# Request headers
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; DataCollector/1.0)",
    "Content-Type": "application/json",
    "Authorization": "Bearer xx3cfe6ca4-11f2-45b6-83ad-41e053e06504",
}

# Request body template
BODY_TEMPLATE = {
    "q": "",
    "numberOfResults": 10,
    "firstResult": 0,
}

def fetch_contractors(start=0, page_size=10, lat=None, lng=None, distance=25):
    body = BODY_TEMPLATE.copy()
    body["firstResult"] = start
    body["numberOfResults"] = page_size
    if lat is not None and lng is not None:
        body["aq"] = f'@distanceinmiles <= {distance} AND @gaf_f_country_code = USA'
        body["queryFunctions"] = [
            {
                "fieldName": "@distanceinmiles",
                "function": f"dist(@gaf_latitude, @gaf_longitude, {lat}, {lng})*0.000621371"
            }
        ]
    try:
        resp = requests.post(API_URL, headers=HEADERS, json=body)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logging.error(f"Error fetching contractors for start={start}: {e}")
        return {"results": []}

def parse_results(data):
    contractors = []
    for item in data.get("results", []):
        raw = item.get("raw", {})
        contractors.append({
            "name": item.get("title"),
            "rating": raw.get("gaf_rating"),
            "reviews": raw.get("gaf_number_of_reviews"),
            "phone": raw.get("gaf_phone"),
            "city": raw.get("gaf_f_city"),
            "state": raw.get("gaf_f_state_code"),
            "postal_code": raw.get("gaf_postal_code"),
            "certifications": raw.get("gaf_f_contractor_certifications_and_awards"),
            "type": raw.get("gaf_contractor_type"),
            "contractor_id": raw.get("gaf_contractor_id"),
            "url": item.get("uri"),
        })
    return contractors

def collect_data():
    all_contractors = []
    page_size = 10
    lat, lng = 40.7217861, -74.0094471
    distance = 25
    total = 20  # For demo, fetch 20 records
    starts = list(range(0, total, page_size))
    logging.info("Starting concurrent data collection.")
    with ThreadPoolExecutor(max_workers=4) as executor:
        future_to_start = {
            executor.submit(fetch_contractors, start, page_size, lat, lng, distance): start
            for start in starts
        }
        for future in as_completed(future_to_start):
            start = future_to_start[future]
            try:
                data = future.result()
                contractors = parse_results(data)
                all_contractors.extend(contractors)
                logging.info(f"Fetched page starting at {start}, {len(contractors)} records.")
            except Exception as e:
                logging.error(f"Error in page starting at {start}: {e}")
    clean_and_insert(all_contractors)
    logging.info(f"Total {len(all_contractors)} records collected and inserted into the database.")

def scheduled_job():
    try:
        logging.info("Scheduled data collection started.")
        collect_data()
        logging.info("Scheduled data collection finished.")
    except Exception as e:
        logging.error(f"Scheduled data collection failed: {e}")

def main():
    collect_data()

if __name__ == "__main__":
    # Manual run for demo
    main()
    # Set up weekly scheduler (runs every Monday at 2:00 AM)
    scheduler = BackgroundScheduler()
    scheduler.add_job(scheduled_job, 'cron', day_of_week='mon', hour=2, minute=0)
    scheduler.start()
    print("Scheduler started. (For demo, will not block main thread.)")
    try:
        time.sleep(10)  # For demo, keep alive for 10 seconds
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown() 