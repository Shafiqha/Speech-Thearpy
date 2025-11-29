"""
Run database migration to add user_difficulty_progress table
"""
import pymysql
from database.config import DB_CONFIG

def run_migration():
    """Execute the migration SQL"""
    
    print("🔄 Running database migration...")
    
    try:
        # Connect to MySQL
        connection = pymysql.connect(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            database=DB_CONFIG['database'],
            charset='utf8mb4'
        )
        
        with connection.cursor() as cursor:
            # Read and execute migration SQL
            import os
            script_dir = os.path.dirname(os.path.abspath(__file__))
            sql_file = os.path.join(script_dir, 'database', 'add_difficulty_progress_table.sql')
            
            with open(sql_file, 'r') as f:
                sql = f.read()
                cursor.execute(sql)
            
            connection.commit()
            print("✅ Migration completed successfully!")
            print("   - Added table: user_difficulty_progress")
            
            # Verify table was created
            cursor.execute("SHOW TABLES LIKE 'user_difficulty_progress'")
            result = cursor.fetchone()
            if result:
                print("✅ Table verified in database")
            else:
                print("⚠️ Table not found after migration")
        
        connection.close()
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = run_migration()
    if success:
        print("\n🎉 Database is ready!")
        print("   Restart your backend server to use the new table.")
    else:
        print("\n❌ Migration failed. Check the error above.")
