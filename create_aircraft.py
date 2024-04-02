import json

from apps.general.models import Aircraft

command = """curl -d "" -H "Content-Type: application/json" https://www4.icao.int/doc8643/External/AircraftTypes >> type_of_aircraft.json"""


def main():
    rename = {
        "Designator": "type",
        "ModelFullName": "model",
        "AircraftDescription": "variant",
        "ManufacturerCode": "manufacturer",
        "Description": "description",
        "EngineType": "engine_type",
        "EngineCount": "engine_count",
        "WTC": "weakturbulence_category",
    }

    objects = list()
    cleaned_objects = list()
    with open("./type_of_aircraft.json", "r") as fl:
        for ac in json.load(fl):
            objects.append(Aircraft(**{rename[key]: value for key, value in ac.items() if key in rename}))
    for obj in objects:
        try:
            obj.full_clean()
            cleaned_objects.append(obj)
        except Exception:
            pass

    Aircraft.objects.bulk_create(cleaned_objects)


if __name__ == "__main__":
    main()
