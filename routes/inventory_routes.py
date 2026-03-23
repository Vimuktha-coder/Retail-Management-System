from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from db import supabase
from werkzeug.exceptions import BadRequest

inventory_bp = Blueprint('inventory', __name__, url_prefix='/inventory')

@inventory_bp.route('/')
def index():
    if not supabase:
        flash("Database connection not established.", "error")
        return render_template('inventory.html', products=[])
    
    try:
        # Fetch products with their category and inventory details
        # We simulate a join by fetching multiple and matching, or using Supabase's select
        # Example Supabase syntax: select="*, categories(name), inventory(stock_level, low_stock_threshold)"
        response = supabase.table('products').select(
            "*, categories(name), inventory(stock_level, low_stock_threshold)"
        ).execute()
        
        products_data = response.data
        
        # Also fetch categories for the 'Add Product' modal
        categories_response = supabase.table('categories').select("*").execute()
        categories = categories_response.data

        return render_template('inventory.html', products=products_data, categories=categories)
    except Exception as e:
        flash(f"Error fetching inventory: {str(e)}", "error")
        return render_template('inventory.html', products=[], categories=[])

@inventory_bp.route('/add_product', methods=['POST'])
def add_product():
    from flask import session
    if session.get('role') != 'Admin':
        return jsonify({"error": "Admin privileges required"}), 403
    if not supabase:
        return jsonify({"error": "No DB connection"}), 500
        
    try:
        data = request.json
        name = data.get('name')
        sku = data.get('sku')
        category_id = data.get('category_id')
        price = float(data.get('price'))
        cost = float(data.get('cost'))
        initial_stock = int(data.get('initial_stock', 0))
        threshold = int(data.get('threshold', 10))

        if not all([name, sku, category_id, price, cost]):
            return jsonify({"error": "Missing required fields"}), 400

        # Insert product
        prod_response = supabase.table('products').insert({
            "name": name,
            "sku": sku,
            "category_id": int(category_id),
            "price": price,
            "cost": cost
        }).execute()

        new_product = prod_response.data[0]

        # Insert inventory
        supabase.table('inventory').insert({
            "product_id": new_product['id'],
            "stock_level": initial_stock,
            "low_stock_threshold": threshold
        }).execute()

        return jsonify({"success": True, "message": "Product added successfully", "product": new_product})

    except Exception as e:
        return jsonify({"error": str(e)}), 400

@inventory_bp.route('/update_stock', methods=['POST'])
def update_stock():
    if not supabase:
         return jsonify({"error": "No DB connection"}), 500
         
    try:
        data = request.json
        product_id = data.get('product_id')
        new_quantity = int(data.get('quantity'))
        
        # Fetch current stock
        inv_record = supabase.table('inventory').select("*").eq('product_id', product_id).execute()
        if not inv_record.data:
            return jsonify({"error": "Inventory record not found"}), 404
            
        current_inv = inv_record.data[0]
        
        # Check low stock threshold alert (just returning flag for now)
        is_low = new_quantity <= current_inv['low_stock_threshold']

        supabase.table('inventory').update({"stock_level": new_quantity}).eq('product_id', product_id).execute()
        
        return jsonify({
            "success": True, 
            "message": "Stock updated", 
            "new_level": new_quantity,
            "is_low": is_low
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@inventory_bp.route('/add_category', methods=['POST'])
def add_category():
    from flask import session
    if session.get('role') != 'Admin':
        return jsonify({"error": "Admin privileges required"}), 403
    if not supabase:
        return jsonify({"error": "No DB connection"}), 500
        
    try:
        data = request.json
        name = data.get('name')
        
        if not name or not name.strip():
            return jsonify({"error": "Category name is required"}), 400
            
        name = name.strip()
        
        # Insert category
        cat_response = supabase.table('categories').insert({
            "name": name
        }).execute()
        
        new_category = cat_response.data[0]
        
        return jsonify({"success": True, "message": "Category created successfully", "category": new_category})

    except Exception as e:
        # Supabase raises an error if the unique constraint on 'name' is violated
        error_msg = str(e)
        if 'duplicate key value violates unique constraint' in error_msg.lower():
            return jsonify({"error": "Category already exists"}), 400
        return jsonify({"error": f"Failed to create category: {error_msg}"}), 400

@inventory_bp.route('/delete_out_of_stock', methods=['DELETE'])
def delete_out_of_stock():
    from flask import session
    if session.get('role') != 'Admin':
         return jsonify({"error": "Admin privileges required"}), 403
    if not supabase:
         return jsonify({"error": "No DB connection"}), 500

    try:
        # Fetch all products and their attached inventory
        products_res = supabase.table('products').select('id, inventory(stock_level)').execute()
        
        product_ids = []
        for p in products_res.data:
            inv = p.get('inventory')
            
            # If no inventory record at all, it's essentially 0 stock
            if not inv:
                product_ids.append(p['id'])
            # Sometimes Supabase returns an array for relationships
            elif isinstance(inv, list) and len(inv) > 0 and inv[0].get('stock_level', 0) == 0:
                product_ids.append(p['id'])
            # Sometimes it returns a direct dictionary
            elif isinstance(inv, dict) and inv.get('stock_level', 0) == 0:
                product_ids.append(p['id'])
        
        if not product_ids:
             return jsonify({"success": True, "message": "No out of stock products found."})
             
        # Delete inventory records first (to clear foreign keys before deleting products)
        supabase.table('inventory').delete().in_('product_id', product_ids).execute()
        
        # Finally delete the products themselves
        supabase.table('products').delete().in_('id', product_ids).execute()
        
        return jsonify({"success": True, "message": f"Successfully deleted {len(product_ids)} out-of-stock products."})
        
    except Exception as e:
        error_msg = str(e)
        if 'violates foreign key constraint' in error_msg.lower():
            return jsonify({"error": "Cannot delete products that have existing historical sales records. Please restock them instead."}), 400
        return jsonify({"error": error_msg}), 400
