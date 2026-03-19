from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://postgres:postgres@localhost/ledgerpro"
    app_name: str = "LedgerPro - Double Entry Accounting"
    debug: bool = True

    class Config:
        env_file = ".env"


settings = Settings()
