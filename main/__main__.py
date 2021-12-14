import asyncio
from game_controller import GameController
from dashboard_delegate import DashboardDelegateThread
from dashboard import configure_dashboard, get_dashboard, GRANDMASTER_ASCII_ART

print(GRANDMASTER_ASCII_ART)

print("Connecting...")

async def main():
	thread = DashboardDelegateThread()
	thread.start()

	print("Waiting...")
	with thread.is_ready:
		print("Connected")

		configure_dashboard(thread)

		await get_dashboard().app.run_async()

asyncio.run(main())