"""Compose migration companion: seed only the explicitly enabled fictional demo."""

from akus.config import Settings
from akus.seed import main as seed_demo

if __name__ == "__main__":
    if Settings().demo_enabled:
        seed_demo()
    else:
        print(
            "Institutional mode: fictional seeding skipped. Approved roster provisioning required."
        )
