from .base import Filter
import dash_mantine_components as dmc
from dash import no_update
from src.dashboard.query_builder import QueryBuilder

class TeamsFilter(Filter):
    filter_name = 'teams'
    component_id = 'teams-filter'

    def parse_from_url(self, params):
        return params.get(self.filter_name, None)
    
    def apply_to_query(self, qb: QueryBuilder, value, exclude):
        if value:
            if value[0] and not exclude:
                qb.join('radiant', 'LEFT JOIN team_details radiant ON radiant.id = md."radiantTeamId"')
                qb.join('dire', 'LEFT JOIN team_details dire ON dire.id = md."direTeamId"')
                if len(value) == 2:
                    qb.where(
                        '''
                        (radiant.name = :team_one_name AND dire.name = :team_two_name) 
                        OR 
                        (radiant.name = :team_two_name AND dire.name = :team_one_name)
                        ''',
                        {'team_one_name': value[0], 'team_two_name': value[1]}
                    )
                else:
                    qb.where('(radiant.name = ANY(:team_names)) OR (dire.name = ANY(:team_names))', {'team_names': value})
        return qb

    def to_url_params(self, value):
        return super().to_url_params(value)
    
    def get_data(self, **filters):
        qb = QueryBuilder()
        qb.join('tdr', 'INNER JOIN team_details tdr ON tdr.id = md."radiantTeamId"')
        qb.join('tdd', 'INNER JOIN team_details tdd ON tdd.id = md."direTeamId"')
        qb.where('tdr."isPro" = \'t\' AND tdd."isPro" = \'t\'')
        self.handle_filters(qb, **filters)
        q1, params1 = qb.build(select='DISTINCT tdr.name')
        q2, params2 = qb.copy().build(select='DISTINCT tdd.name')
        query = f'''
            {q1}
            UNION
            {q2}
            ORDER BY name ASC
        '''
        return [r[0] for r in self.db.select(query, params=params1 | params2)]
    
    def render(self, value, data):
        teams_placeholder = 'Select 2 To See Head-to-Head' if len(data) > 0 else 'No Pro Teams Found'
        return dmc.MultiSelect(
            id='teams-filter',
            label='Pro Teams',
            placeholder=teams_placeholder,
            data=data,
            value=value,
            searchable=True
        )
    
    def get_outputs(self, triggered_component_id, **filters) -> list:
        data = self.get_updated_data(triggered_component_id, **filters)
        if data is no_update:
            placeholder = no_update
        else:
            placeholder = 'Select 2 To See Head-to-Head' if data else 'No Pro Teams Found'
        return [placeholder, data]