import psycopg2
import json
from psycopg2.extras import RealDictCursor

# Database connection
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'voice',
    'user': 'voice',
    'password': 'voice'
}

# LM Studio configuration
LM_STUDIO_CONFIG = {
    "llm_provider": "openai_compat",
    "llm_model": "qwen3-8b-192k-josiefied-uncensored-neo-max",
    "llm_base_url": "http://192.168.40.69:1234/v1",
    "llm_temperature": 0.2,
    "llm_top_p": 1.0,
    "llm_max_input_tokens": 4000,
    "llm_max_output_tokens": 512,
    "whisper_model": "base"
}

def update_settings():
    try:
        # Connect to database
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        print("✓ Connected to database")
        
        # Check if settings table exists and has data
        cursor.execute("SELECT COUNT(*) FROM settings")
        count = cursor.fetchone()['count']
        
        if count == 0:
            # Insert new settings
            cursor.execute("""
                INSERT INTO settings (model_config, secrets_config, created_at, updated_at)
                VALUES (%s, %s, NOW(), NOW())
            """, (json.dumps(LM_STUDIO_CONFIG), json.dumps({})))
            print("✓ Inserted new LM Studio settings")
        else:
            # Update existing settings
            cursor.execute("""
                UPDATE settings 
                SET model_config = %s, updated_at = NOW()
                WHERE id = (SELECT id FROM settings LIMIT 1)
            """, (json.dumps(LM_STUDIO_CONFIG),))
            print("✓ Updated existing settings with LM Studio config")
        
        # Commit changes
        conn.commit()
        
        # Verify the update
        cursor.execute("SELECT model_config FROM settings LIMIT 1")
        result = cursor.fetchone()
        if result:
            config = result['model_config']
            print(f"✓ Current model config: {json.dumps(config, indent=2)}")
        
        cursor.close()
        conn.close()
        print("✓ Database connection closed")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()

if __name__ == "__main__":
    print("Configuring VoiceStack2 for LM Studio...")
    print(f"Target: {LM_STUDIO_CONFIG['llm_base_url']}")
    print(f"Model: {LM_STUDIO_CONFIG['llm_model']}")
    print()
    update_settings()
    print()
    print("Configuration complete! The next audio processing job will use LM Studio for metadata generation.") 