import sys
from google.cloud import firestore

# MUST hardcode project ID as string - do NOT use google.auth.default() or GOOGLE_CLOUD_PROJECT env var
PROJECT_ID = "qwiklabs-gcp-01-697898e2b788"

PLANT_SEED_DATA = [
    {
        "plant_id": "monstera-deliciosa",
        "name": "Monstera Deliciosa",
        "species": "Monstera deliciosa",
        "category": "Tropical",
        "light_requirement": "Bright, indirect light",
        "watering_schedule": "Water every 1-2 weeks, allowing soil to dry out between waterings",
        "price": 34.99,
        "stock_quantity": 15,
        "care_level": "Easy",
        "description": "Stunning tropical plant known for its iconic split leaves and vibrant green foliage.",
    },
    {
        "plant_id": "snake-plant",
        "name": "Snake Plant (Laurentii)",
        "species": "Dracaena trifasciata",
        "category": "Succulent",
        "light_requirement": "Low to bright indirect light",
        "watering_schedule": "Water every 2-3 weeks, drought tolerant",
        "price": 24.99,
        "stock_quantity": 20,
        "care_level": "Beginner",
        "description": "Extremely resilient air-purifying plant with upright sword-like yellow-bordered leaves.",
    },
    {
        "plant_id": "fiddle-leaf-fig",
        "name": "Fiddle Leaf Fig",
        "species": "Ficus lyrata",
        "category": "Indoor Tree",
        "light_requirement": "Bright, indirect light near a window",
        "watering_schedule": "Water weekly when top inch of soil feels dry",
        "price": 49.99,
        "stock_quantity": 8,
        "care_level": "Moderate",
        "description": "Dramatic indoor tree with large, violin-shaped glossy leaves.",
    },
    {
        "plant_id": "peace-lily",
        "name": "Peace Lily",
        "species": "Spathiphyllum",
        "category": "Flowering",
        "light_requirement": "Low to medium indirect light",
        "watering_schedule": "Water weekly, keep soil consistently moist",
        "price": 19.99,
        "stock_quantity": 12,
        "care_level": "Easy",
        "description": "Elegant flowering plant with deep green leaves and classic white spathes.",
    },
    {
        "plant_id": "succulent-trio",
        "name": "Mini Succulent Trio",
        "species": "Echeveria & Haworthia mix",
        "category": "Succulent",
        "light_requirement": "Bright direct to indirect sunlight",
        "watering_schedule": "Water every 2 weeks sparingly",
        "price": 14.99,
        "stock_quantity": 25,
        "care_level": "Beginner",
        "description": "A charming assortment of three hardy miniature succulents in ceramic pots.",
    },
]

def seed_database():
    print(f"Connecting to Firestore for project: {PROJECT_ID}...")
    db = firestore.Client(project=PROJECT_ID)
    plants_ref = db.collection("plants")

    for plant in PLANT_SEED_DATA:
        doc_id = plant["plant_id"]
        plants_ref.document(doc_id).set(plant)
        print(f"  [+] Seeded plant item: {plant['name']} ({doc_id})")

    print(f"Successfully seeded {len(PLANT_SEED_DATA)} plants to collection 'plants'!")

if __name__ == "__main__":
    seed_database()
