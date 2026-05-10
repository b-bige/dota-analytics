from src.database import DatabaseManager

db = DatabaseManager()

HERO_DATA = db.select('SELECT id, "displayName" FROM hero_details')
HERO_DICT = {r[1]: r[0] for r in HERO_DATA}
HERO_LIST = sorted([r[1] for r in HERO_DATA])

PATCH_DATA = db.select('SELECT DISTINCT id, name FROM patches ORDER BY name DESC')
PATCH_DICT = {r[1]: r[0] for r in PATCH_DATA}
PATCH_LIST = [r[1] for r in PATCH_DATA]