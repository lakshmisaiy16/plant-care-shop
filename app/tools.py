import base64
import os
import uuid
import requests
from dotenv import load_dotenv
from google import genai
from google.adk.tools import ToolContext
from google.cloud import firestore, storage
from google.genai import types

load_dotenv()


# MUST hardcode project ID and Cloud Storage bucket as strings
PROJECT_ID = "qwiklabs-gcp-01-697898e2b788"
BUCKET_NAME = "plant-care-shop-media-697898e2b788"



def _get_firestore_db():
    return firestore.Client(project=PROJECT_ID)


def get_plant_details(plant_id: str) -> dict:
    """Fetch details for a specific plant from the Firestore greenhouse inventory.

    Args:
        plant_id: The unique identifier or slug of the plant (e.g., 'monstera-deliciosa', 'snake-plant').

    Returns:
        A dictionary containing plant details or an error message.
    """
    try:
        db = _get_firestore_db()
        doc = db.collection("plants").document(plant_id).get()
        if doc.exists:
            return doc.to_dict()
        return {"error": f"Plant with ID '{plant_id}' not found in greenhouse inventory."}
    except Exception as e:
        return {"error": f"Failed to fetch plant details: {str(e)}"}


def search_plants(category: str = "", max_price: float = None) -> list:
    """Search and filter plants in the Firestore greenhouse catalog.

    Args:
        category: Optional category filter (e.g. 'Tropical', 'Succulent', 'Indoor Tree', 'Flowering').
        max_price: Optional maximum price limit.

    Returns:
        A list of matching plant items.
    """
    try:
        db = _get_firestore_db()
        query_ref = db.collection("plants")
        docs = query_ref.stream()
        results = []
        for doc in docs:
            plant = doc.to_dict()
            if category and category.lower() not in plant.get("category", "").lower():
                continue
            if max_price is not None and plant.get("price", 0.0) > float(max_price):
                continue
            results.append(plant)
        return results
    except Exception as e:
        return [{"error": f"Failed to search plants: {str(e)}"}]


def add_or_update_plant(
    plant_id: str,
    name: str,
    category: str,
    light_requirement: str,
    watering_schedule: str,
    price: float,
    stock_quantity: int,
    care_level: str = "Easy",
    description: str = "",
) -> dict:
    """Add a new plant or update an existing plant in the Firestore greenhouse catalog.

    Args:
        plant_id: Unique identifier for the plant (slug format like 'calathea-orbifolia').
        name: Common name of the plant.
        category: Plant category (e.g. 'Tropical', 'Succulent', 'Flowering', 'Fern').
        light_requirement: Lighting instructions.
        watering_schedule: Watering instructions.
        price: Price in USD.
        stock_quantity: Available stock quantity.
        care_level: Difficulty level ('Beginner', 'Easy', 'Moderate', 'Expert').
        description: Short description of the plant.

    Returns:
        Status dictionary confirming the update.
    """
    try:
        db = _get_firestore_db()
        plant_data = {
            "plant_id": plant_id,
            "name": name,
            "category": category,
            "light_requirement": light_requirement,
            "watering_schedule": watering_schedule,
            "price": float(price),
            "stock_quantity": int(stock_quantity),
            "care_level": care_level,
            "description": description,
        }
        db.collection("plants").document(plant_id).set(plant_data)
        return {
            "status": "success",
            "message": f"Successfully updated plant '{name}' ({plant_id}).",
            "plant": plant_data,
        }
    except Exception as e:
        return {"error": f"Failed to update plant: {str(e)}"}


def diagnose_plant_health(symptoms: str, plant_name: str = "") -> dict:
    """Diagnose plant health problems based on observed symptoms.

    Args:
        symptoms: Description of the observed symptoms (e.g. 'yellowing leaves', 'brown spots', 'drooping').
        plant_name: Optional name of the plant being diagnosed.

    Returns:
        A dictionary containing the diagnostic evaluation, likely cause, and recommended care treatment.
    """
    symptoms_lower = symptoms.lower()

    if "yellow" in symptoms_lower or "soft" in symptoms_lower:
        cause = "Overwatering or Poor Drainage"
        recommendation = (
            "Allow the top 2 inches of soil to dry out completely. Ensure pot has drainage holes."
        )
        severity = "Moderate"
    elif "brown" in symptoms_lower or "dry" in symptoms_lower or "crispy" in symptoms_lower:
        cause = "Underwatering or Low Humidity"
        recommendation = (
            "Water thoroughly until it drains from the bottom. Increase ambient humidity or mist leaves."
        )
        severity = "Low to Moderate"
    elif "spot" in symptoms_lower or "patch" in symptoms_lower:
        cause = "Fungal Spot or Water Quality Issue"
        recommendation = (
            "Avoid getting water on leaves when watering. Prune severely affected leaves and use filtered water."
        )
        severity = "Moderate"
    elif "droop" in symptoms_lower or "wilt" in symptoms_lower:
        cause = "Moisture Stress (Check Soil)"
        recommendation = (
            "Check soil moisture: if dry, water deeply; if soggy, inspect roots for root rot."
        )
        severity = "Moderate"
    elif "white" in symptoms_lower or "web" in symptoms_lower or "bug" in symptoms_lower or "pest" in symptoms_lower:
        cause = "Pest Infestation (Spider Mites or Mealybugs)"
        recommendation = (
            "Isolate plant immediately. Wipe leaves with neem oil or insecticidal soap spray."
        )
        severity = "High"
    else:
        cause = "General Environmental / Nutrient Stress"
        recommendation = (
            "Check lighting levels, ensure consistent watering, and apply balanced indoor plant fertilizer during growing season."
        )
        severity = "Low"

    return {
        "plant_name": plant_name or "Unspecified Plant",
        "symptoms_reported": symptoms,
        "possible_cause": cause,
        "severity": severity,
        "recommended_action": recommendation,
    }


