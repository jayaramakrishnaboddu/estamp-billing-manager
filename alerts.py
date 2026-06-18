import streamlit as st

def floating_drop_message(text, bg_color="#00FF66", text_color="#000000"):
    st.html(f"""
        <style>
        @keyframes slideDownDrop {{
            0% {{ transform: translate(-50%, -120%); opacity: 0; }}
            100% {{ transform: translate(-50%, 0); opacity: 1; }}
        }}
        .floating-drop-alert {{
            position: fixed;
            top: 20px;
            left: 50%;
            transform: translate(-50%, 0);
            z-index: 999999;
            background-color: {bg_color}; 
            color: {text_color}; 
            padding: 16px 32px; 
            border-radius: 12px; 
            font-weight: bold;
            font-size: 16px;
            box-shadow: 0px 8px 24px rgba(0,0,0,0.3);
            min-width: 300px;
            text-align: center;
            animation: slideDownDrop 0.5s ease-out forwards;
        }}
        </style>
        <div class="floating-drop-alert">
            {text}
        </div>
    """)
