"""Pluggable sign-in providers (Google, Meta).

Checkout and orders never talk to a provider directly: a provider only turns an OAuth callback into an Identity,
and app.link_social_identity() attaches that identity to the customer record with the same email, so orders placed
through guest checkout show up in the signed-in account.

To go live with a provider: fill its keys in .env, implement authorize_url() and fetch_identity(), set implemented = True.
"""
from dataclasses import dataclass

from utils.config import env_value


@dataclass
class Identity:
    provider: str
    provider_user_id: str
    email: str
    email_verified: bool
    name: str = ''


class AuthProvider:
    name = ''
    label = ''
    env_keys = ()
    implemented = False  # flip once authorize_url / fetch_identity are written and tested

    def missing_keys(self):
        return [k for k in self.env_keys if not env_value(k)]

    @property
    def enabled(self):
        return self.implemented and not self.missing_keys()

    def disabled_reason(self):
        if self.missing_keys():
            return f"{', '.join(self.missing_keys())} not set"
        if not self.implemented:
            return 'provider not implemented yet'
        return ''

    def authorize_url(self, state, redirect_uri):
        raise NotImplementedError

    def fetch_identity(self, code, redirect_uri):
        """Exchange the OAuth code for an Identity. Must only report email_verified=True when the provider says so."""
        raise NotImplementedError


class GoogleProvider(AuthProvider):
    name = 'google'
    label = 'Google'
    env_keys = ('GOOGLE_CLIENT_ID', 'GOOGLE_CLIENT_SECRET')
    # Later: authorize at https://accounts.google.com/o/oauth2/v2/auth (scope "openid email profile"),
    # exchange at https://oauth2.googleapis.com/token, read email/email_verified/sub from the ID token.


class MetaProvider(AuthProvider):
    name = 'meta'
    label = 'Facebook / Instagram'
    env_keys = ('META_APP_ID', 'META_APP_SECRET')
    # Later: Facebook Login dialog + Graph API /me?fields=id,name,email. Meta does not always return an email;
    # fetch_identity must reject accounts without one, since email is the customer key.


PROVIDERS = {p.name: p for p in (GoogleProvider(), MetaProvider())}
