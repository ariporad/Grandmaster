"""
The entry point to the Game Controller. Run this file (usually in the form of `python3 main`) to
start the server.
"""
import asyncio
from dashboard_delegate import DashboardDelegateThread
from dashboard import configure_dashboard, get_dashboard, GRANDMASTER_ASCII_ART

print(GRANDMASTER_ASCII_ART)

print("Connecting...")

async def main():
	thread = DashboardDelegateThread(main_thread_loop=asyncio.get_running_loop())
	thread.start()

	# Wait for the thread to be ready, but don't hold the lock
	thread.wait_for_ready.acquire()
	thread.wait_for_ready.release()
	print("Connected")

	configure_dashboard(thread)

	await get_dashboard().app.run_async()

asyncio.run(main())