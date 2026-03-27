import requests
from loguru import logger
from utils.base_plugin import ListScraper
from utils.jellyfin import JellyfinClient


class Directors(ListScraper):

    _alias_ = "directors"

    def get_list(list_id, config=None):
        """
        list_id: a Jellyfin person ID for a director.
        Returns a single collection of all movies directed by that person.
        """
        if config is None:
            config = {}

        server_url = config["server_url"].rstrip("/")
        api_key = config["api_key"]
        user_id = config["user_id"]
        headers = {"X-Emby-Token": api_key}

        # Fetch director name
        person_res = requests.get(f"{server_url}/Users/{user_id}/Items/{list_id}", headers=headers)
        person_res.raise_for_status()
        director_name = person_res.json().get("Name", list_id)

        # Fetch all movies for this director
        params = {
            "enableTotalRecordCount": "false",
            "enableImages": "false",
            "Recursive": "true",
            "IncludeItemTypes": "Movie",
            "PersonIds": list_id,
            "PersonTypes": "Director",
            "fields": "ProviderIds,ProductionYear",
        }
        res = requests.get(
            f"{server_url}/Users/{user_id}/Items",
            headers=headers,
            params=params,
        )
        res.raise_for_status()

        movies = []
        for movie in res.json().get("Items", []):
            movies.append({
                "title": movie["Name"],
                "release_year": movie.get("ProductionYear"),
                "media_type": "movie",
                "imdb_id": movie.get("ProviderIds", {}).get("Imdb"),
            })

        logger.info(f"Director '{director_name}': found {len(movies)} movies")

        return {
            "name": director_name,
            "description": f"Films directed by {director_name}",
            "items": movies,
        }

    @staticmethod
    def get_list_ids(config: dict) -> list[str]:
        """
        Auto-discovers all directors in the Jellyfin library.
        Called by main.py when list_ids is empty.
        Returns a list of Jellyfin person IDs, one per director.
        """
        client = JellyfinClient(
            server_url=config["server_url"].rstrip("/"),
            api_key=config["api_key"],
            user_id=config["user_id"],
        )
        directors = client.get_all_directors()
        logger.info(f"Auto-discovered {len(directors)} directors")
        return [d["id"] for d in directors]
