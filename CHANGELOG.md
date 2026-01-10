# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2025-01-04

### Added

#### Authentication & Security
- JWT-based authentication with access and refresh tokens
- Two-Factor Authentication (2FA) with TOTP and QR code setup
- Password strength validation with entropy meter
- Rate limiting with SlowAPI (configurable per-endpoint)
- Session management with device tracking
- Audit logging for compliance
- GDPR data export endpoint

#### Team & Collaboration
- Team creation and management
- Role-based access control (Admin, Analyst, Viewer)
- Member invitation system
- Team-level permissions

#### Notifications & Alerts
- Real-time WebSocket notifications
- Email alerts for fraud detection
- Webhook integrations for external systems
- Slack/Discord notification support

#### Analytics & Reporting
- Advanced dashboard with heatmaps
- Trend analysis charts
- PDF/CSV report generation
- Scheduled automatic reports
- Period comparison analytics

#### Machine Learning
- XGBoost model support
- SHAP values for prediction explanations
- Feature importance visualization
- Batch prediction with CSV upload

#### Infrastructure
- PostgreSQL database support
- Redis caching layer
- Docker and Docker Compose setup
- Kubernetes manifests (k8s/)
- GitHub Actions CI/CD pipeline
- Multi-platform Docker builds (amd64, arm64)

### Changed
- Upgraded to FastAPI 0.109.0
- Upgraded to React 18 with Vite
- Improved API response times with caching
- Enhanced error handling and logging

### Security
- Input validation on all endpoints
- SQL injection prevention with SQLAlchemy ORM
- XSS protection in frontend
- CORS configuration
- Secure password hashing with bcrypt

## [1.0.0] - 2024-12-01

### Added
- Initial release
- Basic fraud detection with Random Forest model
- REST API with FastAPI
- React frontend with TailwindCSS
- Single transaction prediction
- Model information endpoint
- Docker support

---

## Migration Guide

### From 1.x to 2.0

1. **Database Migration**
   ```bash
   # Backup your existing database
   cp fraud_detection.db fraud_detection.db.backup

   # The new schema will be created automatically on first run
   ```

2. **Environment Variables**
   New required variables:
   ```env
   SECRET_KEY=your-secret-key-min-32-chars
   DATABASE_URL=sqlite:///./fraud_detection.db  # or PostgreSQL URL
   ```

3. **API Changes**
   - All endpoints now under `/api/v1/` prefix
   - Authentication required for most endpoints
   - New response format with additional metadata

4. **Frontend**
   - Login required to access dashboard
   - New navigation with user menu
   - Dark mode enabled by default

---

## [Unreleased]

### Planned
- GraphQL API support
- Mobile app (React Native)
- Real-time model retraining
- A/B testing for models
- Multi-language support
