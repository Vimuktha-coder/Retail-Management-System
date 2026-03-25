import os
from dotenv import load_dotenv
from supabase import create_client
import traceback
from collections import defaultdict
import datetime

load_dotenv()
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

stats = {"total_products": 0, "today_sales": 0.0, "low_stock": 0, "pending_pos": 0}
alerts = []
sales_chart_data = []

try:
    print("Fetching products...")
    products_res = supabase.table('products').select('id', count='exact').execute()
    stats['total_products'] = products_res.count if hasattr(products_res, 'count') else len(products_res.data)
    
    print("Fetching sales...")
    sales_res = supabase.table('sales').select('total_amount, created_at').execute()
    
    daily_sales = defaultdict(float)
    today_total = 0.0
    
    if hasattr(sales_res, 'data') and sales_res.data:
        today_str = datetime.datetime.utcnow().strftime('%Y-%m-%d')
        for s in sales_res.data:
            date_str = s.get('created_at', '')[:10] if s.get('created_at') else 'Unknown'
            amt = float(s.get('total_amount', 0))
            daily_sales[date_str] += amt
            if date_str == today_str:
                today_total += amt
        stats['today_sales'] = today_total
        for date, total in sorted(daily_sales.items()):
            sales_chart_data.append({'date': date, 'total': round(total, 2)})
    
    print("Fetching inventory...")
    low_stock_res = supabase.table('inventory').select('*, products(name)').lte('stock_level', 10).execute() 
    stats['low_stock'] = len(low_stock_res.data)
    alerts = [{"name": r['products']['name'], "stock_level": r['stock_level']} for r in low_stock_res.data if 'products' in r]
    
    print("Fetching purchase orders...")
    po_res = supabase.table('purchase_orders').select('id').eq('status', 'Pending').execute()
    stats['pending_pos'] = len(po_res.data)

    print("SUCCESS: No exceptions!")

except Exception as e:
    print("EXCEPTION CAUGHT:")
    traceback.print_exc()
