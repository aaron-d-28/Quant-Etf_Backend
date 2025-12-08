from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str
    POSTGRES_PORT: str
    POSTGRES_DB: str

    KAFKA_BROKER: str
    KAFKA_TOPIC: str

    class Config:
        env_file = ".env"

settings = Settings()  # type: ignore
