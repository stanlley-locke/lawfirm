"""SQLite Cloud helpers: native driver URI builder and Weblite REST client."""
import json
import os
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


def sqlitecloud_enabled():
    """Return True when cloud database mode is enabled via environment."""
    return (
        os.getenv('USE_SQLITECLOUD', '').lower() in ('true', '1', 't', 'yes')
        or bool(os.getenv('SQLITECLOUD_CONNECTION_STRING', '').strip())
        or bool(os.getenv('SQLITECLOUD_CONNECTION_URI', '').strip())
    )


def _api_key():
    return os.getenv('SQLITECLOUD_API_KEY', '').strip() or os.getenv('SQLITECLOUD_APIKEY', '').strip()


def gateway_to_native_host(gateway_url):
    """
    Derive the native sqlitecloud host from a Weblite gateway URL.

    Example: caxawolbdz.g1.gateway.sqlite.cloud -> caxawolbdz.g1.sqlite.cloud
    """
    parsed = urlparse(gateway_url if '://' in gateway_url else f'https://{gateway_url}')
    hostname = parsed.hostname or gateway_url.strip('/')
    return hostname.replace('.gateway.', '.')


def get_sqlitecloud_connection_string():
    """
    Return the native sqlitecloud:// connection string from environment.

    Resolution order:
    1. SQLITECLOUD_CONNECTION_STRING or SQLITECLOUD_CONNECTION_URI (dashboard copy)
    2. SQLITECLOUD_API_KEY + SQLITECLOUD_GATEWAY_URL + SQLITECLOUD_DATABASE
    3. SQLITECLOUD_HOST + SQLITECLOUD_APIKEY + SQLITECLOUD_DATABASE
    """
    for name in ('SQLITECLOUD_CONNECTION_STRING', 'SQLITECLOUD_CONNECTION_URI'):
        conn_str = os.getenv(name, '').strip()
        if conn_str:
            return conn_str

    api_key = _api_key()
    gateway = os.getenv('SQLITECLOUD_GATEWAY_URL', '').strip()
    database = os.getenv('SQLITECLOUD_DATABASE', 'lawfirm.db').strip()

    if api_key and gateway:
        host = gateway_to_native_host(gateway)
        return f'sqlitecloud://{host}:8860/{database}?apikey={api_key}'

    host = os.getenv('SQLITECLOUD_HOST', '').strip()
    if host and api_key:
        return f'sqlitecloud://{host}:8860/{database}?apikey={api_key}'

    raise RuntimeError(
        'SQLite Cloud requires SQLITECLOUD_CONNECTION_STRING, '
        'or SQLITECLOUD_API_KEY + SQLITECLOUD_GATEWAY_URL, '
        'or SQLITECLOUD_HOST + SQLITECLOUD_APIKEY'
    )


def build_sqlitecloud_connection_uri():
    """SQLAlchemy database URI (same format as the native connection string)."""
    return get_sqlitecloud_connection_string()


def redact_connection_string(conn_str):
    """Hide apikey query parameter for safe logging."""
    if '?' in conn_str:
        return conn_str.split('?')[0] + '?apikey=***'
    return conn_str


def build_weblite_bearer_token(api_key=None, gateway_url=None):
    """Build the Authorization bearer token for Weblite REST requests."""
    key = api_key or _api_key()
    gateway = (gateway_url or os.getenv('SQLITECLOUD_GATEWAY_URL', '')).strip()
    bearer_mode = os.getenv('SQLITECLOUD_BEARER_MODE', 'orgkey').lower()
    if not key:
        raise RuntimeError('SQLITECLOUD_API_KEY is required')

    if bearer_mode == 'connection_string' and gateway:
        host = gateway_to_native_host(gateway)
        return f'sqlitecloud://{host}:8860?apikey={key}'
    return key


class WebliteClient:
    """Thin client for the SQLite Cloud Weblite REST API (diagnostics)."""

    def __init__(self, gateway_url=None, api_key=None, database=None):
        self.gateway_url = (gateway_url or os.getenv('SQLITECLOUD_GATEWAY_URL', '')).rstrip('/')
        self.api_key = api_key or _api_key()
        self.database = database or os.getenv('SQLITECLOUD_DATABASE', 'lawfirm.db')
        self.bearer_token = build_weblite_bearer_token(self.api_key, self.gateway_url)

    def _request(self, method, path, body=None, extra_headers=None):
        if not self.gateway_url or not self.api_key:
            raise RuntimeError('SQLITECLOUD_GATEWAY_URL and SQLITECLOUD_API_KEY are required')

        url = f'{self.gateway_url}{path}'
        headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {self.bearer_token}',
        }
        if extra_headers:
            headers.update(extra_headers)

        data = None
        if body is not None:
            data = json.dumps(body).encode('utf-8')
            headers['Content-Type'] = 'application/json'

        request = Request(url, data=data, headers=headers, method=method)
        try:
            with urlopen(request, timeout=30) as response:
                return json.loads(response.read().decode('utf-8'))
        except HTTPError as exc:
            err_body = exc.read().decode('utf-8', errors='replace')
            raise RuntimeError(f'Weblite API error {exc.code}: {err_body}') from exc
        except URLError as exc:
            raise RuntimeError(f'Weblite connection failed: {exc.reason}') from exc

    def list_databases(self):
        return self._request('GET', '/v2/weblite/databases')

    def list_tables(self, database=None):
        db_name = database or self.database
        return self._request('GET', f'/v2/weblite/{db_name}/tables')

    def execute_sql(self, sql, database=None):
        return self._request('POST', '/v2/weblite/sql', {
            'sql': sql,
            'database': database or self.database,
        })
