from flask import Blueprint, render_template, request, flash, jsonify
from db import supabase
from datetime import datetime

sales_bp = Blueprint('sales', __name__, url_prefix='/sales')

@sales_bp.route('/pos')
def pos():
    if not supabase:
        flash("Database connection error.", "error")
        return render_template('pos.html', products=[])
    
    try:
        # Fetch products with stock > 0 for POS
        # Note: We need to filter products where inventory > 0, but doing inner join equivalent in supabase:
        res = supabase.table('products').select("id, name, price, sku, inventory!inner(stock_level)").gt('inventory.stock_level', 0).execute()
        products = res.data
        return render_template('pos.html', products=products)
    except Exception as e:
        flash(f"Error fetching products for POS: {str(e)}", "error")
        return render_template('pos.html', products=[])

@sales_bp.route('/history')
def history():
    if not supabase: return render_template('sales_history.html', sales=[])
    try:
        # Fetch Sales with items
        # Currently leaving out user/seller relation as auth isn't fully active
        res = supabase.table('sales').select("*, sale_items(*, products(name))").order('created_at', desc=True).execute()
        sales_data = res.data
        return render_template('sales_history.html', sales=sales_data)
    except Exception as e:
        flash(str(e), "error")
        return render_template('sales_history.html', sales=[])

@sales_bp.route('/checkout', methods=['POST'])
def checkout():
    if not supabase: return jsonify({"error": "No DB connection"}), 500
    try:
        data = request.json
        items = data.get('cart') # List of {product_id, quantity, price}
        
        if not items or len(items) == 0:
            return jsonify({"error": "Cart is empty"}), 400

        # Validate stock availability
        for item in items:
            inv = supabase.table('inventory').select('stock_level').eq('product_id', item['product_id']).execute()
            if not inv.data or inv.data[0]['stock_level'] < int(item['quantity']):
                return jsonify({"error": f"Insufficient stock for product ID {item['product_id']}"}), 400

        total_amount = sum(float(i['quantity']) * float(i['price']) for i in items)

        # Create Sale Record
        sale_res = supabase.table('sales').insert({
            "total_amount": total_amount
            # "user_id": session.get('user_id') # auth pending
        }).execute()

        new_sale = sale_res.data[0]

        sale_items_data = []
        for i in items:
            # Prepare Sale item
            sale_items_data.append({
                "sale_id": new_sale['id'],
                "product_id": i['product_id'],
                "quantity": i['quantity'],
                "unit_price": i['price']
            })
            
            # Deduct Inventory
            curr_stock = supabase.table('inventory').select('stock_level').eq('product_id', i['product_id']).execute().data[0]['stock_level']
            supabase.table('inventory').update({"stock_level": curr_stock - int(i['quantity'])}).eq('product_id', i['product_id']).execute()

        # Insert all sale items
        supabase.table('sale_items').insert(sale_items_data).execute()

        return jsonify({"success": True, "message": "Checkout successful", "sale_id": new_sale['id']})

    except Exception as e:
        return jsonify({"error": str(e)}), 400

import csv
from flask import Response
import io

@sales_bp.route('/export_csv')
def export_csv():
    if not supabase:
        return "Database error", 500
        
    res = supabase.table('sales').select("*, sale_items(*, products(name))").order('created_at', desc=True).execute()
    sales_data = res.data
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Sale ID', 'Date', 'Total Amount', 'Items Summary'])
    
    for sale in sales_data:
        items = ", ".join([f"{i['products']['name']} (x{i['quantity']})" for i in sale.get('sale_items', [])])
        writer.writerow([sale['id'], sale['created_at'], sale['total_amount'], items])
        
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=sales_export.csv"}
    )

@sales_bp.route('/invoice/<int:sale_id>')
def invoice(sale_id):
    if not supabase:
        return "Database error", 500
    try:
        # Fetch the entire exact sale record including the joined item line items
        res = supabase.table('sales').select("*, sale_items(*, products(name))").eq('id', sale_id).execute()
        if not res.data:
            return "Invoice not found", 404
            
        sale_data = res.data[0]
        return render_template('invoice.html', sale=sale_data)
        
    except Exception as e:
        return str(e), 500

