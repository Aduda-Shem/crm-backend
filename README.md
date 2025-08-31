# Lead Management System - Backend

Django REST Framework backend for managing leads, contacts, notes, reminders, and correspondence tracking with comprehensive audit trails and role-based access control.

### Project Structure
```
backend/
├── apps/
│   ├── accounts/          # User authentication and management
│   └── crm/              # Core CRM functionality
├── core/                  # Project configuration
├── requirements.txt       # Python dependencies
├── Dockerfile.dev        # Development container
├── Dockerfile.prod       # Production container
└── entrypoint.sh         # Container startup script
```
### Quick Start with Docker

1. **Clone the repository**
   ```bash
   git clone https://github.com/Aduda-Shem/crm-backend
   cd backend
   ```

2. **Set up environment variables**
   ```bash
   cp env.example .env
   # Edit .env with your configuration
   ```

3. **Start the services**
   ```bash
   docker-compose up -d
   ```

4. **Run migrations**
   ```bash
   docker-compose exec backend python manage.py migrate
   ```

5. **Create superuser**
   ```bash
   docker-compose exec backend python manage.py createsuperuser
   ```

6. **Access the application**
   - API: http://localhost:8000/api/
   - Admin: http://localhost:8000/admin/
   - Documentation: http://localhost:8000/api/docs/

### Local Development Setup

1. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up database**
   ```bash
   # Configure PostgreSQL connection in .env
   python manage.py migrate
   python manage.py runserver
   ```

## API Documentation

### Authentication
All API endpoints require JWT authentication. Include the token in the Authorization header:
```
Authorization: Bearer <your-jwt-token>
```

### Key Endpoints

#### Leads
- `GET /api/leads/` - List all leads
- `POST /api/leads/` - Create new lead
- `GET /api/leads/{id}/` - Get specific lead
- `PUT /api/leads/` - Update lead
- `DELETE /api/leads/` - Delete lead
- `GET /api/leads/{id}/summary/` - Get lead summary

#### Contacts
- `GET /api/contacts/` - List all contacts
- `POST /api/contacts/` - Create new contact
- `PUT /api/contacts/` - Update contact
- `DELETE /api/contacts/` - Delete contact

#### Notes
- `GET /api/notes/` - List notes (filterable by lead)
- `POST /api/notes/` - Create new note
- `PUT /api/notes/` - Update note
- `DELETE /api/notes/` - Delete note

#### Reminders
- `GET /api/reminders/` - List reminders (filterable by lead)
- `POST /api/reminders/` - Create new reminder
- `PUT /api/reminders/` - Update reminder
- `DELETE /api/reminders/` - Delete reminder

#### Correspondence
- `GET /api/correspondence/` - List correspondence entries
- `POST /api/correspondence/` - Log new correspondence
- `PUT /api/correspondence/` - Update correspondence
- `DELETE /api/correspondence/` - Delete correspondence

### Filtering and Search
All list endpoints support filtering and search:
```
GET /api/leads/?status=NEW&owner=1&search=john
GET /api/notes/?lead=5&created_by=2
GET /api/reminders/?lead=3&reminder_type=FOLLOW_UP
```

##  User Roles and Permissions

### Manager Role
- Full access to all features
- Can create, read, update, and delete all entities
- Access to audit trails and system reports
- User management capabilities

### Agent Role
- Can create, read, and update leads and contacts
- Cannot delete leads or contacts
- Full access to notes, reminders, and correspondence
- Limited access to audit information

