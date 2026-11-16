"""Google-only network boundary. Provider tokens never enter logs or durable storage."""

from typing import Any, cast
from urllib.parse import urlsplit

import httpx
from authlib.integrations.httpx_client import OAuth2Client  # type: ignore[import-untyped]
from joserfc import jwt
from joserfc.jwk import KeySet, KeySetSerialization

from akus.config import Settings

ISSUER = "https://accounts.google.com"
DISCOVERY = ISSUER + "/.well-known/openid-configuration"


class GoogleProvider:
    def __init__(self, settings: Settings):
        self.settings = settings

    def metadata(self) -> dict[str, Any]:
        with httpx.Client(timeout=10, follow_redirects=False) as client:
            response = client.get(DISCOVERY)
            response.raise_for_status()
            if len(response.content) > 100_000:
                raise ValueError("Discovery too large")
            data: dict[str, Any] = response.json()
        if data.get("issuer") != ISSUER:
            raise ValueError("Untrusted issuer")
        for key in ("authorization_endpoint", "token_endpoint", "jwks_uri"):
            parsed = urlsplit(data[key])
            if (
                parsed.scheme != "https"
                or parsed.hostname
                not in {"accounts.google.com", "oauth2.googleapis.com", "www.googleapis.com"}
                or parsed.username
                or parsed.fragment
            ):
                raise ValueError("Untrusted discovery endpoint")
        return data

    def client(self) -> OAuth2Client:
        return OAuth2Client(
            self.settings.google_client_id,
            self.settings.google_client_secret.get_secret_value(),
            scope="openid email profile",
            redirect_uri=self.settings.google_redirect_uri,
            code_challenge_method="S256",
            timeout=10,
            follow_redirects=False,
        )

    def authorization_url(self, state: str, nonce: str, verifier: str) -> str:
        metadata = self.metadata()
        with self.client() as client:
            url, _ = client.create_authorization_url(
                metadata["authorization_endpoint"],
                state=state,
                nonce=nonce,
                code_verifier=verifier,
                hd="cmrit.ac.in",
                prompt="select_account",
            )
        return str(url)

    def exchange(self, code: str, nonce: str, verifier: str) -> dict[str, Any]:
        metadata = self.metadata()
        with self.client() as client:
            token = client.fetch_token(
                metadata["token_endpoint"], code=code, code_verifier=verifier
            )
            response = client.request("GET", metadata["jwks_uri"], withhold_token=True)
            response.raise_for_status()
            if len(response.content) > 200_000:
                raise ValueError("JWKS too large")
            keys = response.json()
        return validate_token(str(token["id_token"]), keys, self.settings.google_client_id, nonce)


def validate_token(raw: str, jwks: dict[str, Any], client_id: str, nonce: str) -> dict[str, Any]:
    token = jwt.decode(
        raw, KeySet.import_key_set(cast(KeySetSerialization, jwks)), algorithms=["RS256"]
    )
    registry = jwt.JWTClaimsRegistry(
        leeway=30,
        iss={"essential": True, "values": [ISSUER, "accounts.google.com"]},
        aud={"essential": True, "value": client_id},
        exp={"essential": True},
        iat={"essential": True},
        sub={"essential": True},
        nonce={"essential": True, "value": nonce},
        email={"essential": True},
        hd={"essential": True, "value": "cmrit.ac.in"},
    )
    registry.validate(token.claims)
    claims = token.claims
    if claims.get("email_verified") is not True:
        raise ValueError("Email not verified")
    if not isinstance(claims["sub"], str) or len(claims["sub"]) > 255:
        raise ValueError("Invalid subject")
    email = claims["email"]
    if not isinstance(email, str) or len(email) > 254 or email.count("@") != 1:
        raise ValueError("Invalid email")
    if email.rsplit("@", 1)[1].lower() != "cmrit.ac.in":
        raise ValueError("Email outside approved institution")
    audience = claims["aud"]
    if (isinstance(audience, list) and len(audience) > 1) or "azp" in claims:
        if claims.get("azp") != client_id:
            raise ValueError("Wrong authorized party")
    return dict(claims, iss=ISSUER)
