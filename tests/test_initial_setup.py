"""
Initial Setup and Integration Test
"""
import sys
from pathlib import Path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from database.db_manager import db
from services.synthetic_generator import SyntheticDataGenerator
from services.dataset_manager import DatasetManager

def test_setup_and_samples():
    # Insert default supporting tables (barns, sensors)
    db.execute("INSERT OR REPLACE INTO barns (barn_id, barn_name, location, capacity) VALUES ('BARN-A', 'Main Lactating Barn', 'North Wing', 60)")
    db.execute("INSERT OR REPLACE INTO barns (barn_id, barn_name, location, capacity) VALUES ('BARN-B', 'Dry Cow & Heifer Barn', 'South Wing', 40)")
    db.execute("INSERT OR REPLACE INTO barns (barn_id, barn_name, location, capacity) VALUES ('BARN-C', 'Calf Nursery', 'East Wing', 20)")
    db.execute("INSERT OR REPLACE INTO barns (barn_id, barn_name, location, capacity) VALUES ('BARN-D', 'Bull Pens', 'West Wing', 10)")

    print("Generating synthetic sample datasets...")
    gen = SyntheticDataGenerator(seed=42)
    res = gen.generate_all(days=30, cow_count=20, bull_count=4, calf_count=6)
    print("Generated:", res)

    print("Restoring sample datasets into database...")
    restore_res = DatasetManager.restore_all_samples()
    for k, v in restore_res.items():
        print(f"  {k}: {v['success']} - {v['message']}")

    summary = DatasetManager.list_datasets()
    print("\nDataset summary after restore:")
    for d in summary:
        print(f"  {d['dataset_name']}: {d['records']} records")

if __name__ == "__main__":
    test_setup_and_samples()
