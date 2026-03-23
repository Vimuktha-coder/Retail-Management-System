from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from db import supabase
import bcrypt
import datetime

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not email or not password:
            flash('Email and password are required', 'error')
            return render_template('login.html')
            
        try:
            # Fetch user by email
            res = supabase.table('users').select('*, roles(name)').eq('email', email).execute()
            if not res.data:
                flash('Invalid email or password', 'error')
                return render_template('login.html')
                
            user = res.data[0]
            
            # Verify password
            stored_hash = user['password_hash'].encode('utf-8')
            if not bcrypt.checkpw(password.encode('utf-8'), stored_hash):
                flash('Invalid email or password', 'error')
                return render_template('login.html')
                
            # Set session
            session['user_id'] = str(user['id'])
            session['user_email'] = user['email']
            session['role'] = user['roles']['name'] if user.get('roles') else 'Staff'
            
            # Update last login
            supabase.table('users').update({'last_login_at': datetime.datetime.utcnow().isoformat()}).eq('id', user['id']).execute()
            
            return redirect(url_for('dashboard'))
            
        except Exception as e:
            flash(f"Login error: {str(e)}", "error")
            return render_template('login.html')
            
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('auth.login'))

@auth_bp.route('/setup_default_users')
def setup_default_users():
    try:
        if not supabase:
            return "No DB connection", 500
            
        # Check if roles exist
        roles_res = supabase.table('roles').select('*').execute()
        roles = {r['name']: r['id'] for r in roles_res.data}
        
        if 'Admin' not in roles or 'Staff' not in roles:
            # Create roles if they don't exist
            roles_to_insert = []
            if 'Admin' not in roles: roles_to_insert.append({'name': 'Admin'})
            if 'Staff' not in roles: roles_to_insert.append({'name': 'Staff'})
            
            if roles_to_insert:
                supabase.table('roles').insert(roles_to_insert).execute()
                
            roles_res = supabase.table('roles').select('*').execute()
            roles = {r['name']: r['id'] for r in roles_res.data}

        password_raw = "password123"
        hashed_pw = bcrypt.hashpw(password_raw.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        users_to_create = [
            {'email': 'admin@retail.com', 'password_hash': hashed_pw, 'role_id': roles.get('Admin')},
            {'email': 'staff@retail.com', 'password_hash': hashed_pw, 'role_id': roles.get('Staff')}
        ]
        
        created = 0
        for u in users_to_create:
            existing = supabase.table('users').select('id').eq('email', u['email']).execute()
            if not existing.data:
                supabase.table('users').insert(u).execute()
                created += 1
                
        return f"Setup complete. {created} new users created. <a href='{url_for('auth.login')}'>Go to Login</a>"
    except Exception as e:
        return f"Error: {str(e)}"
