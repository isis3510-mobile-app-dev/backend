# seed_vaccines.py
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()

from api.models import Vaccine

vaccines_data = [
    # APPLY TO BOTH

        {
        "schema": 1,
        "name": "Rabies",
        "species": ["dog", "cat"],
        "product_name": "Nobivac Rabies",
        "manufacturer": "MSD Animal Health",
        "interval_days": 365,
        "description": "Protects against the rabies virus. Legally required in most countries.",
    },
    # DOG VACCINES
    {
        "schema": 1,
        "name": "Distemper",
        "species": ["dog"],
        "product_name": "Nobivac DHPPi",
        "manufacturer": "MSD Animal Health",
        "interval_days": 365,
        "description": "Protects against canine distemper virus. Part of the core polyvalent vaccine.",
    },
    {
        "schema": 1,
        "name": "Parvovirus",
        "species": ["dog"],
        "product_name": "Nobivac DHPPi",
        "manufacturer": "MSD Animal Health",
        "interval_days": 365,
        "description": "Protects against canine parvovirus, highly contagious and often fatal.",
    },
    {
        "schema": 1,
        "name": "Adenovirus (Hepatitis)",
        "species": ["dog"],
        "product_name": "Nobivac DHPPi",
        "manufacturer": "MSD Animal Health",
        "interval_days": 365,
        "description": "Protects against infectious canine hepatitis caused by adenovirus type 1 and 2.",
    },
    {
        "schema": 1,
        "name": "Parainfluenza",
        "species": ["dog"],
        "product_name": "Nobivac DHPPi",
        "manufacturer": "MSD Animal Health",
        "interval_days": 365,
        "description": "Protects against parainfluenza virus, one of the main agents of kennel cough.",
    },
    # Recommended 
    {
        "schema": 1,
        "name": "Leptospirosis",
        "species": ["dog"],
        "product_name": "Nobivac Lepto 4",
        "manufacturer": "MSD Animal Health",
        "interval_days": 365,
        "description": "Protects against 4 Leptospira serogroups. Important for dogs with access to water or rural areas.",
    },
    {
        "schema": 1,
        "name": "Bordetella (Kennel Cough)",
        "species": ["dog"],
        "product_name": "Nobivac KC",
        "manufacturer": "MSD Animal Health",
        "interval_days": 180,
        "description": "Protects against Bordetella bronchiseptica. Recommended for dogs that frequent parks or daycares.",
    },
    {
        "schema": 1,
        "name": "Canine Coronavirus",
        "species": ["dog"],
        "product_name": "Vanguard CCV",
        "manufacturer": "Zoetis",
        "interval_days": 365,
        "description": "Protects against canine enteric coronavirus, which causes gastroenteritis.",
    },
    # Optional
    {
        "schema": 1,
        "name": "Leishmaniasis",
        "species": ["dog"],
        "product_name": "CaniLeish",
        "manufacturer": "Virbac",
        "interval_days": 365,
        "description": "Protects against Leishmania infantum transmitted by sandflies. Recommended in endemic areas.",
    },
    {
        "schema": 1,
        "name": "Lyme Disease (Borreliosis)",
        "species": ["dog"],
        "product_name": "Nobivac Lyme",
        "manufacturer": "MSD Animal Health",
        "interval_days": 365,
        "description": "Protects against Borrelia burgdorferi transmitted by ticks. Recommended in wooded areas.",
    },

    # CAT VACCINES

    # Required 
    {
        "schema": 1,
        "name": "Feline Panleukopenia (FPV)",
        "species": ["cat"],
        "product_name": "Nobivac Tricat Trio",
        "manufacturer": "MSD Animal Health",
        "interval_days": 365,
        "description": "Protects against feline panleukopenia virus (feline parvovirus). Highly contagious and often fatal.",
    },
    {
        "schema": 1,
        "name": "Feline Herpesvirus (FHV-1)",
        "species": ["cat"],
        "product_name": "Nobivac Tricat Trio",
        "manufacturer": "MSD Animal Health",
        "interval_days": 365,
        "description": "Protects against feline herpesvirus type 1, a major cause of feline upper respiratory disease.",
    },
    {
        "schema": 1,
        "name": "Feline Calicivirus (FCV)",
        "species": ["cat"],
        "product_name": "Nobivac Tricat Trio",
        "manufacturer": "MSD Animal Health",
        "interval_days": 365,
        "description": "Protects against feline calicivirus, which causes respiratory disease and oral ulcers.",
    },
    # Recommended 
    {
        "schema": 1,
        "name": "Feline Leukemia Virus (FeLV)",
        "species": ["cat"],
        "product_name": "Nobivac FeLV",
        "manufacturer": "MSD Animal Health",
        "interval_days": 365,
        "description": "Protects against feline leukemia virus. Recommended for cats with outdoor access.",
    },
    {
        "schema": 1,
        "name": "Feline Chlamydiosis",
        "species": ["cat"],
        "product_name": "Nobivac Forcat",
        "manufacturer": "MSD Animal Health",
        "interval_days": 365,
        "description": "Protects against Chlamydophila felis, which causes conjunctivitis and respiratory disease.",
    },
    # Optional / exposure-based 
    {
        "schema": 1,
        "name": "Feline Immunodeficiency Virus (FIV)",
        "species": ["cat"],
        "product_name": "Fel-O-Vax FIV",
        "manufacturer": "Boehringer Ingelheim",
        "interval_days": 365,
        "description": "Protects against feline immunodeficiency virus. Recommended for outdoor cats.",
    },
    {
        "schema": 1,
        "name": "Feline Infectious Peritonitis (FIP)",
        "species": ["cat"],
        "product_name": "Primucell FIP",
        "manufacturer": "Zoetis",
        "interval_days": 365,
        "description": "Protects against feline coronavirus that causes FIP. Recommended for multi-cat households.",
    },
    {
        "schema": 1,
        "name": "Bordetella (Cat)",
        "species": ["cat"],
        "product_name": "Protex-Bb",
        "manufacturer": "Elanco",
        "interval_days": 365,
        "description": "Protects against Bordetella bronchiseptica in cats. Recommended for shelters or high-density environments.",
    },
]


def run(clear=False):
    if clear:
        count = Vaccine.objects.count()
        Vaccine.objects.all().delete()
        print(f"Deleted {count} existing vaccines")

    created = 0
    skipped = 0
    for data in vaccines_data:
        _, was_created = Vaccine.objects.get_or_create(
            name=data["name"],
            species=data["species"],
            defaults=data,
        )
        if was_created:
            print(f"  Created : {data['name']} ({', '.join(data['species'])})")
            created += 1
        else:
            print(f"  Skipped : {data['name']} ({', '.join(data['species'])})")
            skipped += 1

    print(f"\nDone — {created} created, {skipped} skipped")


if __name__ == "__main__":
    import sys
    clear = "--clear" in sys.argv
    run(clear=clear)