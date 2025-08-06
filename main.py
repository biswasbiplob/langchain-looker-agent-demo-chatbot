import os
from app import app

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    print(f"🚀 Starting Looker Chatbot on port {port}...")
    # Disable debug mode to avoid process reloading issues with JVM
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
