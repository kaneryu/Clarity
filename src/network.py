import requests
import logging
from typing import Dict, Any, Optional, Union, Tuple
import time
import urllib3
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from concurrent.futures import ThreadPoolExecutor
import enum
import os

from src import paths
from src.misc import settings
from src.misc.enumerations.Network import OnlineStatus
from src.workers import bgworker

from PySide6.QtCore import QObject, Signal, Slot, Property


 
class NetworkManager(QObject):
    """Centralized network request manager for Clarity"""
    onlineStatusChanged =  Signal(int)
    
    _instance: "NetworkManager" = None  # type: ignore
    
    @classmethod
    def get_instance(cls) -> 'NetworkManager':
        """Get or create the NetworkManager singleton instance"""
        if cls._instance is None:
            cls._instance = NetworkManager()
        return cls._instance
    
    def __init__(self):
        """Initialize the NetworkManager"""
        if NetworkManager._instance is not None:
            raise RuntimeError("Use NetworkManager.get_instance() instead of constructor")
            
        super().__init__()
        self.logger = logging.getLogger("NetworkManager")
        self.session = requests.Session()
        self.timeout = 30  # Default timeout in seconds
        self.proxy_config: Union[dict, None] = None
        self.default_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9"
            # "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
        }
        
        # Configure session with retry logic
        retry_strategy = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST", "PUT", "DELETE", "HEAD", "OPTIONS"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        self.session.headers.update(self.default_headers)
        
        NetworkManager._instance = self
        self._onlineStatus = self.test_onlinemode()
        self.onlineStatus: OnlineStatus
        bgworker.add_occasional_task(self.occasionally_test_onlinemode, dynamic_interval_max=60)  # Max interval of 5 minutes
    
    def occasionally_test_onlinemode(self) -> bool:
        self.test_onlinemode()
        return True # We always want to increase the timer, so treat every run as a success
        # to not reset the dynamic interval timer to 0
    
    def set_proxy(self, proxy_url: Optional[str] = None):
        """
        Set proxy for all requests
        Example: http://username:password@proxyserver:port
        """
        
        if proxy_url:
            self.proxy_config = {
                "http": proxy_url,
                "https": proxy_url
            }
            self.session.proxies = self.proxy_config
            self.logger.info(f"Proxy configured: {proxy_url.split('@')[-1]}")
        else:
            self.proxy_config = None
            self.session.proxies = {}
            self.logger.info("Proxy disabled")
    
    def set_timeout(self, timeout: int):
        """Set default timeout for requests in seconds"""
        self.timeout = timeout
    
    def set_headers(self, headers: Dict[str, str]):
        """Set default headers for all requests"""
        self.default_headers.update(headers)
        self.session.headers.update(self.default_headers)
    
    def get(self, url: str, params: Optional[Dict] = None, 
            headers: Optional[Dict] = None, timeout: Optional[int] = None, 
            stream: bool = False, allow_redirects: bool = True) -> Union[requests.Response, None]:
        """
        Perform a GET request
        
        Args:
            url: URL to request
            params: URL parameters
            headers: Additional headers
            timeout: Request timeout (overrides default)
            stream: Whether to stream the response
            allow_redirects: Whether to follow redirects
        
        Returns:
            Response object
        """
        request_timeout = timeout if timeout is not None else self.timeout
        request_headers = {**self.default_headers, **(headers or {})}
        
        try:
            self.logger.debug(f"GET {url}")
            response = self.session.get(
                url, 
                params=params,
                headers=request_headers,
                timeout=request_timeout,
                stream=stream,
                allow_redirects=allow_redirects
            )
            response.raise_for_status()
            return response
        except Exception as e:
            self.logger.error(f"GET request failed: {url} - {str(e)}")
            return None
            
    
    def post(self, url: str, data: Optional[Dict] = None, 
             json: Optional[Dict] = None, headers: Optional[Dict] = None, 
             timeout: Optional[int] = None) -> requests.Response:
        """
        Perform a POST request
        
        Args:
            url: URL to request
            data: Form data
            json: JSON data
            headers: Additional headers
            timeout: Request timeout (overrides default)
        
        Returns:
            Response object
        """
        request_timeout = timeout if timeout is not None else self.timeout
        request_headers = {**self.default_headers, **(headers or {})}
        
        try:
            self.logger.debug(f"POST {url}")
            response = self.session.post(
                url,
                data=data,
                json=json,
                headers=request_headers,
                timeout=request_timeout
            )
            response.raise_for_status()
            return response
        except Exception as e:
            self.logger.error(f"POST request failed: {url} - {str(e)}")

    
    def download_file(self, url: str, file_obj, 
                     headers: Optional[Dict] = None, 
                     progress_callback=None,
                     start: int = -1) -> bool:
        """
        Download a file with optional progress tracking
        
        Args:
            url: URL of the file
            destination_path: Where to save the file
            headers: Additional headers
            progress_callback: Function to call with (current_size, total_size)
        
        Returns:
            True if successful, False if failed
        """
        request_headers = {**self.default_headers, **(headers or {})}
        if start >= 0:
            request_headers["Range"] = f"bytes={start}-"
        try:
            with self.session.get(url, headers=request_headers, stream=True) as response:
                response.raise_for_status()
                if response.status_code == 416:  # Requested range not satisfiable
                    self.logger.warning(f"Range not satisfiable for {url}, starting from beginning")
                    start = 0
                    request_headers["Range"] = "bytes=0-"
                    response = self.session.get(url, headers=request_headers, stream=True)
                if response.status_code == 200 and start >= 0:
                    file_obj.seek(0)  # Ensure we start writing at the beginning
                    
                file_obj.seek(start)  # Ensure we start writing at the correct position
                    
                total_size = int(response.headers.get('content-length', 0))
                
                
                downloaded = 0
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:  # filter out keep-alive chunks
                        file_obj.write(chunk)
                        downloaded += len(chunk)
                        if progress_callback:
                            progress_callback(downloaded, total_size)
                
                self.logger.debug(f"Downloaded {url} to {file_obj.name} ({downloaded}/{total_size} bytes)")
                return True
                
        except Exception as e:
            self.logger.error(f"Download failed: {url} - {str(e)}")
            return False
    
    def download_chunk(self, url: str, file_obj, start: int, end: int, 
                      headers: Optional[Dict] = None,
                      progress_callback=None) -> int:
        """
        Download a specific byte range from a URL to a file object
        
        Args:
            url: URL to download from
            file_obj: File object to write to (must be opened in 'wb' mode)
            start: Start byte
            end: End byte
            headers: Additional headers
            progress_callback: Function to call with progress updates
            
        Returns:
            Number of bytes downloaded
        """
        request_headers = {**self.default_headers, **(headers or {})}
        request_headers["Range"] = f"bytes={start}-{end}"
        
        bytes_downloaded = 0
        
        try:
            with self.session.get(url, headers=request_headers, stream=True) as response:
                response.raise_for_status()
                
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:  # filter out keep-alive chunks
                        file_obj.seek(start + bytes_downloaded)
                        file_obj.write(chunk)
                        bytes_downloaded += len(chunk)
                        if progress_callback:
                            progress_callback(start + bytes_downloaded)
                            
            self.logger.debug(f"Downloaded chunk {start}-{end} from {url}")
            return bytes_downloaded
            
        except Exception as e:
            self.logger.error(f"Chunk download failed: {url} [{start}-{end}] - {str(e)}")
            raise
        
    async def download_file_parallel(self, url: str, file_obj, 
                                    chunk_size: int = 10*1024*1024,  # 10MB default
                                    max_workers: int = 4,
                                    headers: Optional[Dict] = None,
                                    progress_callback=None) -> bool:
        """
        Download a file in parallel chunks
        
        Args:
            url: URL to download
            file_obj: File object to write to (must support seek/write)
            chunk_size: Size of each chunk in bytes
            max_workers: Maximum number of parallel downloads
            headers: Additional headers
            progress_callback: Function to call with (current_bytes, total_bytes)
            
        Returns:
            True if successful
        """
        request_headers = {**self.default_headers, **(headers or {})}
        downloaded_size = file_obj.tell()  # Get current position for resuming
        
        # Get file size with HEAD request
        try:
            head_response = self.session.head(url, headers=request_headers, timeout=self.timeout)
            head_response.raise_for_status()
            total_size = int(head_response.headers.get("Content-Length", 0)) + downloaded_size
            
            if total_size == 0:
                self.logger.warning(f"Could not determine file size for {url}")
                return False
                
            # Generate chunk ranges
            ranges = [(i, min(i + chunk_size - 1, total_size - 1)) 
                     for i in range(downloaded_size, total_size, chunk_size)]
            
            progress = {i: 0 for i in range(len(ranges))}
            total_progress = downloaded_size
            
            def update_progress(chunk_index, bytes_position):
                nonlocal total_progress
                progress[chunk_index] = bytes_position
                current_total = sum(progress.values())
                if progress_callback:
                    progress_callback(current_total, total_size)
            
            # Download chunks in parallel
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = []
                for i, (start, end) in enumerate(ranges):
                    futures.append(
                        executor.submit(
                            self.download_chunk, 
                            url,
                            file_obj,
                            start, 
                            end,
                            request_headers,
                            lambda pos, idx=i: update_progress(idx, pos)
                        )
                    )
                
                # Wait for all futures to complete
                for future in futures:
                    future.result()  # Will raise exceptions if any occurred
                    
            self.logger.info(f"Parallel download complete for {url}")
            return True
            
        except Exception as e:
            self.logger.error(f"Parallel download failed: {url} - {str(e)}")
            return False
    
    def clear_cookies(self):
        """Clear session cookies"""
        self.session.cookies.clear()
        self.logger.debug("Cookies cleared")
    
    def close(self):
        """Close the current session"""
        if self.session:
            self.session.close()
            self.logger.debug("Session closed")

    def test_onlinemode(self) -> OnlineStatus:
        connected = True if self.get("https://www.google.com", timeout = 1) else False
        youtube = True if self.get("https://music.youtube.com", timeout = 1) else False
        
        if (connected and youtube):
            r = OnlineStatus.ONLINE
        elif (connected and not youtube):
            r = OnlineStatus.ONLINE_NO_YOUTUBE
        else:
            r = OnlineStatus.OFFLINE
        
        if not OnlineStatus.ONLINE:
            self.logger.error(f"You are Offline (offlineMode {r.name})")
        self._onlineStatus = r
        return r
    
    @Property(int)
    def onlineStatus(self) -> OnlineStatus:
        return self._onlineStatus
    
    @onlineStatus.setter
    def onlineStatus(self, value: OnlineStatus) -> None:
        self._onlineStatus = value
        self.onlineStatusChanged.emit(self._onlineStatus)
    
# Create a global network manager instance for easier imports
networkManager = NetworkManager.get_instance()
connected = False