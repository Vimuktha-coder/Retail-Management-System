from flask import Blueprint, render_template, request, flash, jsonify
from db import supabase

procurement_bp = Blueprint('procurement', __name__, url_prefix='/procurement')

@procurement_bp.route('/')
def index():
    if not supabase:
        flash("Database connection not established.", "error")
        return render_template('procurement.html', suppliers=[], pur_orders=[])

    try:
        # Fetch Suppliers
        sup_res = supabase.table('suppliers').select('*').execute()
        suppliers = sup_res.data

        # Fetch Purchase Orders with supplier info
        po_res = supabase.table('purchase_orders').select('*, suppliers(name)').order('created_at', desc=True).execute()
        pur_orders = po_res.data
        
        # Fetch products for PO creation dropdown
        prod_res = supabase.table('products').select("id, name, cost").execute()
        products = prod_res.data

        return render_template('procurement.html', suppliers=suppliers, pur_orders=pur_orders, products=products)
    except Exception as e:
        flash(f"Error fetching procurement info: {str(e)}", "error")
        return render_template('procurement.html', suppliers=[], pur_orders=[])

@procurement_bp.route('/add_supplier', methods=['POST'])
def add_supplier():
    if not supabase: return jsonify({"error": "No DB connection"}), 500
    try:
        data = request.json
        name = data.get('name')
        if not name: return jsonify({"error": "Name is required"}), 400
        
        name = name.strip()

        # Check for duplicate
        existing = supabase.table('suppliers').select('id').ilike('name', name).execute()
        if existing.data:
            return jsonify({"error": "A supplier with this name already exists"}), 400

        res = supabase.table('suppliers').insert({
            "name": name,
            "contact_email": data.get('email'),
            "phone": data.get('phone'),
            "address": data.get('address')
        }).execute()

        return jsonify({"success": True, "message": "Supplier added", "data": res.data[0]})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@procurement_bp.route('/create_po', methods=['POST'])
def create_po():
    if not supabase: return jsonify({"error": "No DB connection"}), 500
    try:
        data = request.json
        supplier_id = data.get('supplier_id')
        items = data.get('items') # List of {product_id, quantity, unit_cost}
        
        if not items or len(items) == 0:
            return jsonify({"error": "Cannot create empty PO"}), 400

        total_cost = sum(float(i['quantity']) * float(i['unit_cost']) for i in items)

        # Insert PO
        po_res = supabase.table('purchase_orders').insert({
            "supplier_id": supplier_id,
            "status": "Pending",
            "total_cost": total_cost,
            # "created_by": session.get('user_id') # Requires Auth implementation
        }).execute()
        
        new_po = po_res.data[0]

        # Insert items
        po_items = []
        for i in items:
            po_items.append({
                "po_id": new_po['id'],
                "product_id": i['product_id'],
                "quantity": i['quantity'],
                "unit_cost": i['unit_cost']
            })
        
        supabase.table('po_items').insert(po_items).execute()

        return jsonify({"success": True, "message": "Purchase Order Created"})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@procurement_bp.route('/receive_po/<int:po_id>', methods=['POST'])
def receive_po(po_id):
    if not supabase: return jsonify({"error": "No DB connection"}), 500
    try:
        # Check PO status
        po_res = supabase.table('purchase_orders').select('*').eq('id', po_id).execute()
        if not po_res.data:
            return jsonify({"error": "PO not found"}), 404
        if po_res.data[0]['status'] == 'Completed':
            return jsonify({"error": "Already completed"}), 400

        # Fetch PO Items
        items_res = supabase.table('po_items').select('*').eq('po_id', po_id).execute()
        
        # Update Inventory
        for item in items_res.data:
             # get current inv
             inv_res = supabase.table('inventory').select('*').eq('product_id', item['product_id']).execute()
             if inv_res.data:
                 new_stock = inv_res.data[0]['stock_level'] + item['quantity']
                 supabase.table('inventory').update({"stock_level": new_stock}).eq('product_id', item['product_id']).execute()
             else:
                 # Should not happen as inventory record created with product, but fallback
                 supabase.table('inventory').insert({
                     "product_id": item['product_id'],
                     "stock_level": item['quantity']
                 }).execute()

        # Mark PO as completed
        supabase.table('purchase_orders').update({"status": "Completed"}).eq('id', po_id).execute()

        return jsonify({"success": True, "message": "PO Received & Inventory Updated"})
    except Exception as e:
        return jsonify({"error": str(e)}), 400
