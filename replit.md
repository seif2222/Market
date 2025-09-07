# Market Management System

## Overview

This is a Flask-based point-of-sale (POS) and inventory management system designed for small to medium businesses. The application provides a comprehensive solution for managing products, processing sales, generating invoices, and tracking business analytics. The system features QR code generation for products, invoice PDF generation, and an Arabic-localized user interface optimized for RTL (right-to-left) display.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Backend Architecture
- **Framework**: Flask web framework with Python
- **Database**: SQLite for local data storage using SQLAlchemy ORM
- **Session Management**: Flask sessions for user authentication and state management
- **Authentication**: Hash-based password authentication using Werkzeug security utilities

### Database Design
The system uses a relational database structure with four main entities:
- **Users**: Store admin credentials and user information
- **Products**: Manage inventory with fields for name, price, quantity, category, and QR codes
- **Sales**: Track individual sales transactions with customer information and totals
- **SaleItems**: Detailed line items for each sale, linking products to sales with quantities and prices

### Frontend Architecture
- **Template Engine**: Jinja2 templating with Flask
- **UI Framework**: Bootstrap 5 with RTL (right-to-left) support for Arabic localization
- **Styling**: Custom CSS for Arabic typography and RTL layout optimization
- **JavaScript**: Vanilla JavaScript for interactive features like cart management and search

### Key Features Implementation
- **QR Code Generation**: Uses the `qrcode` library to generate product QR codes for quick scanning
- **PDF Invoice Generation**: Utilizes ReportLab for creating professional invoices
- **Inventory Management**: Real-time stock tracking with automatic quantity updates on sales
- **Sales Analytics**: Dashboard with statistics and reporting capabilities
- **Multi-language Support**: Arabic-first interface with RTL layout support

### File Structure
- **app.py**: Main application entry point with database initialization
- **models.py**: SQLAlchemy model definitions for all database entities
- **routes.py**: Flask route handlers for all application endpoints
- **utils.py**: Utility functions for QR code and PDF generation
- **templates/**: HTML templates with Arabic RTL support
- **static/**: CSS, JavaScript, and generated assets (QR codes, invoices)

## External Dependencies

### Python Libraries
- **Flask**: Web framework for routing and request handling
- **Flask-SQLAlchemy**: Database ORM for SQLite integration
- **Werkzeug**: Security utilities for password hashing and authentication
- **qrcode**: QR code generation for product identification
- **Pillow (PIL)**: Image processing for QR code creation
- **ReportLab**: PDF generation for invoices and reports

### Frontend Dependencies
- **Bootstrap 5**: UI framework with RTL support for Arabic layout
- **Font Awesome**: Icon library for user interface elements
- **Custom CSS**: Arabic typography and RTL-specific styling

### File System Dependencies
- **SQLite Database**: Local file-based database (market_system.db)
- **Static File Storage**: Local directories for QR codes and invoice PDFs
- **Session Storage**: Server-side session management for user authentication

### Development Tools
- **Logging**: Python logging module for debugging and monitoring
- **Environment Variables**: Support for configuration through environment variables