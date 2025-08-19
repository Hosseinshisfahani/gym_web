# Shirneshan Sport - Comprehensive Gym Management & E-commerce Platform

## 🏋️‍♂️ Project Overview

**Shirneshan Sport** is a comprehensive web-based platform that combines gym management services with an integrated e-commerce shop for sports equipment and apparel. The platform is built using Django (Python) and provides a complete solution for fitness professionals to manage their clients, programs, and business operations.

## 🏗️ Architecture & Technology Stack

### Backend Framework
- **Django 5.2.1** - Main web framework
- **PostgreSQL** - Primary database
- **Python 3.x** - Programming language

### Key Dependencies
- **Pillow** - Image processing and manipulation
- **django-widget-tweaks** - Enhanced form rendering
- **reportlab** - PDF generation capabilities
- **jdatetime** - Persian (Jalali) date support
- **psycopg2-binary** - PostgreSQL adapter
- **python-dotenv** - Environment variable management

### Frontend
- **HTML5/CSS3** - Modern responsive design
- **JavaScript** - Interactive functionality
- **Bootstrap** - UI framework (inferred from templates)
- **RTL Support** - Full Persian language support

## 📁 Project Structure

```
gym_web/
├── cnt_project/                 # Main Django project
│   ├── gym_website/            # Project settings and configuration
│   ├── gym/                    # Core gym management app
│   ├── gym_shop/              # E-commerce module
│   ├── category_export/       # Category management utilities
│   ├── manage.py              # Django management script
│   ├── requirements.txt       # Python dependencies
│   └── locale/               # Internationalization files
├── front_end/                 # Frontend assets
│   ├── static/               # Static files (CSS, JS, images)
│   ├── templates/            # HTML templates
│   ├── staticfiles/          # Collected static files
│   └── media/               # User-uploaded files
└── venv/                    # Python virtual environment
```

## 🎯 Core Features

### 1. User Management System
- **User Registration & Authentication**
- **Profile Management** with personal information
- **VIP User System** for premium members
- **Multi-factor authentication** via phone numbers
- **Persian language support** throughout the interface

### 2. Fitness Program Management
- **Workout Plans**: Customized exercise programs
  - Fat burning, bulk, hypertrophy, corrective programs
  - Duration-based planning (weeks)
  - File attachments for detailed instructions
  - Progress tracking

- **Diet Plans**: Nutritional guidance
  - Personalized meal plans
  - Duration tracking
  - File-based instructions
  - Integration with body analysis

### 3. Body Analysis & Progress Tracking
- **Body Information Management**
  - Height, weight, body measurements
  - Body composition tracking
  - Medical history documentation
  - Multi-angle body photos

- **Progress Analysis**
  - Weight tracking
  - Body fat percentage monitoring
  - Muscle mass measurements
  - Custom measurement types

- **Monthly Goals System**
  - Target setting for weight, body fat, muscle mass
  - Progress percentage calculation
  - Coach feedback integration
  - Goal direction (lose/gain/maintain)

### 4. Payment & Financial Management
- **Multiple Payment Methods**
  - Manual payment with receipt upload
  - Online payment gateways (ZarinPal, IDPay)
  - Card-based payments

- **Payment Types**
  - Membership fees
  - Workout plan purchases
  - Diet plan purchases
  - Booklet purchases

- **Payment Status Tracking**
  - Pending, approved, rejected, failed
  - Admin approval workflow
  - Automatic verification for gateway payments

### 5. E-commerce Module (Gym Shop)
- **Product Management**
  - Categories and subcategories
  - Product details with multiple images
  - Size and inventory management
  - Discount system
  - Product specifications (brand, material, color, weight)

- **Shopping Cart System**
  - Add/remove products
  - Quantity management
  - Cart persistence

- **Order Management**
  - Complete order workflow
  - Order status tracking
  - Customer information management
  - Inventory updates

### 6. Support & Communication
- **Ticket System**
  - User support tickets
  - Admin responses
  - Status tracking (open, in progress, closed)
  - Multi-message conversations

- **Document Management**
  - Certificate uploads
  - Educational documents
  - Medical records
  - File organization by type

### 7. Administrative Features
- **Admin Dashboard**
  - User management
  - Payment approvals
  - Plan request management
  - Order processing
  - Analytics and reporting

- **Email Notification System**
  - Configurable notification preferences
  - Order status updates
  - Payment confirmations
  - Plan request notifications

## 🗄️ Database Models

### Core User Models
- **UserProfile**: Extended user information
- **BodyInformationUser**: Physical measurements and medical data
- **EmailNotificationSettings**: Admin notification preferences

### Program Models
- **WorkoutPlan**: Exercise programs with types and durations
- **DietPlan**: Nutritional programs
- **PlanRequest**: User requests for custom programs
- **MonthlyGoal**: Goal setting and tracking

### Financial Models
- **Payment**: All payment transactions
- **PaymentCard**: Payment card information
- **Booklet**: Educational materials for sale
- **BookletPayment**: Booklet purchase transactions

### E-commerce Models (gym_shop app)
- **Category**: Product categories
- **Product**: Product information and inventory
- **Cart/CartItem**: Shopping cart functionality
- **Order/OrderItem**: Order management

