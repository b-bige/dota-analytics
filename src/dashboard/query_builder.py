class QueryBuilder:
    def __init__(self, base_table='match_details md'):
        self.base_table = base_table
        self._joins = {}
        self._conditions = []
        self._having = []
        self._params = {}
        self._having_params = {}

    def copy(self):
        """Return a fresh copy with only the filter conditions/joins, not query-specific ones"""
        new_qb = QueryBuilder(self.base_table)
        new_qb._joins = self._joins.copy()
        new_qb._conditions = self._conditions.copy()
        new_qb._params = self._params.copy()
        new_qb._having = self._having.copy()
        new_qb._having_params = self._having_params.copy()
        return new_qb

    def join(self, alias, join_sql):
        """Add a join only if not already present"""
        if alias not in self._joins:
            self._joins[alias] = join_sql
        return self

    def where(self, condition, param_dict={}):
        self._conditions.append(condition)
        self._params.update(param_dict)
        return self
    
    def having(self, condition, param_dict={}):
        self._having.append(condition)
        self._having_params.update(param_dict)
        return self

    def build(self, select:str, group_by:str='', order_by:str='', extra_conditions:str='', extra_params:dict=None):
        extra_params = extra_params or {}
        joins = ' '.join(self._joins.values())

        where = 'WHERE 1=1'
        if self._conditions:
            where += ' AND ' + ' AND '.join(f'({c})' for c in self._conditions)
        if extra_conditions:
            where += f' AND ({extra_conditions})'  

        having = ''
        if self._having:
            having = 'HAVING ' + ' AND '.join(f'({h})' for h in self._having)  

        query = f'''
            SELECT {select}
            FROM {self.base_table}
            {joins}
            {where}
            {group_by}
            {having}
            {order_by}
        '''
        return query, self._params | self._having_params | extra_params
    
    @property
    def is_filtered(self):
        """True if any filters have been applied"""
        return len(self._conditions) > 0