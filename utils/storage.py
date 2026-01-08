import json
from pathlib import Path
class UserStorage:
    def __init__(self):
        self.path = Path("data/users.json")
        self.path.parent.mkdir(exist_ok=True)
        if not self.path.exists(): 
            with open(self.path, "w") as f: json.dump({}, f)
    def get_system_stats(self):
        return {"users": 0}