### Support Models
- **Ticket/TicketResponse**: Support system
- **Document**: File management
- **BodyAnalysisReport**: Progress reports

## 🔧 Configuration & Setup

### Environment Configuration
```python
# Database Configuration
DATABASES_POSTGRESQL = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'gymdb',
        'USER': 'gymuser',
        'PASSWORD': 'strongpassword',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

# Payment Gateway Configuration
ZARINPAL_MERCHANT_ID = 'your-merchant-id'
IDPAY_API_KEY = 'your-api-key'
PAYMENT_GATEWAY_TYPE = 'zarinpal'  # or 'idpay'
```

### URL Structure
- `/` - Main dashboard
- `/shop/` - E-commerce section
- `/admin/` - Django admin interface
- `/accounts/` - Authentication pages
- `/plans/` - Program management
- `/payments/` - Payment processing
- `/support/` - Ticket system

## 🌐 Deployment & Production

### Server Configuration
- **Nginx** - Web server and reverse proxy
- **Gunicorn** - WSGI server
- **PostgreSQL** - Production database
- **Linux** - Operating system (Ubuntu/Debian)

### Security Features
- **HTTPS** - SSL/TLS encryption
- **CSRF Protection** - Cross-site request forgery prevention
- **SQL Injection Protection** - Django ORM security
- **File Upload Security** - Validated file types and sizes
- **Environment Variables** - Secure configuration management

## 📊 Business Logic

### User Workflow
1. **Registration** → Profile completion → Body information submission
2. **Plan Request** → Payment → Plan creation → Progress tracking
3. **Shop Purchase** → Cart → Checkout → Order fulfillment
4. **Support** → Ticket creation → Admin response → Resolution

### Admin Workflow
1. **User Management** → Profile verification → VIP status assignment
2. **Payment Processing** → Receipt verification → Status updates
3. **Plan Creation** → Custom program development → File upload
4. **Order Fulfillment** → Inventory management → Shipping coordination

## 🎨 User Interface Features

### Design Principles
- **Responsive Design** - Mobile-first approach
- **Persian RTL Support** - Right-to-left text direction
- **Modern UI/UX** - Clean, intuitive interface
- **Accessibility** - WCAG compliance considerations
- **Performance** - Optimized loading times

### Key UI Components
- **Dashboard Cards** - Quick access to main features
- **Progress Charts** - Visual progress tracking
- **Form Validation** - Real-time input validation
- **Modal Dialogs** - Interactive popups
- **File Upload** - Drag-and-drop functionality

## 🔮 Future Enhancements

### Planned Features
- **Mobile Application** - Native iOS/Android apps
- **Advanced Analytics** - Detailed reporting and insights
- **Social Features** - Community and sharing capabilities
- **AI Integration** - Automated plan recommendations
- **Video Content** - Exercise demonstration videos
- **Live Coaching** - Real-time video sessions

### Technical Improvements
- **API Development** - RESTful API for mobile apps
- **Caching System** - Redis integration for performance
- **Background Tasks** - Celery for async operations
- **Microservices** - Service-oriented architecture
- **Containerization** - Docker deployment

## 📈 Scalability Considerations

### Database Optimization
- **Indexing** - Strategic database indexes
- **Query Optimization** - Efficient ORM usage
- **Connection Pooling** - Database connection management
- **Caching** - Query result caching

### Performance Optimization
- **Static File CDN** - Content delivery network
- **Image Optimization** - Compressed image delivery
- **Code Splitting** - Modular JavaScript loading
- **Database Sharding** - Horizontal scaling preparation

## 🛡️ Security & Compliance

### Data Protection
- **User Privacy** - GDPR compliance considerations
- **Data Encryption** - Sensitive data protection
- **Access Control** - Role-based permissions
- **Audit Logging** - Activity tracking

### Payment Security
- **PCI Compliance** - Payment card industry standards
- **Tokenization** - Secure payment data handling
- **Fraud Prevention** - Transaction monitoring
- **Secure Gateways** - Certified payment processors

## 📚 Documentation & Support

### Available Documentation
- **API Documentation** - Integration guides
- **User Manuals** - Feature explanations
- **Admin Guides** - Management procedures
- **Developer Docs** - Technical specifications

### Support Channels
- **In-app Tickets** - Integrated support system
- **Email Support** - Direct communication
- **Phone Support** - Voice assistance
- **Live Chat** - Real-time help (planned)

---

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- PostgreSQL 12+
- Nginx (for production)
- Virtual environment

### Installation Steps
1. Clone the repository
2. Create virtual environment: `python -m venv venv`
3. Activate environment: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Configure database settings
6. Run migrations: `python manage.py migrate`
7. Create superuser: `python manage.py createsuperuser`
8. Run development server: `python manage.py runserver`

### Production Deployment
1. Configure production settings
2. Set up PostgreSQL database
3. Configure Nginx reverse proxy
4. Set up SSL certificates
5. Configure environment variables
6. Run collectstatic: `python manage.py collectstatic`
7. Start Gunicorn service
8. Monitor logs and performance

---

**This platform represents a comprehensive solution for modern fitness business management, combining traditional gym services with e-commerce capabilities in a unified, user-friendly interface.** 