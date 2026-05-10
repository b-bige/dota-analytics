from .base import Filter
import dash_mantine_components as dmc
from src.dashboard.query_builder import QueryBuilder
from src.dashboard.data_assets import HERO_LIST

class HeroesFilter(Filter):
    filter_name = 'heroes'
    component_id = 'heroes-filter'

    def parse_from_url(self, params):
        return params.get(self.filter_name, None)
    
    def apply_to_query(self, qb: QueryBuilder, value, exclude):
        if value:
            if value[0] and not exclude:
                qb.join('mp', 'INNER JOIN match_players mp ON mp.match_id = md.id')
                qb.join('hd', 'RIGHT JOIN hero_details hd ON hd.id = mp."heroId"')
                qb.where('hd."displayName" = ANY(:value)', {'value': value})
        return qb
    
    def to_url_params(self, value):
        return super().to_url_params(value)
    
    def get_data(self, **filters):
        return None
    
    def render(self, value, data):
        return dmc.MultiSelect(
            id='heroes-filter',
            label='Heroes',
            placeholder='Select Heroes',
            data=HERO_LIST,
            value=value,
            searchable=True
        )