"""
Quick Setup Script for XAMPP MySQL Integration
One-command setup for database connection
"""

import sys
import os
import subprocess

def print_header(text):
    """Print formatted header"""
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70 + "\n")

def check_xampp():
    """Check if XAMPP MySQL is accessible"""
    print_header("🔍 CHECKING XAMPP MYSQL")
    
    try:
        import pymysql
        
        # Try to connect
        connection = pymysql.connect(
            host='localhost',
            port=3306,
            user='root',
            password=''
        )
        connection.close()
        print("✅ XAMPP MySQL is running and accessible")
        return True
        
    except ImportError:
        print("❌ pymysql not installed")
        print("   Installing required packages...")
        return False
        
    except Exception as e:
        print(f"❌ Cannot connect to XAMPP MySQL: {e}")
        print("\n⚠️ Please start XAMPP MySQL:")
        print("   1. Open XAMPP Control Panel")
        print("   2. Click 'Start' next to MySQL")
        print("   3. Wait for it to turn green")
        print("   4. Run this script again")
        return False

def install_dependencies():
    """Install required Python packages"""
    print_header("📦 INSTALLING DEPENDENCIES")
    
    packages = [
        'pymysql',
        'sqlalchemy',
        'python-dotenv',
        'bcrypt'
    ]
    
    for package in packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package} already installed")
        except ImportError:
            print(f"📥 Installing {package}...")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
            print(f"✅ {package} installed")
    
    return True

def run_setup():
    """Run database setup"""
    print_header("🗄️ SETTING UP DATABASE")
    
    try:
        result = subprocess.run(
            [sys.executable, 'setup_database.py'],
            cwd=os.path.dirname(os.path.abspath(__file__)),
            capture_output=False
        )
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        return False

def run_tests():
    """Run connection tests"""
    print_header("🧪 TESTING CONNECTION")
    
    try:
        result = subprocess.run(
            [sys.executable, 'test_database_connection.py'],
            cwd=os.path.dirname(os.path.abspath(__file__)),
            capture_output=False
        )
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ Tests failed: {e}")
        return False

def show_next_steps():
    """Show next steps"""
    print_header("🎉 SETUP COMPLETE!")
    
    print("Your database is ready! Here's what you can do next:\n")
    
    print("1️⃣ Access phpMyAdmin:")
    print("   http://localhost/phpmyadmin")
    print("   Database: aphasia_therapy_db\n")
    
    print("2️⃣ Start the backend server:")
    print("   cd backend/api")
    print("   python run_server.py\n")
    
    print("3️⃣ Start the frontend:")
    print("   cd frontend")
    print("   npm start\n")
    
    print("4️⃣ Login with sample credentials:")
    print("   Patient: patient@example.com / demo123")
    print("   Clinician: clinician@example.com / demo123\n")
    
    print("📚 For detailed documentation, see:")
    print("   XAMPP_DATABASE_SETUP.md\n")
    
    print("="*70 + "\n")

def main():
    """Main setup flow"""
    print("\n" + "="*70)
    print("  🚀 APHASIA THERAPY - XAMPP MYSQL QUICK SETUP")
    print("="*70)
    print("\nThis script will:")
    print("  ✓ Check XAMPP MySQL connection")
    print("  ✓ Install required Python packages")
    print("  ✓ Create database and tables")
    print("  ✓ Insert sample data")
    print("  ✓ Test the connection")
    print("\n" + "="*70)
    
    input("\nPress ENTER to continue...")
    
    # Step 1: Install dependencies
    if not install_dependencies():
        print("\n❌ Failed to install dependencies")
        return False
    
    # Step 2: Check XAMPP
    if not check_xampp():
        print("\n❌ XAMPP MySQL is not accessible")
        print("\nPlease start XAMPP MySQL and run this script again:")
        print(f"  python {os.path.basename(__file__)}")
        return False
    
    # Step 3: Run setup
    if not run_setup():
        print("\n❌ Database setup failed")
        return False
    
    # Step 4: Run tests
    if not run_tests():
        print("\n⚠️ Some tests failed, but database might still work")
    
    # Step 5: Show next steps
    show_next_steps()
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️ Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
