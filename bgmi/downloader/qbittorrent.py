from typing import TYPE_CHECKING

from bgmi.config import (
    QBITTORRENT_CATEGORY,
    QBITTORRENT_HOST,
    QBITTORRENT_PASSWORD,
    QBITTORRENT_PORT,
    QBITTORRENT_USERNAME,
)
from bgmi.plugin.status import DownloadStatus
from bgmi.utils import print_info, print_warning
from bgmi.plugin.base import BaseDownloadService, MissingDependencyError
from bgmi.website.model import Episode

if TYPE_CHECKING:
    from qbittorrentapi import TorrentStates


class QBittorrentWebAPI(BaseDownloadService):
    def __init__(self):
        super().__init__()
        import qbittorrentapi

        self.client = qbittorrentapi.Client(
            host=QBITTORRENT_HOST,
            port=QBITTORRENT_PORT,
            username=QBITTORRENT_USERNAME,
            password=QBITTORRENT_PASSWORD,
        )
        self.client.auth_log_in()

    def add_download(self, episode: Episode, save_path: str, overwrite: bool = False):
        self.client.torrents_add(
            urls=episode.download,
            category=QBITTORRENT_CATEGORY,
            save_path=save_path,
            is_paused=False,
            use_auto_torrent_management=False,
        )
        print_info(
            "Add torrent into the download queue, the file will be saved at {}".format(
                save_path
            )
        )

    @staticmethod
    def check_dep():
        try:
            __import__("qbittorrentapi")
        except ImportError:
            raise MissingDependencyError("Please run `pip install qbittorrent-api`")

    def get_status(self, id: str) -> DownloadStatus:
        import qbittorrentapi

        # torrent in self.client.torrents_info(category=QBITTORRENT_CATEGORY)
        torrent = self.client.torrents.info()
        state_enum: "TorrentStates" = torrent.state_enum
        if state_enum.is_complete or state_enum.is_uploading:
            return DownloadStatus.done
        elif state_enum.is_errored:
            return DownloadStatus.error
        elif state_enum.is_downloading:
            return DownloadStatus.downloading
        elif state_enum == qbittorrentapi.TorrentStates.PAUSED_DOWNLOAD:
            return DownloadStatus.not_downloading
