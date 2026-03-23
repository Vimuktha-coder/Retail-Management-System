import os
import requests
from db import supabase

class ChatbotService:
    def __init__(self, api_key):
        self.api_key = api_key
        # Connect strictly to Google Gemini Flash (Free Tier)
        self.api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={self.api_key}"

    def get_system_context(self):
        context_str = "You are a helpful Retail Store AI Assistant.\nSystem Data Summary:\n"
        if not supabase:
            return context_str + "Database not connected."
            
        try:
            prod_cnt = len(supabase.table('products').select('id').execute().data)
            low_inv = len(supabase.table('inventory').select('id').lte('stock_level', 10).execute().data)
            context_str += f"- Total Products: {prod_cnt}\n"
            context_str += f"- Products Low on Stock: {low_inv}\n"
            context_str += "Help the user navigate the system. POS is at /sales/pos. Inventory is at /inventory."
        except Exception:
            context_str += "Could not load real-time db metrics."
            
        return context_str

    def get_response(self, user_message):
        if not self.api_key:
             return "AI Chatbot API Key is missing. Please configure GEMINI_API_KEY in .env."

        headers = {
            "Content-Type": "application/json"
        }
        
        prompt = f"System Context: {self.get_system_context()}\nUser Request: {user_message}"
        
        payload = {
            "contents": [
                {
                    "parts": [{"text": prompt}]
                }
            ]
        }

        try:
            res = requests.post(self.api_url, json=payload, headers=headers, timeout=10)
            if res.status_code == 200:
                data = res.json()
                return data['candidates'][0]['content']['parts'][0]['text'].strip()
            else:
                return f"Sorry, AI API Error: {res.text}"
        except Exception as e:
            return f"Error computing response: {str(e)}"
