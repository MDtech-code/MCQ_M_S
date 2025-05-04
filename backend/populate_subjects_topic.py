import os
import django

# Set up Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
django.setup()

from apps.content.models import Subject, Topic

def populate_data():
    # List of subjects and their topics
    subjects_data = [
        {"name": "Mathematics", "topics": ["Algebra", "Calculus", "Geometry", "Trigonometry", "Statistics"]},
        {"name": "Physics", "topics": ["Mechanics", "Electricity", "Magnetism", "Thermodynamics", "Optics"]},
        {"name": "Chemistry", "topics": ["Organic Chemistry", "Inorganic Chemistry", "Physical Chemistry", "Biochemistry", "Analytical Chemistry"]},
        {"name": "Biology", "topics": ["Genetics", "Ecology", "Cell Biology", "Evolution", "Human Anatomy"]},
        {"name": "Computer Science", "topics": ["Programming", "Data Structures", "Algorithms", "Databases", "Networking"]},
        {"name": "History", "topics": ["Ancient History", "Medieval History", "Modern History", "World Wars", "Civilizations"]},
        {"name": "Geography", "topics": ["Physical Geography", "Human Geography", "Climatology", "Geomorphology", "Cartography"]},
        {"name": "English", "topics": ["Grammar", "Literature", "Writing Skills", "Vocabulary", "Poetry"]},
        {"name": "Economics", "topics": ["Microeconomics", "Macroeconomics", "International Trade", "Development Economics", "Finance"]},
        {"name": "Art", "topics": ["Painting", "Sculpture", "Drawing", "Art History", "Photography"]},
    ]

    # Populate subjects and topics
    for subject_data in subjects_data:
        subject, created = Subject.objects.get_or_create(name=subject_data["name"])
        for topic_name in subject_data["topics"]:
            Topic.objects.get_or_create(name=topic_name, subject=subject)

    print("Database populated with 10 subjects and 50 topics.")

if __name__ == "__main__":
    populate_data()