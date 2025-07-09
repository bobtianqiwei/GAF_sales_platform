import json
import os
from models import Contractor, Session
import openai
import logging
from geopy.geocoders import Nominatim
import time

def clean_and_insert(contractors):
    session = Session()
    missing_name = 0
    missing_rating = 0
    missing_phone = 0
    missing_cert = 0
    for c in contractors:
        # Data cleaning
        c['name'] = c['name'].strip() if c['name'] else None
        c['certifications'] = json.dumps(c['certifications'] or [])
        # Data quality checks
        if not c['name']:
            missing_name += 1
        if not c['rating']:
            missing_rating += 1
        if not c['phone']:
            missing_phone += 1
        if not c['certifications'] or c['certifications'] == '[]':
            missing_cert += 1
        # Duplicate check
        if session.query(Contractor).filter_by(contractor_id=c['contractor_id']).first():
            continue
        contractor = Contractor(**c)
        session.add(contractor)
    session.commit()
    session.close()
    logging.info(f"{len(contractors)} records collected and inserted into the database")
    logging.info(f"Missing name: {missing_name}, missing rating: {missing_rating}, missing phone: {missing_phone}, missing certifications: {missing_cert}")

openai.api_key = os.environ.get("OPENAI_API_KEY")

INSIGHT_PROMPT = (
    "Based on the following contractor information, generate a concise, professional sales insight in English. Highlight their strengths, potential value, and possible sales approaches.\n"
    "Company Name: {name}\n"
    "Rating: {rating}\n"
    "Reviews: {reviews}\n"
    "Phone: {phone}\n"
    "City: {city}\n"
    "State: {state}\n"
    "Postal Code: {postal_code}\n"
    "Certifications: {certifications}\n"
    "Type: {type}\n"
)

def generate_insight(contractor):
    prompt = INSIGHT_PROMPT.format(**contractor)
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=200,
        temperature=0.7,
    )
    return response.choices[0].message.content.strip()

def update_insights():
    session = Session()
    contractors = session.query(Contractor).filter((Contractor.insight == None) | (Contractor.insight == "")).all()
    for c in contractors:
        contractor_dict = {
            "name": c.name or "",
            "rating": c.rating or "N/A",
            "reviews": c.reviews or "N/A",
            "phone": c.phone or "N/A",
            "city": c.city or "N/A",
            "state": c.state or "N/A",
            "postal_code": c.postal_code or "N/A",
            "certifications": c.certifications or "N/A",
            "type": c.type or "N/A",
        }
        try:
            insight = generate_insight(contractor_dict)
            c.insight = insight
            print(f"Insight generated: {c.name}")
        except Exception as e:
            print(f"Insight generation failed: {c.name}, Error: {e}")
    session.commit()
    session.close()

EVALUATION_PROMPT = (
    "You are a sales enablement expert. Please evaluate the following AI-generated sales insight for a contractor based on the contractor's information. Score the insight on a scale of 1-5 for each of the following criteria: relevance, actionability, accuracy, and clarity. Also, provide a brief comment.\n"
    "Contractor Info: {contractor_info}\n"
    "AI Insight: {insight}\n"
    "Respond in valid JSON format, use double quotes for all keys and string values, and do not include trailing commas.\n"
    "Example:\n"
    '{{"relevance": 5, "actionability": 4, "accuracy": 5, "clarity": 5, "comment": "This insight is actionable and relevant."}}'
)

def evaluate_insights():
    """Batch evaluate all contractors with an AI insight but no evaluation scores. Update the evaluation fields in the database."""
    import json
    import ast
    session = Session()
    contractors = session.query(Contractor).filter(
        Contractor.insight != None,
        (Contractor.relevance_score == None) | (Contractor.actionability_score == None) |
        (Contractor.accuracy_score == None) | (Contractor.clarity_score == None)
    ).all()
    for c in contractors:
        contractor_info = f"Name: {c.name}, Rating: {c.rating}, Reviews: {c.reviews}, Phone: {c.phone}, City: {c.city}, State: {c.state}, Postal Code: {c.postal_code}, Certifications: {c.certifications}, Type: {c.type}"
        prompt = EVALUATION_PROMPT.format(contractor_info=contractor_info, insight=c.insight)
        try:
            response = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=0.3,
            )
            result = response.choices[0].message.content.strip()
            try:
                result_dict = json.loads(result)
            except Exception:
                result_dict = ast.literal_eval(result)
            c.relevance_score = int(result_dict.get('relevance', 0))
            c.actionability_score = int(result_dict.get('actionability', 0))
            c.accuracy_score = int(result_dict.get('accuracy', 0))
            c.clarity_score = int(result_dict.get('clarity', 0))
            c.evaluation_comment = result_dict.get('comment', '')
            print(f"Evaluated: {c.name}")
        except Exception as e:
            print(f"Evaluation failed: {c.name}, Error: {e}")
    session.commit()
    session.close()

IMPROVED_INSIGHT_PROMPT = (
    "Based on the following contractor information, generate a concise, actionable, and differentiated sales insight in English. Avoid generic statements and focus on unique value or opportunities for engagement.\n"
    "Company Name: {name}\n"
    "Rating: {rating}\n"
    "Reviews: {reviews}\n"
    "Phone: {phone}\n"
    "City: {city}\n"
    "State: {state}\n"
    "Postal Code: {postal_code}\n"
    "Certifications: {certifications}\n"
    "Type: {type}\n"
)

