import asyncio
from game_controller import GameController
from dashboard_delegate import DashboardDelegate
from dashboard import configure_dashboard, get_dashboard, GRANDMASTER_ASCII_ART

print(GRANDMASTER_ASCII_ART)

print("Connecting...")

configure_dashboard(DashboardDelegate(GameController()))

print("Ready")

asyncio.run(get_dashboard().main())