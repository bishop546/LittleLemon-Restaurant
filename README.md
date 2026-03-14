LittleLemon-Restaurant
A robust, role-based backend system built with Django REST Framework (DRF). This API handles the complete lifecycle of a restaurant's digital operations—from customer menu browsing and cart management to manager-led delivery assignments.

Key Features & Logic
Role-Based Access Control (RBAC): Distinct permissions and views for Managers, Delivery Crew, and Customers.
Order Management: Customers place orders; Managers assign them to specific Delivery Crew members; Delivery Crew update status.
Secure Authentication: Utilizes Token-based authentication for session management.
Performance Optimized: Includes Pagination for menu items and Throttling (User & Anonymous) to prevent API abuse.
Search & Filtering: Robust filtering for menu items to enhance user experience.

User Roles & Permissions
Manager - Full CRUD on Menu, Assign/Remove Delivery Crew, Assign Orders to Crew.
Delivery Crew - View assigned orders only, update delivery status (e.g., "Delivered").
Customer - Browse Menu items, Manage personal Cart, Place/View personal Orders.

API Endpoints


Technical Stack
Languages: Python
Framework: Django REST Framework (DRF)
Database: SQLite
Auth: Djoser / DRF Token Authentication
Testing: Insomnia

