from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import computed_field

class Settings(BaseSettings):
    db_user:           str
    db_password:       str
    db_host:           str
    db_port:           int = 5432
    db_name:           str
    db_schema:         str = 'public'
    db_local_host:     str = 'localhost'
    db_local_password: str = ''
    env:               str = 'remote'
    stratz_api_key:    str
    stratz_url:        str = 'https://api.stratz.com/graphql'
    opendota_url:      str = 'https://api.opendota.com/api'

    model_config = SettingsConfigDict(
        env_file='.env', 
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='ignore' # Ignores extra variables in .env so it doesn't crash
    )

    @computed_field
    @property
    def database_url(self) -> str:
        host = self.db_local_host if self.env == 'local' else self.db_host
        pw = self.db_local_password if self.env == 'local' else self.db_password
        return f"postgresql+psycopg://{self.db_user}:{pw}@{host}:{self.db_port}/{self.db_name}?options=-csearch_path%3D{self.db_schema}"

settings = Settings()