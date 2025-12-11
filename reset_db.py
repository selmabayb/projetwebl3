import os
import glob
import shutil

def clean_project():
    print(">>> Cleaning project...")
    
    # 1. Delete SQLite DB
    if os.path.exists('db.sqlite3'):
        try:
            os.remove('db.sqlite3')
            print("Deleted db.sqlite3")
        except PermissionError:
            print("Could not delete db.sqlite3 (Locked?)")
            return False

    # 2. Delete Migrations
    apps = ['accounts', 'appointments', 'billing', 'cases', 'catalog', 'notifications', 'quotes', 'vehicles']
    for app in apps:
        migration_path = os.path.join('garage', app, 'migrations')
        if os.path.exists(migration_path):
            # Get all files starting with numbers (0001_...)
            files = glob.glob(os.path.join(migration_path, "[0-9]*.py"))
            for f in files:
                try:
                    os.remove(f)
                    print(f"Deleted {f}")
                except Exception as e:
                    print(f"Error deleting {f}: {e}")
            
            # Remove __pycache__ if exists
            pycache = os.path.join(migration_path, '__pycache__')
            if os.path.exists(pycache):
                try:
                    shutil.rmtree(pycache)
                    print(f"Deleted {pycache}")
                except:
                    pass

    print(">>> Clean complete.")
    return True

if __name__ == "__main__":
    clean_project()
