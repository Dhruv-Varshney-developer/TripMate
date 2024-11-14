from typing import Optional

from pydantic import BaseModel

from browser_use.dom.views import ProcessedDomContent


# Pydantic
class TabInfo(BaseModel):
	"""Represents information about a browser tab"""

	handle: str
	url: str
	title: str


class BrowserState(ProcessedDomContent):
	url: str
	title: str
	current_tab_handle: str
	tabs: list[TabInfo]
	screenshot: Optional[str] = None

	def model_dump(self) -> dict:
		dump = super().model_dump()
		# Add a summary of available tabs
		if self.tabs:
			dump['available_tabs'] = [
				f'Tab {i+1}: {tab.title} ({tab.url})' for i, tab in enumerate(self.tabs)
			]
		return dump
