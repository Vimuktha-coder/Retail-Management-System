-- Retail Store Management System Database Schema (PostgreSQL via Supabase)

-- 1. Roles table
CREATE TABLE IF NOT EXISTS public.roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL
);

-- Insert default roles
INSERT INTO public.roles (name) VALUES ('Admin'), ('Staff') ON CONFLICT DO NOTHING;

-- 2. Users table
CREATE TABLE IF NOT EXISTS public.users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role_id INTEGER REFERENCES public.roles(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    last_login_at TIMESTAMP WITH TIME ZONE
);

-- 3. Categories table
CREATE TABLE IF NOT EXISTS public.categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT
);

-- 4. Products table
CREATE TABLE IF NOT EXISTS public.products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    sku VARCHAR(100) UNIQUE NOT NULL,
    category_id INTEGER REFERENCES public.categories(id) ON DELETE SET NULL,
    price NUMERIC(10, 2) NOT NULL CHECK (price >= 0),
    cost NUMERIC(10, 2) NOT NULL CHECK (cost >= 0),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 5. Inventory table
CREATE TABLE IF NOT EXISTS public.inventory (
    id SERIAL PRIMARY KEY,
    product_id INTEGER UNIQUE REFERENCES public.products(id) ON DELETE CASCADE,
    stock_level INTEGER NOT NULL DEFAULT 0 CHECK (stock_level >= 0),
    low_stock_threshold INTEGER NOT NULL DEFAULT 10 CHECK (low_stock_threshold >= 0),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 6. Suppliers table
CREATE TABLE IF NOT EXISTS public.suppliers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    contact_email VARCHAR(255),
    phone VARCHAR(50),
    address TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 7. Purchase Orders (Procurement)
CREATE TABLE IF NOT EXISTS public.purchase_orders (
    id SERIAL PRIMARY KEY,
    supplier_id INTEGER REFERENCES public.suppliers(id) ON DELETE SET NULL,
    status VARCHAR(50) DEFAULT 'Pending', -- Pending, Completed, Cancelled
    total_cost NUMERIC(12, 2) DEFAULT 0.00,
    created_by UUID REFERENCES public.users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 8. Purchase Order Items
CREATE TABLE IF NOT EXISTS public.po_items (
    id SERIAL PRIMARY KEY,
    po_id INTEGER REFERENCES public.purchase_orders(id) ON DELETE CASCADE,
    product_id INTEGER REFERENCES public.products(id),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_cost NUMERIC(10, 2) NOT NULL CHECK (unit_cost >= 0)
);

-- 9. Sales table
CREATE TABLE IF NOT EXISTS public.sales (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES public.users(id),
    total_amount NUMERIC(12, 2) NOT NULL DEFAULT 0.00,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 10. Sale Items table
CREATE TABLE IF NOT EXISTS public.sale_items (
    id SERIAL PRIMARY KEY,
    sale_id INTEGER REFERENCES public.sales(id) ON DELETE CASCADE,
    product_id INTEGER REFERENCES public.products(id),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price NUMERIC(10, 2) NOT NULL CHECK (unit_price >= 0)
);

-- ==============================================
-- Row Level Security (RLS) Policies
-- ==============================================

-- Enable RLS on all tables
ALTER TABLE public.roles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.categories ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.products ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.inventory ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.suppliers ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.purchase_orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.po_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.sales ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.sale_items ENABLE ROW LEVEL SECURITY;

-- Note: Since we are using Supabase Python Client Server-Side with SERVICE_ROLE key or securely from backend,
-- The backend (Flask API) acts as an admin. We can bypass RLS via the service role key,
-- or create explicit policies if the UI connects directly to Supabase.
-- Assuming backend proxy:
-- Create a blanket policy allowing access for authenticated service roles (or all via our secure API)
CREATE POLICY "Allow full access to authenticated roles" ON public.users FOR ALL USING (true);
CREATE POLICY "Allow full access to authenticated roles" ON public.roles FOR ALL USING (true);
CREATE POLICY "Allow full access to authenticated roles" ON public.categories FOR ALL USING (true);
CREATE POLICY "Allow full access to authenticated roles" ON public.products FOR ALL USING (true);
CREATE POLICY "Allow full access to authenticated roles" ON public.inventory FOR ALL USING (true);
CREATE POLICY "Allow full access to authenticated roles" ON public.suppliers FOR ALL USING (true);
CREATE POLICY "Allow full access to authenticated roles" ON public.purchase_orders FOR ALL USING (true);
CREATE POLICY "Allow full access to authenticated roles" ON public.po_items FOR ALL USING (true);
CREATE POLICY "Allow full access to authenticated roles" ON public.sales FOR ALL USING (true);
CREATE POLICY "Allow full access to authenticated roles" ON public.sale_items FOR ALL USING (true);
