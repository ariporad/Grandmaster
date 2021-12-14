import asyncio
import chess
from prompt_toolkit import Application
from prompt_toolkit import completion
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.completion import NestedCompleter
from prompt_toolkit.completion.base import Completer
from prompt_toolkit.formatted_text.base import FormattedText
from prompt_toolkit.key_binding.key_bindings import KeyBindings
from prompt_toolkit.layout.containers import HSplit, VSplit, Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.widgets.base import TextArea

GRANDMASTER_ASCII_ART = """
Welcome to
   ______                     __                     __           
  / ____/________ _____  ____/ /___ ___  ____ ______/ /____  _____
 / / __/ ___/ __ `/ __ \/ __  / __ `__ \/ __ `/ ___/ __/ _ \/ ___/
/ /_/ / /  / /_/ / / / / /_/ / / / / / / /_/ (__  ) /_/  __/ /    
\____/_/   \__,_/_/ /_/\__,_/_/ /_/ /_/\__,_/____/\__/\___/_/     
                                                                  
                                                 Let's Play a Game
""".strip()

dashboard = None

def configure_dashboard(game: 'GameController'):
	global dashboard
	dashboard = Dashboard(game)
	
def get_dashboard():
	return dashboard

class Dashboard:
	content_view: FormattedTextControl
	input_view: TextArea
	app: Application
	text: str = 'Connected!\n'
	
	game: 'GameController'

	def __init__(self, game: 'GameController') -> None:
		"""
		DO NOT INSTANTIATE DIRECTLY! SINGLETON! USE configure_dashboard!
		"""
		self.content_view = FormattedTextControl()
		self.text_area = TextArea(
			multiline=False,
			prompt='→ ',
			style='bg:ansiwhite ansiblack',
			accept_handler=self.on_input,
			completer=self.completer,
			complete_while_typing=True,
		)
		self.game = game
		self.app = Application(
			layout=self.layout,
			key_bindings=self.key_bindings,
			full_screen=True,
			erase_when_done=False,
			refresh_interval=0.1,
		)

	def print(self, *args):
		self.text += ' '.join(str(x) for x in args) + '\n'
		self.content_view.text = FormattedText([('', self.text), ('[SetCursorPosition]', '')])

	def on_input(self, text: Buffer):
		text = text.text.strip()
		# TODO: parse input
	
	@property
	def completer(self) -> Completer:
		return NestedCompleter({
			'move': chess.SQUARE_NAMES,
			'setpos': None,
			'magnet': {'on', 'off'},
			'bled': {'player', 'computer', 'start', 'fun'},
			'exit': None
		})

	@property
	def key_bindings(self) -> KeyBindings:
		kb = KeyBindings()

		@kb.add("c-c")
		@kb.add("c-q")
		def _(event):
			"Pressing Ctrl-Q or Ctrl-C will exit the dashboard."
			event.app.exit()
		
		return kb

	@property
	def logo_window(self) -> Window:
		return Window(
			FormattedTextControl(GRANDMASTER_ASCII_ART, show_cursor=False, focusable=False),
			style='bg:ansiblue',
			dont_extend_height=True
		)
	
	@property
	def status_window(self) -> Window:
		return VSplit(
			style='bg:ansiblue',
			children=[
				Window(FormattedTextControl("Grandmaster OK")),
				Window(
					FormattedTextControl(
						show_cursor=False, focusable=False,
						text=f"State: {self.game.state.name}. Gantry at {self.game.arduino.gantry_pos}. Magnet {'ON' if self.game.arduino.electromagnet_enabled else 'OFF'}.",
					),
					dont_extend_height=True,
					dont_extend_width=True
				)
			]
		)

	@property
	def layout(self) -> Layout:
		return Layout(
		    HSplit([
				self.logo_window,
		        Window(self.content_view),
				self.text_area,
				self.status_window
		    ]),
			focused_element=self.text_area
		)

	async def main(self):
		app_task = asyncio.create_task(self.app.run_async())
		game_task = asyncio.create_task(self.game.main())

		await game_task
		await app_task
