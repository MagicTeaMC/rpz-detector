import gzip
import time
import requests
from pathlib import Path
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import logging
from typing import List
import argparse

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("domain_downloader.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class DomainDownloader:
    def __init__(
        self,
        base_url: str = "https://ipsniper.info/domaincount.html",
        download_dir: str = "downloads",
        output_file: str = "merged_domains.txt",
        max_retries: int = 3,
        retry_delay: int = 5,
        chunk_size: int = 8192,
    ):
        """
        Initialize the domain downloader.

        Args:
            base_url: Base URL to fetch the domain list page
            download_dir: Directory to store downloaded files
            output_file: Final merged output file name
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries in seconds
            chunk_size: Download chunk size in bytes
        """
        self.base_url = base_url
        self.download_dir = Path(download_dir)
        self.output_file = output_file
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.chunk_size = chunk_size

        self.download_dir.mkdir(exist_ok=True)
        self.temp_dir = self.download_dir / "temp"
        self.temp_dir.mkdir(exist_ok=True)

        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
        )

    def get_download_urls(self, html_content: str = None) -> List[str]:

        if html_content is None:
            logger.info(f"Fetching page content from {self.base_url}")
            try:
                response = self.session.get(self.base_url)
                response.raise_for_status()
                html_content = response.text
            except requests.RequestException as e:
                logger.error(f"Failed to fetch page: {e}")
                return []

        soup = BeautifulSoup(html_content, "html.parser")
        urls = []

        for link in soup.find_all("a", href=True):
            href = link["href"]
            if href.endswith(".txt.gz"):
                full_url = urljoin("https://ipsniper.info/", href)
                urls.append(full_url)

        logger.info(f"Found {len(urls)} download URLs")
        return urls

    def download_file(self, url: str, force_redownload: bool = False) -> Path:

        filename = Path(urlparse(url).path).name
        filepath = self.download_dir / filename

        if filepath.exists() and not force_redownload:
            logger.info(f"File {filename} already exists, skipping")
            return filepath

        logger.info(f"Downloading {filename}")

        for attempt in range(self.max_retries):
            try:
                response = self.session.get(url, stream=True, timeout=30)
                response.raise_for_status()

                total_size = int(response.headers.get("content-length", 0))
                downloaded_size = 0

                with open(filepath, "wb") as f:
                    for chunk in response.iter_content(chunk_size=self.chunk_size):
                        if chunk:
                            f.write(chunk)
                            downloaded_size += len(chunk)

                            if total_size > 0:
                                progress = (downloaded_size / total_size) * 100
                                print(
                                    f"\r  Progress: {progress:.1f}%", end="", flush=True
                                )

                print()
                logger.info(f"Successfully downloaded {filename}")
                return filepath

            except requests.RequestException as e:
                logger.warning(f"Attempt {attempt + 1} failed for {filename}: {e}")
                if attempt < self.max_retries - 1:
                    logger.info(f"Retrying in {self.retry_delay} seconds...")
                    time.sleep(self.retry_delay)
                else:
                    logger.error(
                        f"Failed to download {filename} after {self.max_retries} attempts"
                    )

        return None

    def decompress_file(self, gz_filepath: Path) -> Path:

        output_path = self.temp_dir / gz_filepath.stem

        if output_path.exists():
            logger.info(f"File {output_path.name} already decompressed")
            return output_path

        logger.info(f"Decompressing {gz_filepath.name}")

        try:
            with gzip.open(gz_filepath, "rt", encoding="utf-8") as gz_file:
                with open(output_path, "w", encoding="utf-8") as output_file:
                    for line in gz_file:
                        output_file.write(line)

            logger.info(f"Successfully decompressed to {output_path.name}")
            return output_path

        except Exception as e:
            logger.error(f"Failed to decompress {gz_filepath.name}: {e}")
            return None

    def merge_files(self, txt_files: List[Path]) -> None:

        output_path = self.download_dir / self.output_file
        total_domains = 0
        unique_domains = set()

        logger.info(f"Merging {len(txt_files)} files into {self.output_file}")

        logger.info("Pass 1: Collecting unique domains...")
        for txt_file in txt_files:
            if txt_file and txt_file.exists():
                logger.info(f"Processing {txt_file.name}")
                try:
                    with open(txt_file, "r", encoding="utf-8") as f:
                        for line in f:
                            domain = line.strip()
                            if domain:
                                unique_domains.add(domain.lower())
                                total_domains += 1
                except Exception as e:
                    logger.error(f"Error reading {txt_file.name}: {e}")

        logger.info("Pass 2: Writing unique domains to output...")
        with open(output_path, "w", encoding="utf-8") as output_file:
            for domain in sorted(unique_domains):
                output_file.write(domain + "\n")

        logger.info(f"Merge complete!")
        logger.info(f"Total domains processed: {total_domains:,}")
        logger.info(f"Unique domains saved: {len(unique_domains):,}")
        logger.info(f"Output file: {output_path}")

    def cleanup(self, keep_compressed: bool = True, keep_temp: bool = False):

        logger.info("Starting cleanup...")

        if not keep_temp and self.temp_dir.exists():
            logger.info("Removing temporary decompressed files...")
            for file in self.temp_dir.glob("*"):
                try:
                    file.unlink()
                    logger.debug(f"Removed {file.name}")
                except Exception as e:
                    logger.warning(f"Failed to remove {file.name}: {e}")

            try:
                self.temp_dir.rmdir()
                logger.info("Removed temp directory")
            except Exception as e:
                logger.warning(f"Failed to remove temp directory: {e}")

        if not keep_compressed:
            logger.info("Removing compressed files...")
            for file in self.download_dir.glob("*.gz"):
                try:
                    file.unlink()
                    logger.debug(f"Removed {file.name}")
                except Exception as e:
                    logger.warning(f"Failed to remove {file.name}: {e}")

        logger.info("Cleanup complete")

    def run(self, html_content: str = None, force_redownload: bool = False):
        """
        Main execution method.

        Args:
            html_content: HTML content to parse (if None, fetches from URL)
            force_redownload: Force redownload of existing files
        """
        logger.info("Starting domain list download and merge process")

        urls = self.get_download_urls(html_content)
        if not urls:
            logger.error("No download URLs found")
            return

        logger.info(f"Starting download of {len(urls)} files...")
        downloaded_files = []
        failed_downloads = []

        for i, url in enumerate(urls, 1):
            logger.info(f"Downloading file {i}/{len(urls)}")
            filepath = self.download_file(url, force_redownload)
            if filepath:
                downloaded_files.append(filepath)
            else:
                failed_downloads.append(url)

        logger.info(
            f"Downloads complete: {len(downloaded_files)} successful, {len(failed_downloads)} failed"
        )

        if failed_downloads:
            logger.warning("Failed downloads:")
            for url in failed_downloads:
                logger.warning(f"  - {url}")

        logger.info("Starting decompression...")
        txt_files = []
        for gz_file in downloaded_files:
            txt_file = self.decompress_file(gz_file)
            if txt_file:
                txt_files.append(txt_file)

        if txt_files:
            self.merge_files(txt_files)
        else:
            logger.error("No files to merge")
            return

        self.cleanup()

        logger.info("Process completed successfully!")


