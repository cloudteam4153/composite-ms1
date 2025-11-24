# Environment Setup Guide

## Integrations Service Setup

The integrations service requires environment variables. Create a `.env` file:

```bash
cd integrations-svc-ms2

# Generate a valid Fernet key (32 bytes, base64-encoded)
TOKEN_KEY=$(python3 -c "import base64, secrets; print(base64.urlsafe_b64encode(secrets.token_bytes(32)).decode())")

cat > .env << EOF
DATABASE_URL=sqlite+aiosqlite:///./dev.db
TOKEN_ENCRYPTION_KEY=${TOKEN_KEY}
EOF
```

Or manually create `.env` with a valid Fernet key:
```
DATABASE_URL=sqlite+aiosqlite:///./dev.db
TOKEN_ENCRYPTION_KEY=mrs5ElwA0bn5IvE6xHGNCCN18WuPcKJ1bu8B8xlgQJo=
```

**Note**: 
- `DATABASE_URL` uses SQLite for local development (no database server needed)
- `TOKEN_ENCRYPTION_KEY` must be a valid Fernet key (32 url-safe base64-encoded bytes)
- Generate a new key for production: `python3 -c "import base64, secrets; print(base64.urlsafe_b64encode(secrets.token_bytes(32)).decode())"`

## Other Services

- **Actions Service (ms3)**: No environment variables required
- **Classification Service (ms4-classification)**: No environment variables required  
- **Composite Service (composite-ms1)**: No environment variables required (uses defaults)

## Install Dependencies

Make sure all dependencies are installed (especially `aiosqlite` for SQLite support):

```bash
cd integrations-svc-ms2
pip install -r requirements.txt
```

## Verify Setup

Test that the integrations service can load settings:

```bash
cd integrations-svc-ms2
python -c "from config.settings import settings; print('Settings loaded!')"
```

If you see "Settings loaded!" then you're good to go!

