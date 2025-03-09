"""
Playwright browser on steroids.
"""

import asyncio
import gc
import logging
import os
import shutil
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
from zipfile import ZipFile

import requests
from playwright._impl._api_structures import ProxySettings
from playwright.async_api import Browser as PlaywrightBrowser
from playwright.async_api import (
    Playwright,
    async_playwright,
)

from browser_use.browser.context import BrowserContext, BrowserContextConfig
from browser_use.utils import time_execution_async

logger = logging.getLogger(__name__)


@dataclass
class ExtensionConfig:
    r"""
    Configuration for the Extension.

    name: name of Chrome extension

    github_url: GitHub URL from where it can be downloaded

    """
    name: str
    github_url: str
    install_path: Optional[Path] | None = None


@dataclass
class BrowserConfig:
    r"""
    Configuration for the Browser.

    Default values:
        headless: True
            Whether to run browser in headless mode

        disable_security: True
            Disable browser security features

        extra_chromium_args: []
            Extra arguments to pass to the browser

        wss_url: None
            Connect to a browser instance via WebSocket

        cdp_url: None
            Connect to a browser instance via CDP

        chrome_instance_path: None
            Path to a Chrome instance to use to connect to your normal browser
            e.g. '/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome'

        chrome_profile_data: None
            Path to a Chrome instance to use to connect to your normal browser
            e.g. '/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome'

        extensions: [{name, github_url}]
            Mention the names of chrome extensions, and their urls from where it should be installed
            e.g. {name: 'ublock-lite', github_url: 'https://github.com/uBlockOrigin/uBOL-home'}
    """

    headless: bool = False
    disable_security: bool = True
    extra_chromium_args: list[str] = field(default_factory=list)
    chrome_instance_path: str | None = None
    chrome_profile_data: str | None = None
    extensions: list[ExtensionConfig] | None = None
    wss_url: str | None = None
    cdp_url: str | None = None

    proxy: ProxySettings | None = field(default=None)
    new_context_config: BrowserContextConfig = field(default_factory=BrowserContextConfig)

    _force_keep_browser_alive: bool = False

    def __post_init__(self):
        if self.extra_chromium_args is None:
            self.extra_chromium_args = []
        if self.chrome_profile_data is None and self.extensions is not None and len(self.extensions) > 0:
            self.chrome_profile_data = tempfile.mkdtemp(prefix='browser_use_')
        if self.chrome_profile_data is not None:
            Path(self.chrome_profile_data).mkdir(parents=True, exist_ok=True)

    def has_extensions(self):
        return self.extensions is not None and len(self.extensions) > 0


def _cache_dir_extension(extension_name) -> Path:
    """Get the cache directory for uBlock extension"""
    cache_dir = Path.home() / ".cache" / "browser_use" / "extensions" / extension_name
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def convert_github_url(repo_url: str) -> str:
    if not repo_url.startswith("https://github.com/"):
        raise ValueError("Invalid GitHub repository URL")

    repo_path = repo_url.replace("https://github.com/", "")
    return f"https://api.github.com/repos/{repo_path}/releases/latest"


