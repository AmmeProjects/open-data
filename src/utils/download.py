import os
from urllib.request import urlretrieve


class Download:
    
    def __init__(
            self,
            url: str,
            path: str,
        ) -> None:
        self.url = url
        self.path = path

    def download(self, force=False):
        
        if force or not os.path.exists(self.path):
            urlretrieve(self.url, self.path)
        
        
        