def regenerate_low_score_insights():
    session = Session()
    contractors = session.query(Contractor).filter(
        (Contractor.relevance_score <= 2) |
        (Contractor.actionability_score <= 2) |
        (Contractor.accuracy_score <= 2) |
        (Contractor.clarity_score <= 2)
    ).all()
    for c in contractors:
        contractor_dict = {
            "name": c.name or "",
            "rating": c.rating or "N/A",
            "reviews": c.reviews or "N/A",
            "phone": c.phone or "N/A",
            "city": c.city or "N/A",
            "state": c.state or "N/A",
            "postal_code": c.postal_code or "N/A",
            "certifications": c.certifications or "N/A",
            "type": c.type or "N/A",
        }
        try:
            prompt = IMPROVED_INSIGHT_PROMPT.format(**contractor_dict)
            response = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=0.7,
            )
            improved_insight = response.choices[0].message.content.strip()
            c.insight = improved_insight
            print(f"Regenerated improved insight: {c.name}")
        except Exception as e:
            print(f"Insight regeneration failed: {c.name}, Error: {e}")
    session.commit()
    session.close()

BUSINESS_SUMMARY_PROMPT = (
    "Given the following contractor data, summarize their business scale and activity level. Highlight any recent major projects or news if available.\n"
    "Company Name: {name}\n"
    "Rating: {rating}\n"
    "Reviews: {reviews}\n"
    "City: {city}\n"
    "State: {state}\n"
    "Certifications: {certifications}\n"
    "Type: {type}\n"
)
SALES_TIP_PROMPT = (
    "Based on this contractor's profile, generate a personalized sales talking point and a recommended opening line for a sales call.\n"
    "Company Name: {name}\n"
    "Rating: {rating}\n"
    "Reviews: {reviews}\n"
    "City: {city}\n"
    "State: {state}\n"
    "Certifications: {certifications}\n"
    "Type: {type}\n"
)
RISK_ALERT_PROMPT = (
    "Analyze the contractor's recent ratings and reviews. If there are negative trends or risks, summarize them and suggest how a sales rep should address them.\n"
    "Company Name: {name}\n"
    "Rating: {rating}\n"
    "Reviews: {reviews}\n"
    "City: {city}\n"
    "State: {state}\n"
    "Certifications: {certifications}\n"
    "Type: {type}\n"
)
PRIORITY_SUGGESTION_PROMPT = (
    "Given the contractor's data, rate how high a priority they should be for sales outreach (High/Medium/Low) and explain why.\n"
    "Company Name: {name}\n"
    "Rating: {rating}\n"
    "Reviews: {reviews}\n"
    "City: {city}\n"
    "State: {state}\n"
    "Certifications: {certifications}\n"
    "Type: {type}\n"
)
NEXT_ACTION_PROMPT = (
    "Based on the contractor's profile, recommend the next best action for a sales rep (e.g., call, email, send brochure) and the best time to contact.\n"
    "Company Name: {name}\n"
    "Rating: {rating}\n"
    "Reviews: {reviews}\n"
    "City: {city}\n"
    "State: {state}\n"
    "Certifications: {certifications}\n"
    "Type: {type}\n"
)

def generate_multi_insights(contractor):
    prompts = [
        ("business_summary", BUSINESS_SUMMARY_PROMPT),
        ("sales_tip", SALES_TIP_PROMPT),
        ("risk_alert", RISK_ALERT_PROMPT),
        ("priority_suggestion", PRIORITY_SUGGESTION_PROMPT),
        ("next_action", NEXT_ACTION_PROMPT),
    ]
    results = {}
    for field, prompt_template in prompts:
        prompt = prompt_template.format(**contractor)
        try:
            response = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=0.7,
            )
            results[field] = response.choices[0].message.content.strip()
        except Exception as e:
            results[field] = f"[Error generating {field}: {e}]"
    return results

def update_multi_insights():
    session = Session()
    contractors = session.query(Contractor).filter(
        (Contractor.business_summary == None) | (Contractor.business_summary == "") |
        (Contractor.sales_tip == None) | (Contractor.sales_tip == "") |
        (Contractor.risk_alert == None) | (Contractor.risk_alert == "") |
        (Contractor.priority_suggestion == None) | (Contractor.priority_suggestion == "") |
        (Contractor.next_action == None) | (Contractor.next_action == "")
    ).all()
    for c in contractors:
        contractor_dict = {
            "name": c.name or "",
            "rating": c.rating or "N/A",
            "reviews": c.reviews or "N/A",
            "phone": c.phone or "N/A",
            "city": c.city or "N/A",
            "state": c.state or "N/A",
            "postal_code": c.postal_code or "N/A",
            "certifications": c.certifications or "N/A",
            "type": c.type or "N/A",
        }
        try:
            insights = generate_multi_insights(contractor_dict)
            c.business_summary = insights["business_summary"]
            c.sales_tip = insights["sales_tip"]
            c.risk_alert = insights["risk_alert"]
            c.priority_suggestion = insights["priority_suggestion"]
            c.next_action = insights["next_action"]
            print(f"Multi-insights generated: {c.name}")
        except Exception as e:
            print(f"Multi-insight generation failed: {c.name}, Error: {e}")
    session.commit()
    session.close()

def geocode_and_update_latlng():
    session = Session()
    geolocator = Nominatim(user_agent="gaf_sales_platform")
    contractors = session.query(Contractor).filter((Contractor.latitude == None) | (Contractor.longitude == None)).all()
    for c in contractors:
        address = f"{c.city or ''}, {c.state or ''}, {c.postal_code or ''}".strip(', ')
        try:
            location = geolocator.geocode(address, timeout=10)
            if location:
                c.latitude = location.latitude
                c.longitude = location.longitude
                print(f"Geocoded: {c.name} -> ({c.latitude}, {c.longitude})")
            else:
                print(f"Geocode failed: {c.name} ({address})")
        except Exception as e:
            print(f"Geocode error: {c.name} ({address}): {e}")
        time.sleep(1)  # avoid rate limit
    session.commit()
    session.close() 