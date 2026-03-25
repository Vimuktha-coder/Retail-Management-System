from flask import Flask, render_template, session, redirect, url_for
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from config import Config
from db import supabase

app = Flask(__name__)
app.config.from_object(Config)

# Apply ProxyFix if running behind a reverse proxy (e.g., Nginx) for secure cookies
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

# Enable CSRF Protection
csrf = CSRFProtect(app)

# Rate limiting to prevent brute-force attacks
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["500 per day", "100 per hour"],
    storage_uri="memory://"
)

# --- Security Headers ---
@app.after_request
def add_security_headers(response):
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com data:; img-src 'self' data:;"
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response

# --- Register Blueprints ---
from routes.inventory_routes import inventory_bp
from routes.procurement_routes import procurement_bp
from routes.sales_routes import sales_bp
from routes.auth_routes import auth_bp

app.register_blueprint(auth_bp)
app.register_blueprint(inventory_bp)
app.register_blueprint(sales_bp)
app.register_blueprint(procurement_bp)

from flask import request

@app.before_request
def require_login():
    allowed_endpoints = ['auth.login', 'auth.setup_default_users', 'static']
    if request.endpoint and request.endpoint not in allowed_endpoints and 'user_id' not in session:
        return redirect(url_for('auth.login'))
        
    if request.endpoint and request.endpoint.startswith('procurement.') and session.get('role') != 'Admin':
        from flask import flash
        flash('Access denied: Admin privileges required.', 'error')
        return redirect(url_for('dashboard'))

@app.route('/')
def index():
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    stats = {"total_products": 0, "today_sales": 0.0, "low_stock": 0, "pending_pos": 0}
    alerts = []
    sales_chart_data = []
    
    if supabase:
        try:
            products_res = supabase.table('products').select('id', count='exact').execute()
            stats['total_products'] = products_res.count if hasattr(products_res, 'count') else len(products_res.data)
            
            # Simple simulation for today sales sum
            sales_res = supabase.table('sales').select('total_amount, created_at').execute()
            
            # Compute today's total and build chart timeline
            from collections import defaultdict
            daily_sales = defaultdict(float)
            today_total = 0.0
            
            if hasattr(sales_res, 'data') and sales_res.data:
                import datetime
                today_str = datetime.datetime.utcnow().strftime('%Y-%m-%d')
                
                for s in sales_res.data:
                    date_str = s.get('created_at', '')[:10] if s.get('created_at') else 'Unknown'
                    amt = float(s.get('total_amount', 0))
                    daily_sales[date_str] += amt
                    
                    if date_str == today_str:
                        today_total += amt
                        
                stats['today_sales'] = today_total
                
                # Format for Chart.js
                for date, total in sorted(daily_sales.items()):
                    sales_chart_data.append({'date': date, 'total': round(total, 2)})
            
            
            low_stock_res = supabase.table('inventory').select('*, products(name)').lte('stock_level', 10).execute() # Uses default 10 threshold for demo
            stats['low_stock'] = len(low_stock_res.data)
            
            # Safely fetch product names safely avoiding NoneType subscription errors
            for r in low_stock_res.data:
                prod_name = r.get('products', {}).get('name') if isinstance(r.get('products'), dict) else 'Unknown Product'
                alerts.append({"name": prod_name, "stock_level": r['stock_level']})
            
            po_res = supabase.table('purchase_orders').select('id').eq('status', 'Pending').execute()
            stats['pending_pos'] = len(po_res.data)
        except Exception as e:
            print("Dashboard stat load error:", str(e))
            # Inject the exact python error into the web UI so the user isn't left guessing with 0s!
            alerts.append({"name": "SYSTEM ERROR", "stock_level": str(e)})

    return render_template('dashboard.html', stats=stats, alerts=alerts, sales_chart_data=sales_chart_data)

# --- AI Chatbot Route ---
from services.chatbot import ChatbotService
from flask import request, jsonify

@app.route('/api/chat', methods=['POST'])
def chat_api():
    try:
        user_message = request.json.get('message')
        if not user_message:
            return jsonify({"error": "Message is required"}), 400
            
        chatbot = ChatbotService(app.config['GEMINI_API_KEY'])
        ai_response = chatbot.get_response(user_message)
        
        return jsonify({"response": ai_response})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
