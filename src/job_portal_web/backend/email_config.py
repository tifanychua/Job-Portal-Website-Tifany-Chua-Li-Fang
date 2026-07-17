from fastapi_mail import ConnectionConfig
from pydantic import SecretStr

conf = ConnectionConfig(
    MAIL_USERNAME="tifanyclf-pm23@student.tarc.edu.my",
    MAIL_PASSWORD=SecretStr("vxvk rfhr daij ybqz"),
    MAIL_FROM="tifanyclf-pm23@student.tarc.edu.my",
    MAIL_PORT=587,
    MAIL_SERVER="smtp.gmail.com",
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
)
