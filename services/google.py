from google_auth_oauthlib.flow import Flow

from config.settings import settings



def build_google_flow(active_redirect_uri: str, gmail_scopes: bool = False) -> Flow:
    client_config = {
        "web": {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "project_id": settings.GOOGLE_PROJECT_ID,
            "auth_uri": settings.GOOGLE_AUTH_URI,
            "token_uri": settings.GOOGLE_TOKEN_URI,
            "auth_provider_x509_cert_url": settings.GOOGLE_AUTH_PROVIDER_X509_CERT_URL,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "redirect_uris": settings.GOOGLE_REDIRECT_URIS,
        }
    }

    all_scopes = []
    all_scopes.extend(settings.GOOGLE_LOGIN_SCOPES)
    if gmail_scopes: all_scopes.extend(settings.GMAIL_OAUTH_SCOPES)

    flow = Flow.from_client_config(
        client_config=client_config,
        scopes=all_scopes
    )
    flow.redirect_uri = active_redirect_uri

    return flow