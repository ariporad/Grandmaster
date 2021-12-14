import asyncio
from game_controller import GameController
from dashboard import configure_dashboard, get_dashboard, GRANDMASTER_ASCII_ART

print(GRANDMASTER_ASCII_ART)

print("Connecting...")

configure_dashboard(GameController())

print("Ready")

asyncio.run(get_dashboard().main())