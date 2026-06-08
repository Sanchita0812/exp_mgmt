import ssl
import certifi
from django.core.mail.backends.smtp import EmailBackend as DjangoEmailBackend


class EmailBackend(DjangoEmailBackend):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Use certifi's CA bundle for TLS certificate verification
        self.ssl_context = ssl.create_default_context(cafile=certifi.where())
