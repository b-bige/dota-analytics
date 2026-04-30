from .base import Filter
from .patch import PatchFilter
from .league import LeagueFilter
from .teams import TeamsFilter
from .heroes import HeroesFilter
from .durations import DurationsFilter
from .dates import DatesFilter

FILTER_IDS = {
    'patch': 'patch-filter',
    'league': 'league-filter',
    'teams': 'teams-filter',
    'heroes': 'heroes-filter',
    'durations': 'durations-filter',
    'dates': 'date-filter',
}

FILTERS: list[Filter] = [
    PatchFilter(),
    LeagueFilter(),
    TeamsFilter(),
    HeroesFilter(),
    DurationsFilter(),
    DatesFilter(),
]

FILTER_MAP = {f.filter_name: f for f in FILTERS}

__all__ = ["Filter", "FILTERS", "FILTER_MAP", "FILTER_IDS"]