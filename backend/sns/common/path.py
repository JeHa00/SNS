from pathlib import Path
from typing import Final

BASE_DIR: Final = Path(__file__).resolve().parents[2]
APP_DIR: Final = BASE_DIR / "sns"
EMAIL_TEMPLATE_DIR: Final = APP_DIR / "users" / "email_templates"