# @singleton: TODO - think about id singleton makes sense here
# @dev By default this is a singleton, but you can create multiple instances if you need to.
class Browser:
    """
    Playwright browser on steroids.

    This is persistant browser factory that can spawn multiple browser contexts.
    It is recommended to use only one instance of Browser per your application (RAM usage will grow otherwise).
    """

    def __init__(
            self,
            config: BrowserConfig = BrowserConfig(),
    ):
        logger.debug('Initializing new browser')
        self.config = config
        self.playwright: Playwright | None = None
        self.playwright_browser: PlaywrightBrowser | None = None

        self.disable_security_args = []
        if self.config.disable_security:
            self.disable_security_args = [
                '--disable-web-security',
                '--disable-site-isolation-trials',
                '--disable-features=IsolateOrigins,site-per-process',
            ]

    async def _add_extension_paths_as_commandline_args(self):
        extension_paths = await self._get_extension_paths()
        if len(extension_paths) > 0:
            extension_paths_cmd = ""
            for idx, path in enumerate(extension_paths):
                extension_paths_cmd += ("," if idx > 0 else "") + str(path)
            self.config.extra_chromium_args.append("--load-extension=" + extension_paths_cmd)

    async def _get_extension_paths(self) -> list[Path]:
        """
        Download and extract extensions if not already present.
        Returns path to the extension directory.
        """
        # If extension already exists and has manifest.json, use it
        extension_paths = []
        if self.config.has_extensions():
            for extension in self.config.extensions:
                if extension.install_path is None:
                    extension.install_path = _cache_dir_extension(extension.name)
                if extension.install_path.exists() and any(extension.install_path.iterdir()) and Path(
                        extension.install_path.joinpath("manifest.json")).exists():
                    logger.debug("Using cached " + extension.name + " extension")
                    extension_paths.append(extension.install_path)
                    continue

                shutil.rmtree(str(extension.install_path), ignore_errors=True)
                extension.install_path.mkdir(parents=True, exist_ok=True)

                # Download if not present
                logger.info("Downloading " + extension.name + " extension...")
                try:
                    # Get latest release info
                    response = requests.get(convert_github_url(extension.github_url))
                    response.raise_for_status()
                    release_data = response.json()

                    # Find the chromium zip asset
                    zip_asset = release_data["assets"][0]

                    # Create a temporary directory for extraction
                    with tempfile.TemporaryDirectory() as temp_dir:
                        # Download zip file
                        zip_path = os.path.join(temp_dir, "extension.zip")
                        response = requests.get(zip_asset["browser_download_url"])
                        response.raise_for_status()

                        # Save zip file
                        with open(zip_path, "wb") as f:
                            f.write(response.content)

                        # Extract to cache directory
                        with ZipFile(zip_path) as zip_file:
                            zip_file.extractall(str(extension.install_path))

                        logger.info("Successfully installed " + extension.name)

                except Exception as e:
                    logger.error(f"Failed to download " + extension.name + ": {e}")
                    raise RuntimeError("Failed to download " + extension.name + " extension") from e

                extension_paths.append(extension.install_path)
        return extension_paths

    async def new_context(self, config: BrowserContextConfig = BrowserContextConfig()) -> BrowserContext:
        """Create a browser context"""
        return BrowserContext(config=config, browser=self)

    async def get_playwright_browser(self) -> PlaywrightBrowser:
        """Get a browser context"""
        if self.playwright_browser is None:
            return await self._init()

        return self.playwright_browser

    @time_execution_async('--init (browser)')
    async def _init(self):
        """Initialize the browser session"""
        playwright = await async_playwright().start()
        browser = await self._setup_browser(playwright)

        self.playwright = playwright
        self.playwright_browser = browser

        return self.playwright_browser

    async def _setup_cdp(self, playwright: Playwright) -> PlaywrightBrowser:
        """Sets up and returns a Playwright Browser instance with anti-detection measures."""
        if not self.config.cdp_url:
            raise ValueError('CDP URL is required')
        logger.info(f'Connecting to remote browser via CDP {self.config.cdp_url}')
        browser = await playwright.chromium.connect_over_cdp(self.config.cdp_url)
        return browser

    async def _setup_wss(self, playwright: Playwright) -> PlaywrightBrowser:
        """Sets up and returns a Playwright Browser instance with anti-detection measures."""
        if not self.config.wss_url:
            raise ValueError('WSS URL is required')
        logger.info(f'Connecting to remote browser via WSS {self.config.wss_url}')
        browser = await playwright.chromium.connect(self.config.wss_url)
        return browser

    async def _setup_browser_with_instance(self, playwright: Playwright) -> PlaywrightBrowser:
        """Sets up and returns a Playwright Browser instance with anti-detection measures."""
        if not self.config.chrome_instance_path:
            raise ValueError('Chrome instance path is required')
        import subprocess

        try:
            # Check if browser is already running
            response = requests.get('http://localhost:9222/json/version', timeout=2)
            if response.status_code == 200:
                logger.info('Reusing existing Chrome instance')
                browser = await playwright.chromium.connect_over_cdp(
                    endpoint_url='http://localhost:9222',
                    timeout=20000,  # 20 second timeout for connection
                )
                return browser
        except requests.ConnectionError:
            logger.debug('No existing Chrome instance found, starting a new one')

        # Start a new Chrome instance
        subprocess.Popen(
            [
                self.config.chrome_instance_path,
                '--remote-debugging-port=9222',
            ]
            + self.config.extra_chromium_args +
            ([f"--user-data-dir={self.config.chrome_profile_data}"] if not self.config.has_extensions() else []),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        # Attempt to connect again after starting a new instance
        for _ in range(10):
            try:
                response = requests.get('http://localhost:9222/json/version', timeout=2)
                if response.status_code == 200:
                    break
            except requests.ConnectionError:
                pass
            await asyncio.sleep(1)

        # Attempt to connect again after starting a new instance
        try:
            browser = await playwright.chromium.connect_over_cdp(
                endpoint_url='http://localhost:9222',
                timeout=20000,  # 20 second timeout for connection
            )
            return browser
        except Exception as e:
            logger.error(f'Failed to start a new Chrome instance.: {str(e)}')
            raise RuntimeError(
                ' To start chrome in Debug mode, you need to close all existing Chrome instances and try again otherwise we can not connect to the instance.'
            )

    async def _setup_standard_browser(self, playwright: Playwright) -> PlaywrightBrowser:
        """Sets up and returns a Playwright Browser instance with anti-detection measures."""
        browser = await playwright.chromium.launch(
            headless=self.config.headless,
            args=[
                     '--no-sandbox',
                     '--disable-blink-features=AutomationControlled',
                     '--disable-infobars',
                     '--disable-background-timer-throttling',
                     '--disable-popup-blocking',
                     '--disable-backgrounding-occluded-windows',
                     '--disable-renderer-backgrounding',
                     '--disable-window-activation',
                     '--disable-focus-on-load',
                     '--no-first-run',
                     '--no-default-browser-check',
                     '--no-startup-window',
                     '--window-position=0,0',
                     # '--window-size=1280,1000',
                 ]
                 + self.disable_security_args
                 + self.config.extra_chromium_args,
            proxy=self.config.proxy,
        )
        # convert to Browser
        return browser

    async def _setup_browser(self, playwright: Playwright) -> PlaywrightBrowser:
        """Sets up and returns a Playwright Browser instance with anti-detection measures."""
        await self._add_extension_paths_as_commandline_args()
        try:
            if self.config.cdp_url:
                return await self._setup_cdp(playwright)
            if self.config.wss_url:
                return await self._setup_wss(playwright)
            elif self.config.chrome_instance_path:
                return await self._setup_browser_with_instance(playwright)
            else:
                return await self._setup_standard_browser(playwright)
        except Exception as e:
            logger.error(f'Failed to initialize Playwright browser: {str(e)}')
            raise

    async def close(self):
        """Close the browser instance"""
        try:
            if not self.config._force_keep_browser_alive:
                if self.playwright_browser:
                    await self.playwright_browser.close()
                    del self.playwright_browser
                if self.playwright:
                    await self.playwright.stop()
                    del self.playwright

        except Exception as e:
            logger.debug(f'Failed to close browser properly: {e}')
        finally:
            self.playwright_browser = None
            self.playwright = None

            gc.collect()

    def __del__(self):
        """Async cleanup when object is destroyed"""
        try:
            if self.playwright_browser or self.playwright:
                loop = asyncio.get_running_loop()
                if loop.is_running():
                    loop.create_task(self.close())
                else:
                    asyncio.run(self.close())
        except Exception as e:
            logger.debug(f'Failed to cleanup browser in destructor: {e}')
