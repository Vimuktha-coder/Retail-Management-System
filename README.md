# Retail Management System

Welcome to the **Retail Management System**, a fully-featured, cloud-ready web application built to streamline store operations. The system incorporates Role-Based Access Control (RBAC), Inventory Tracking, Point of Sale (POS) Checkout, and an integrated AI Chatbot.

## 🚀 Features

- **Store Dashboard:** Real-time metrics including today's sales, low stock alerts, and a dynamic revenue chart (powered by Chart.js).
- **Point of Sale (POS):** A dynamic, Javascript-driven cart system that allows staff to quickly ring up customers and adjust quantities.
- **Inventory Management:** Supports adding, categorizing, and managing thousands of SKUs. Features a Secure "Bulk-Delete Out of Stock" action.
- **Role-Based Access Control (RBAC):** Distinct `Admin` and `Staff` roles. Staff members are isolated to POS and viewing stock, while Admins control Procurement and overall system changes.
- **Procurement & Purchase Orders:** Track incoming stock and supplier relationships.
- **AI Assistant:** An integrated Google Gemini AI chatbot available to assist users directly on the dashboard.

## 🛠️ Technology Stack

- **Backend:** Python / Flask
- **Database:** Supabase (PostgreSQL)
- **Frontend:** HTML5, Vanilla JavaScript, CSS3
- **Authentication:** Flask-Session & Bcrypt
- **AI Platform:** Google Gemini 2.5 Flash API

## 💻 Running Locally

### Prerequisites
- Python 3.9+
- A [Supabase](https://supabase.com/) Account (Free Tier)
- A [Google AI Studio](https://aistudio.google.com/) API Key (Free Tier)

### 1. Clone the Repository
```bash
git clone https://github.com/Vimuktha-coder/Retail-Management-System.git
cd Retail-Management-System
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Environment Variables
Create a file named `.env` in the root directory of the project and add your unique API keys:
```env
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=your_secure_random_string_here
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-supabase-anon-key
GEMINI_API_KEY=your-google-gemini-key
```

### 4. Run the Server
```bash
python app.py
```
*The app will automatically start at `http://127.0.0.1:5000`*
id:admin@retail.com
pass:password123
id:staff@retail.com
pass:password123

## 🌩️ Cloud Deployment (Render.com)

This application is configured for an effortless 1-click deployment on **Render**.
1. Create a **New Web Service** and connect this continuous deployment repository.
2. Set the Environment to `Python 3`.
3. Set the Build Command to `pip install -r requirements.txt`.
4. Set the Start Command to `gunicorn app:app`.
5. Provide your `.env` variables under the **Environment Variables** tab.
