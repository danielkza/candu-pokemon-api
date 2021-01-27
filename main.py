import requests
import re
import json
from urllib.parse import urljoin

from dataclasses import dataclass, asdict
from wsgiref.simple_server import make_server
from pyramid.config import Configurator
from pyramid.response import Response


POKE_API_BASE_URL = "https://pokeapi.co/api/v2/"
POKE_DESCRIPTION_LANGUAGE = "en"


@dataclass
class PokemonInfo:
    description: str
    image_url: str


def clean_description(description: str) -> str:
    return re.sub(r"[\n\x0c]", "", description)

def get_pokemon_info(name: str) -> PokemonInfo:
    poke_response = requests.get(urljoin(POKE_API_BASE_URL, "pokemon/" + name))
    poke_response.raise_for_status()

    poke_info = poke_response.json()
    species_url = poke_info["species"]["url"]

    species_response = requests.get(species_url)
    species_response.raise_for_status()
    species_info = species_response.json()

    description_lines = [
        entry["flavor_text"] for entry in species_info["flavor_text_entries"]
        if entry["language"]["name"] == POKE_DESCRIPTION_LANGUAGE
    ]
    description = clean_description(" ".join(description_lines))

    image_url = poke_info["sprites"]["front_default"]

    return PokemonInfo(description=description, image_url=image_url)


"""
GET /pokemon/{name} -> {"description": "", "image_url": ""}
"""


def get_pokemon_request(request):
    pokemon_name = request.matchdict['name']
    try:
        pokemon_info = get_pokemon_info(pokemon_name)
    except requests.RequestException:
        return Response(status=404)

    return Response(json=asdict(pokemon_info))


if __name__ == '__main__':
    with Configurator() as config:
        config.add_route('get_pokemon', '/pokemon/{name}')
        config.add_view(get_pokemon_request, route_name='get_pokemon')
        app = config.make_wsgi_app()

    server = make_server('0.0.0.0', 6543, app)
    server.serve_forever()