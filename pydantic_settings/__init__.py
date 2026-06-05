# ==============================================================================
# Brickify SecurityOS - Lightweight fallback for pydantic_settings
# ==============================================================================
import os
from pydantic import BaseModel

def SettingsConfigDict(*args, **kwargs):
    return kwargs

class BaseSettings(BaseModel):
    def __init__(self, *args, **kwargs):
        env_data = {}
        
        # 1. Look for .env in the current directory or parent directory
        env_paths = [".env", "../.env"]
        for env_path in env_paths:
            if os.path.exists(env_path):
                try:
                    with open(env_path, "r", encoding="utf-8") as f:
                        for line in f:
                            line = line.strip()
                            if not line or line.startswith("#"):
                                continue
                            if "=" in line:
                                k, v = line.split("=", 1)
                                env_data[k.strip().upper()] = v.strip()
                except Exception:
                    pass
                break # Use the first one found

        # 2. Extract values based on annotations
        init_data = {}
        for field_name, field_type in self.__annotations__.items():
            field_name_upper = field_name.upper()
            val = None
            
            # Value priority:
            # 1. Explicit kwargs
            # 2. os.environ
            # 3. .env file data
            # 4. Standard default value on the class
            if field_name in kwargs:
                val = kwargs[field_name]
            elif field_name_upper in os.environ:
                val = os.environ[field_name_upper]
            elif field_name_upper in env_data:
                val = env_data[field_name_upper]
                
            if val is not None:
                # Safe type conversion
                try:
                    # Strip quotes if present
                    if isinstance(val, str) and len(val) >= 2:
                        if (val[0] == '"' and val[-1] == '"') or (val[0] == "'" and val[-1] == "'"):
                            val = val[1:-1]
                            
                    if field_type is int:
                        val = int(val)
                    elif field_type is float:
                        val = float(val)
                    elif field_type is bool:
                        val = str(val).lower() in ("true", "1", "yes", "on")
                except Exception:
                    pass
                init_data[field_name] = val
                
        # Merge in any other fields or provided values
        for k, v in kwargs.items():
            if k not in init_data:
                init_data[k] = v

        super().__init__(**init_data)
