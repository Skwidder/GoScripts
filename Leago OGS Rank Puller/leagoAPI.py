import asyncio
import webbrowser
import base64
import hashlib
import secrets
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
import httpx
from datetime import datetime, timedelta

AUTHORITY = "https://id.leago.gg"
CLIENT_ID = "leago.public"
SCOPE = "openid profile Leago.WebAPI"
REDIRECT_PORT = 63136
REDIRECT_URI = f"http://127.0.0.1:{REDIRECT_PORT}"

class CallbackHandler(BaseHTTPRequestHandler):
    code = None
    state = None
    error = None
    
    def do_GET(self):
        query = parse_qs(urlparse(self.path).query)
        CallbackHandler.code = query.get("code", [None])[0]
        CallbackHandler.state = query.get("state", [None])[0]
        CallbackHandler.error = query.get("error", [None])[0]
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        
        if CallbackHandler.error:
            self.wfile.write(f"<h1>Error: {CallbackHandler.error}</h1>".encode())
        else:
            self.wfile.write(b"<h1>Success! Close this window.</h1>")
    
    def log_message(self, format, *args):
        pass

def generate_pkce():
    verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode().rstrip('=')
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip('=')
    return verifier, challenge

class LeagoAuth:
    def __init__(self):
        self.discovery = None
        self.access_token = None
        self.expires_at = None

    async def discover(self):
        async with httpx.AsyncClient() as client:
            r = await client.get(f"{AUTHORITY}/.well-known/openid-configuration")
            self.discovery = r.json()
            return True

    def build_auth_url(self):
        verifier, challenge = generate_pkce()
        self.verifier = verifier
        self.state = base64.urlsafe_b64encode(secrets.token_bytes(16)).decode().rstrip('=')
        
        params = {
            'response_type': 'code',
            'client_id': CLIENT_ID,
            'redirect_uri': REDIRECT_URI,
            'scope': SCOPE,
            'state': self.state,
            'code_challenge': challenge,
            'code_challenge_method': 'S256'
        }
        
        return f"{self.discovery['authorization_endpoint']}?" + urllib.parse.urlencode(params)

    async def wait_callback(self):
        CallbackHandler.code = None
        CallbackHandler.state = None
        CallbackHandler.error = None
        
        server = HTTPServer(("127.0.0.1", REDIRECT_PORT), CallbackHandler)
        
        attempts = 0
        while CallbackHandler.code is None and CallbackHandler.error is None and attempts < 120:
            server.timeout = 1.0
            server.handle_request()
            attempts += 1
        
        server.server_close()
        
        if CallbackHandler.error:
            raise Exception(f"Auth error: {CallbackHandler.error}")
        if CallbackHandler.code is None:
            raise Exception("Timeout")
        if CallbackHandler.state != self.state:
            raise Exception("State mismatch")
        
        return CallbackHandler.code

    async def get_tokens(self, code):
        data = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': REDIRECT_URI,
            'client_id': CLIENT_ID,
            'code_verifier': self.verifier,
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(self.discovery["token_endpoint"], data=data)
            
            if response.status_code != 200:
                raise Exception(f"Token failed: {response.text}")
            
            tokens = response.json()
            self.access_token = tokens['access_token']
            expires_in = tokens.get('expires_in', 3600)
            self.expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
            
            return tokens

    async def login(self):
        await self.discover()
        auth_url = self.build_auth_url()
        webbrowser.open(auth_url)
        code = await self.wait_callback()
        return await self.get_tokens(code)

    async def get_token(self):
        if self.access_token and datetime.utcnow() < self.expires_at - timedelta(minutes=5):
            return self.access_token
        
        await self.login()
        return self.access_token

class AuthClient:
    def __init__(self, auth: LeagoAuth):
        self.auth = auth
        
    async def get(self, url, **kwargs):
        token = await self.auth.get_token()
        headers = kwargs.get('headers', {})
        headers['Authorization'] = f'Bearer {token}'
        kwargs['headers'] = headers
        
        async with httpx.AsyncClient() as client:
            return await client.get(url, **kwargs)