def main():
    parser = argparse.ArgumentParser(description="Download and merge domain lists")
    parser.add_argument(
        "--url",
        default="https://ipsniper.info/domaincount.html",
        help="Base URL to fetch domain lists from",
    )
    parser.add_argument(
        "--output",
        default="merged_domains.txt",
        help="Output filename for merged domains",
    )
    parser.add_argument(
        "--download-dir",
        default="downloads",
        help="Directory to store downloaded files",
    )
    parser.add_argument(
        "--force-redownload",
        action="store_true",
        help="Force redownload of existing files",
    )
    parser.add_argument(
        "--max-retries", type=int, default=3, help="Maximum number of retry attempts"
    )
    parser.add_argument(
        "--retry-delay", type=int, default=5, help="Delay between retries in seconds"
    )
    parser.add_argument(
        "--html-file", help="Use local HTML file instead of fetching from URL"
    )

    args = parser.parse_args()

    html_content = None
    if args.html_file:
        try:
            with open(args.html_file, "r", encoding="utf-8") as f:
                html_content = f.read()
            logger.info(f"Using HTML content from {args.html_file}")
        except Exception as e:
            logger.error(f"Failed to read HTML file: {e}")
            return

    downloader = DomainDownloader(
        base_url=args.url,
        download_dir=args.download_dir,
        output_file=args.output,
        max_retries=args.max_retries,
        retry_delay=args.retry_delay,
    )

    try:
        downloader.run(html_content, args.force_redownload)
    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")


if __name__ == "__main__":
    main()
