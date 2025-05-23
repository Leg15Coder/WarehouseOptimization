from pydantic import BaseSettings, SecretStr


class Settings(BaseSettings):
    dbname: SecretStr
    dbuser: SecretStr
    dbpassword: SecretStr
    dbhost: SecretStr
    dbport: SecretStr
    wsauth: SecretStr

    class Config:
        env_file = 'env/config.env'
        env_file_encoding = 'utf-8'


config = Settings()
