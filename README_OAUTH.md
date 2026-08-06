# Frore OAuth Login System Implementation

## Overview

This PR implements OAuth authentication for the Xray machine booking system, enabling employees to sign in using their Frore Systems identity.

## Features

### 🔐 OAuth Authentication
- **Frore OAuth Provider Integration** - Users can sign in with their Frore Systems account
- **Dual Authentication** - Support for both local (username/password) and OAuth login
- **Automatic User Provisioning** - New OAuth users are automatically created on first login
- **Admin Approval Workflow** - New OAuth users require admin approval before accessing the system

### 📋 Database Schema Updates
- **User Model Enhancements**:
  - `email` - User's email address (unique)
  - `oauth_provider` - OAuth provider name (e.g., 'frore')
  - `oauth_id` - Unique identifier from OAuth provider
  - `password_hash` - Made nullable to support password-less OAuth users

### 🚀 Deployment Options
1. **Local Development** - Simple setup with SQLite
2. **Docker Compose** - Complete dev/prod environment with PostgreSQL
3. **Systemd** - Production deployment on Linux servers
4. **Nginx Reverse Proxy** - HTTPS with security headers

## Files Changed

### Core Changes
- `models/__init__.py` - Added OAuth fields to User model
- `config.py` - OAuth configuration settings
- `routes/auth.py` - Complete OAuth flow implementation
- `requirements.txt` - Added `requests` library for OAuth integration

### UI Updates
- `templates/auth/login.html` - Updated login page with OAuth button and local login options

### Configuration & Deployment
- `.env.example` - Environment variables template with OAuth settings
- `Dockerfile` - Container image for application
- `docker-compose.yml` - Multi-container setup (app + PostgreSQL)
- `DEPLOYMENT.md` - Comprehensive deployment guide

## How It Works

### OAuth Flow
1. User clicks "Sign in with Frore" button
2. Application redirects to Frore OAuth authorize endpoint
3. User authenticates with Frore (if not already logged in)
4. Frore redirects back with authorization code
5. Application exchanges code for access token
6. Application retrieves user info from OAuth provider
7. User is automatically created/logged in

### User Creation
- **First Login**: New user is created with OAuth credentials
- **Status**: Set to `is_qualified=False` (requires admin approval)
- **Email**: Automatically populated from OAuth provider
- **Username**: Generated from email (e.g., "john" from "john@frore.com")

## Configuration

### Environment Variables
Set in `.env` file:

```env
# Enable OAuth
OAUTH_ENABLED=true

# OAuth Provider
OAUTH_PROVIDER=frore

# Frore OAuth Credentials (obtain from your OAuth admin)
OAUTH_CLIENT_ID=your-client-id
OAUTH_CLIENT_SECRET=your-client-secret

# Frore OAuth Endpoints
OAUTH_AUTHORIZE_URL=https://frore.example.com/oauth/authorize
OAUTH_TOKEN_URL=https://frore.example.com/oauth/token
OAUTH_USERINFO_URL=https://frore.example.com/oauth/userinfo

# Application Redirect URL (must match OAuth provider config)
OAUTH_REDIRECT_URI=https://xray.example.com/auth/oauth/callback
```

## Deployment

### Quick Start with Docker
```bash
cp .env.example .env
# Edit .env with your OAuth credentials
docker-compose up -d
```

### Production on Linux
```bash
# See DEPLOYMENT.md for complete setup guide
# Includes systemd service, nginx reverse proxy, PostgreSQL setup
```

## Security Considerations

✅ **Implemented**:
- Password hashes use Werkzeug's secure hashing (PBKDF2)
- OAuth tokens exchanged server-side (not exposed to browser)
- Password-less OAuth users cannot be compromised by weak passwords
- CSRF protection via Flask's session mechanism
- Secure cookie settings (HttpOnly, Secure flags)

⚠️ **Recommendations**:
- Use HTTPS in production (required by most OAuth providers)
- Rotate `SECRET_KEY` regularly
- Monitor logs for authentication failures
- Regularly audit user permissions
- Keep dependencies updated

## Testing

### Manual Testing
1. Start application
2. Navigate to `/auth/login`
3. Test local login (if enabled)
4. Test OAuth login (if configured)
5. Verify new user creation in database
6. Test admin approval workflow

### Environment Variables for Testing
```env
OAUTH_ENABLED=true
FLASK_DEBUG=1
```

## Troubleshooting

**OAuth login not working?**
- Verify `OAUTH_ENABLED=true` in `.env`
- Check that `OAUTH_REDIRECT_URI` matches OAuth provider config
- Verify `OAUTH_CLIENT_ID` and `OAUTH_CLIENT_SECRET` are correct
- Check application logs for error messages

**New users not created?**
- Verify OAuth provider is returning `sub` or `id` field
- Check that email is being returned by OAuth provider
- Review database for user creation errors

**Migration from existing users?**
- Existing local users continue to work (no data loss)
- Add `--oauth-provider=frore` option to sync with OAuth system (future feature)

## Future Enhancements

- [ ] Multiple OAuth providers (Google, Microsoft, etc.)
- [ ] LDAP/Active Directory integration
- [ ] User profile synchronization
- [ ] Role-based access control (RBAC)
- [ ] Two-factor authentication (2FA)
- [ ] Audit logging for authentication events

## Support & Documentation

- See `DEPLOYMENT.md` for complete deployment instructions
- See `.env.example` for configuration options
- See `routes/auth.py` for OAuth implementation details
