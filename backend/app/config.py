from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[2]

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(ROOT / '.env'), extra='ignore')
    app_env: Literal['development','production','test'] = 'development'
    public_origin: str = 'http://localhost:5173'
    database_url: str = f'sqlite:///{ROOT / "data/human-fluid.db"}'
    cookie_secure: bool = False
    session_days: int = Field(90,ge=1,le=365)
    ai_provider: str = 'disabled'
    ai_enabled: bool = False
    ai_base_url: str = ''
    ai_model: str = ''
    ai_api_key: str = ''
    ai_cap_verified: bool = False
    ai_max_input_tokens: int = Field(6000,ge=256,le=32000)
    ai_max_output_tokens: int = Field(1500,ge=1,le=8192)
    ai_grant_requests_per_minute: int = Field(4,ge=0,le=1000000000)
    ai_grant_requests_per_day: int = Field(30,ge=0,le=1000000000)
    ai_global_requests_per_day: int = Field(100,ge=0,le=1000000000)
    ai_global_tokens_per_day: int = Field(750000,ge=0,le=1000000000)
    ai_grant_tokens_per_day: int = Field(225000,ge=0,le=1000000000)

    @field_validator('public_origin')
    @classmethod
    def normalize_public_origin(cls, value: str) -> str:
        origin = urlsplit(value.strip())
        if (
            origin.scheme not in ('http', 'https')
            or not origin.hostname
            or origin.username is not None
            or origin.password is not None
            or origin.path not in ('', '/')
            or origin.query
            or origin.fragment
            or any(char.isspace() for char in origin.netloc)
        ):
            raise ValueError('PUBLIC_ORIGIN must be an HTTP(S) origin without credentials, a path, query, or fragment.')
        host = origin.hostname.encode('idna').decode('ascii').lower()
        if ':' in host:
            host = f'[{host}]'
        port = origin.port
        if port == 0:
            raise ValueError('PUBLIC_ORIGIN must use a nonzero port.')
        default_port = 443 if origin.scheme == 'https' else 80
        suffix = f':{port}' if port is not None and port != default_port else ''
        return f'{origin.scheme}://{host}{suffix}'

    @property
    def allowed_origins(self) -> frozenset[str]:
        origins = {self.public_origin}
        configured = urlsplit(self.public_origin)
        loopback_hosts = ('localhost', '127.0.0.1', '::1')
        if (
            self.app_env == 'development'
            and configured.scheme == 'http'
            and configured.hostname in loopback_hosts
        ):
            # Both shipped local entry points work through either loopback name.
            # Never derive trust from Host, Origin, or forwarding headers.
            ports = {5173, 8000, configured.port or 80}
            for host in loopback_hosts:
                authority = f'[{host}]' if ':' in host else host
                for port in ports:
                    suffix = f':{port}' if port != 80 else ''
                    origins.add(f'http://{authority}{suffix}')
        return frozenset(origins)

    def validate_runtime(self):
        if self.app_env == 'production' and (not self.cookie_secure or not self.public_origin.startswith('https://')):
            raise RuntimeError('Production requires Secure cookies and an HTTPS PUBLIC_ORIGIN.')
        if self.ai_provider not in ('disabled', 'local', 'cloud'):
            raise RuntimeError('Unknown AI_PROVIDER')
        if self.ai_provider == 'cloud' and self.ai_enabled and not self.ai_cap_verified:
            raise RuntimeError('Funded cloud mode requires operator-verified output cap semantics.')
        if self.ai_provider == 'local' and self.ai_api_key:
            raise RuntimeError('Local mode must not carry a funded cloud key.')

settings = Settings()
