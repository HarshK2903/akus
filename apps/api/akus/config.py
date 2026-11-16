from typing import Literal
from urllib.parse import urlsplit

from cryptography.fernet import Fernet
from pydantic import SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="AKUS_", env_file=".env", extra="ignore", hide_input_in_errors=True
    )
    env: Literal["local", "test", "production"] = "local"
    demo_enabled: bool = False
    database_url: str = "postgresql+psycopg://akus_demo:akus_demo@127.0.0.1:55432/akus"
    public_origin: str = "http://127.0.0.1:5173"
    institution_label: str = "Local demonstration institution"
    google_client_id: str = ""
    google_client_secret: SecretStr = SecretStr("")
    google_redirect_uri: str = ""
    session_key: SecretStr = SecretStr("")

    @property
    def google_enabled(self) -> bool:
        return bool(
            self.google_client_id
            and self.google_client_secret.get_secret_value()
            and self.google_redirect_uri
            and self.session_key.get_secret_value()
        )

    @property
    def secure_cookies(self) -> bool:
        return self.public_origin.startswith("https://")

    @model_validator(mode="after")
    def validate_boundary(self) -> "Settings":
        if not self.database_url.startswith("postgresql+psycopg://"):
            raise ValueError("PostgreSQL with Psycopg is required")
        parsed = urlsplit(self.public_origin)
        loopback = parsed.hostname in {"127.0.0.1", "localhost"}
        if parsed.path or parsed.query or parsed.fragment or parsed.username:
            raise ValueError("Public origin must contain only scheme and authority")
        if parsed.scheme != "https" and not (
            self.env != "production" and loopback and parsed.scheme == "http"
        ):
            raise ValueError("HTTPS is required except local loopback development")
        if self.demo_enabled and (not loopback or self.env == "production"):
            raise ValueError("Demo identity is restricted to a loopback browser origin")
        configured = [
            bool(self.google_client_id),
            bool(self.google_client_secret.get_secret_value()),
            bool(self.google_redirect_uri),
            bool(self.session_key.get_secret_value()),
        ]
        if any(configured) and not all(configured):
            raise ValueError(
                "OIDC configuration must supply client ID, secret, redirect URI and session key together"
            )
        if self.google_enabled:
            if self.demo_enabled:
                raise ValueError("Institutional OIDC requires demo access disabled")
            if self.google_redirect_uri != self.public_origin + "/api/v1/auth/google/callback":
                raise ValueError("Google redirect URI must match the public same-origin callback")
            Fernet(self.session_key.get_secret_value().encode())
        if self.env == "production" and (
            not self.google_enabled or "akus_demo" in self.database_url
        ):
            raise ValueError(
                "Production requires institutional OIDC and a private database credential"
            )
        return self
