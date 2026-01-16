import aiohttp
import logging
import urllib.parse
from utils import check_season_episode

class LaCaleService:
    def __init__(self, passkey):
        self.passkey = passkey
        self.base_url = "https://la-cale.space/api/external"

    async def search(self, query):
        if not self.passkey:
            return []

        # URL encodée
        encoded_query = urllib.parse.quote(query)
        # Endpoint: /api/external?passkey=...&q=...
        url = f"{self.base_url}?passkey={self.passkey}&q={encoded_query}"
        
        # Log avec passkey masquée
        log_url = url.replace(self.passkey, '***PASSKEY***')
        logging.info(f"LaCale Request: {log_url}")

        async with aiohttp.ClientSession(trust_env=True) as session:
            try:
                async with session.get(url, timeout=20) as response:
                    if response.status == 200:
                        data = await response.json()
                        # L'API retourne une liste d'objets directement selon l'OpenAPI spec
                        # schema: type: array, items: ExternalResult
                        results = data if isinstance(data, list) else []
                        
                        logging.info(f"LaCale found {len(results)} results for '{query}'")
                        
                        normalized = []
                        for res in results:
                            # Mapping des champs LaCale vers format interne
                            # Spec API:
                            # title, size (bytes), link (download), infoHash, category, seeders, leechers
                            
                            # La spec dit que 'link' appends /api/torrents/download/{{infoHash}} to app URL
                            # Donc c'est un lien direct de téléchargement
                            
                            item = {
                                "name": res.get("title"),
                                "size": res.get("size", 0),
                                "tracker_name": "LaCale",
                                "info_hash": res.get("infoHash"),
                                "magnet": None, # On n'a pas de magnet direct, mais infoHash suffisant pour debrid
                                "link": res.get("link"), # Lien de téléchargement .torrent
                                "source": "lacale",
                                "seeders": res.get("seeders"),
                                "leechers": res.get("leechers")
                            }
                            normalized.append(item)
                        return normalized
                    elif response.status in [401, 403]:
                        logging.error(f"LaCale Unauthorized/Forbidden. Check passkey.")
                    else:
                        logging.warning(f"LaCale Error {response.status}")
                        text = await response.text()
                        logging.warning(f"LaCale Body: {text[:200]}")
            except Exception as e:
                logging.error(f"LaCale Exception: {e}")
        return []

    async def search_movie(self, title, year):
        # Recherche combinée pour maximiser les chances
        queries = [f"{title} {year}", title]
        results = []
        
        seen_hashes = set()
        
        for q in queries:
            res_list = await self.search(q)
            for res in res_list:
                if res['info_hash'] not in seen_hashes:
                    results.append(res)
                    seen_hashes.add(res['info_hash'])
            
        return results

    async def search_series(self, title, season, episode):
        results = []
        seen_hashes = set()
        
        # SxxExx
        if season is not None and episode is not None:
            s_str = f"S{int(season):02d}"
            e_str = f"E{int(episode):02d}"
            q = f"{title} {s_str}{e_str}"
            
            res_list = await self.search(q)
            for res in res_list:
                # Filtrage supplémentaire côté client si besoin, mais la recherche est assez précise
                if res['info_hash'] not in seen_hashes:
                    results.append(res)
                    seen_hashes.add(res['info_hash'])
        
        # Saison Pack (Sxx)
        if season is not None:
             s_str = f"S{int(season):02d}"
             q = f"{title} {s_str}"
             
             res_list = await self.search(q)
             for res in res_list:
                if res['info_hash'] not in seen_hashes:
                    results.append(res)
                    seen_hashes.add(res['info_hash'])

        return results