def lookup_botanical_taxonomy(plant_name: str) -> dict:
    """Lookup official botanical taxonomy and scientific classification for a plant species.
    Reads optional PERENUAL_API_KEY environment variable if present; otherwise queries GBIF Botanical Species API.

    Args:
        plant_name: Common or scientific plant name (e.g. 'Monstera deliciosa', 'Ficus lyrata', 'Spathiphyllum').

    Returns:
        A dictionary containing scientific classification (kingdom, family, genus, species, taxonomic status).
    """
    api_key = os.environ.get("PERENUAL_API_KEY")
    if api_key:
        try:
            url = f"https://perenual.com/api/species-list?key={api_key}&q={plant_name}"
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("data"):
                    item = data["data"][0]
                    return {
                        "source": "Perenual API",
                        "common_name": item.get("common_name"),
                        "scientific_name": item.get("scientific_name", []),
                        "watering": item.get("watering"),
                        "sunlight": item.get("sunlight"),
                    }
        except Exception:
            pass  # Fallback to GBIF API

    try:
        url = f"https://api.gbif.org/v1/species/match?name={plant_name}"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("matchType") != "NONE":
                return {
                    "source": "GBIF Botanical Species API",
                    "scientific_name": data.get("scientificName"),
                    "canonical_name": data.get("canonicalName"),
                    "kingdom": data.get("kingdom"),
                    "family": data.get("family"),
                    "genus": data.get("genus"),
                    "species": data.get("species"),
                    "taxonomic_status": data.get("status"),
                    "confidence": data.get("confidence"),
                }
        return {"error": f"No botanical taxonomy record found for '{plant_name}'."}
    except Exception as e:
        return {"error": f"Botanical API request failed: {str(e)}"}


def geocode_address(address: str) -> dict:
    """Convert a human-readable address into geographical coordinates (latitude and longitude) using Google Maps Geocoding API.

    Args:
        address: The location address to geocode (e.g. '1600 Amphitheatre Pkwy, Mountain View, CA' or 'San Francisco, CA').

    Returns:
        A dictionary containing the formatted address and location coordinates (latitude, longitude).
    """
    api_key = os.environ.get("GOOGLE_MAPS_API_KEY")
    if not api_key:
        return {"error": "GOOGLE_MAPS_API_KEY environment variable is not set."}

    try:
        url = "https://maps.googleapis.com/maps/api/geocode/json"
        params = {"address": address, "key": api_key}
        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("status") == "OK" and data.get("results"):
                result = data["results"][0]
                location = result.get("geometry", {}).get("location", {})
                return {
                    "address": result.get("formatted_address"),
                    "location": {
                        "latitude": location.get("lat"),
                        "longitude": location.get("lng"),
                    },
                }
            return {
                "error": f"Geocoding failed with status '{data.get('status')}': {data.get('error_message', 'No results found.')}"
            }
        return {"error": f"Geocoding HTTP error {resp.status_code}: {resp.text}"}
    except Exception as e:
        return {"error": f"Geocoding request failed: {str(e)}"}


def find_nearby_places(
    latitude: float,
    longitude: float,
    place_type: str = "florist",
    radius_meters: float = 5000.0,
) -> list:
    """Find nearby points of interest of a given type near specified coordinates using Google Places API (New).

    Args:
        latitude: Center point latitude.
        longitude: Center point longitude.
        place_type: Type of place to search for (e.g. 'florist', 'plant_nursery', 'garden_center', 'store').
        radius_meters: Search radius in meters (default 5000.0 meters).

    Returns:
        A list of nearby places with name, address, and location coordinates.
    """
    api_key = os.environ.get("GOOGLE_MAPS_API_KEY")
    if not api_key:
        return [{"error": "GOOGLE_MAPS_API_KEY environment variable is not set."}]

    try:
        url = "https://places.googleapis.com/v1/places:searchNearby"
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": api_key,
            "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.location",
        }
        body = {
            "includedTypes": [place_type],
            "maxResultCount": 5,
            "locationRestriction": {
                "circle": {
                    "center": {
                        "latitude": float(latitude),
                        "longitude": float(longitude),
                    },
                    "radius": float(radius_meters),
                }
            },
        }
        resp = requests.post(url, headers=headers, json=body, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            results = []
            for place in data.get("places", []):
                results.append(
                    {
                        "name": place.get("displayName", {}).get("text", ""),
                        "address": place.get("formattedAddress", ""),
                        "location": place.get("location", {}),
                    }
                )
            return results
        return [{"error": f"Places API HTTP error {resp.status_code}: {resp.text}"}]
    except Exception as e:
        return [{"error": f"Places API request failed: {str(e)}"}]


def generate_plant_image(prompt: str, tool_context: ToolContext) -> dict:
    """Generate an image for a plant, flower, or greenhouse item in the shop domain using the gemini-3.1-flash-lite-image model in the global region.
    Saves the image as an artifact for the Playground's Artifacts panel and uploads the image bytes directly to Cloud Storage.

    Args:
        prompt: Description of the plant or greenhouse item to generate an image for (e.g. 'A vibrant Monstera Deliciosa with glossy leaves in a ceramic pot').
        tool_context: ADK ToolContext instance injected by the framework.

    Returns:
        A dictionary containing the image filename, prompt, and public Cloud Storage https URL.
    """
    try:
        genai_client = genai.Client(
            vertexai=True,
            location="global",
            project=PROJECT_ID,
        )

        full_prompt = f"A high quality realistic photograph of {prompt}, greenhouse plant shop catalog item"
        response = genai_client.models.generate_content(
            model="gemini-3.1-flash-lite-image",
            contents=full_prompt,
        )

        image_bytes = None
        mime_type = "image/jpeg"

        if response.candidates and response.candidates[0].content.parts:
            for part in response.candidates[0].content.parts:
                if part.inline_data:
                    image_bytes = part.inline_data.data
                    mime_type = part.inline_data.mime_type or "image/jpeg"
                    break

        if not image_bytes:
            return {"error": "No image data was returned by the gemini-3.1-flash-lite-image model."}

        filename = f"plant_{uuid.uuid4().hex[:8]}.jpg"

        # (1) Save artifact with tool_context.save_artifact for Playground Artifacts panel
        artifact_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
        tool_context.save_artifact(filename=filename, artifact=artifact_part)

        # (2) Upload image bytes directly to public Cloud Storage bucket (without writing to local file)
        storage_client = storage.Client(project=PROJECT_ID)
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(filename)
        blob.upload_from_string(image_bytes, content_type=mime_type)

        public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{filename}"

        return {
            "status": "success",
            "prompt": prompt,
            "filename": filename,
            "public_url": public_url,
        }
    except Exception as e:
        return {"error": f"Failed to generate plant image: {str(e)}"}


def generate_plant_video(prompt: str, tool_context: ToolContext) -> dict:
    """Generate a short video for a plant, flower, or greenhouse item in the shop domain using the gemini-omni-flash-preview model in the global region.
    Saves the video as an artifact for the Playground's Artifacts panel using tool_context.save_artifact and uploads the video bytes directly to the public Cloud Storage bucket without saving locally.

    Args:
        prompt: Description of the plant or greenhouse item to generate a short video for (e.g. 'A time-lapse video of a flowering orchid sprouting').
        tool_context: ADK ToolContext instance injected by the framework.

    Returns:
        A dictionary containing the video filename, prompt, and public Cloud Storage https URL.
    """
    try:
        genai_client = genai.Client(
            vertexai=True,
            location="global",
            project=PROJECT_ID,
        )

        full_prompt = f"A short video of {prompt}, plant care and greenhouse shop item"
        resp = genai_client.interactions.create(
            model="gemini-omni-flash-preview",
            input=full_prompt,
        )

        if not resp.output_video or not resp.output_video.data:
            return {"error": "No video data returned by gemini-omni-flash-preview."}

        video_data = resp.output_video.data
        if isinstance(video_data, str):
            video_bytes = base64.b64decode(video_data)
        else:
            video_bytes = video_data

        filename = f"plant_video_{uuid.uuid4().hex[:8]}.mp4"
        mime_type = "video/mp4"

        # (1) Save artifact with tool_context.save_artifact so it shows up in Playground's Artifacts panel
        artifact_part = types.Part.from_bytes(data=video_bytes, mime_type=mime_type)
        tool_context.save_artifact(filename=filename, artifact=artifact_part)

        # (2) Upload video bytes directly to public Cloud Storage bucket (without writing to a local file)
        storage_client = storage.Client(project=PROJECT_ID)
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(filename)
        blob.upload_from_string(video_bytes, content_type=mime_type)

        public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{filename}"

        return {
            "status": "success",
            "prompt": prompt,
            "filename": filename,
            "public_url": public_url,
        }
    except Exception as e:
        return {"error": f"Failed to generate plant video: {str(e)}"}






