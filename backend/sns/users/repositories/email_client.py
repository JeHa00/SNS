import smtplib

from jinja2 import Environment, FileSystemLoader
from email.message import EmailMessage

from sns.common.path import EMAIL_TEMPLATE_DIR
from sns.common.config import settings


class EmailClient:
    def __init__(self):
        self._template_name = None  # 이메일 발송에 사용될 이메일 템플릿 이름
        self._password = None  # 임시 비밀번호
        self._url = None  # 이메일 인증 코드 url

    def make_massage(self, email_to: str, template_name: str, **kwargs) -> dict:
        """발송될 이메일 메세지와 이메일 템플릿 종류에 따른 렌더링 데이터를 생성한다.

        Args:
            email_to (str): 수신자
            template_name (str): 템플릿 이름

        Raises:
            ValueError: 임시 비밀번호 또는 이메일 인증 url 값이 생성되지 않아 존재하지 않을 경우 발생

        Returns:
            dict: 발송될 이메일 메세지와 템플릿 렌더링에 사용될 데이터
        """
        self._template_name = template_name

        message = EmailMessage()
        message.add_header("From", settings.EMAIL_ADDRESS)
        message.add_header("To", email_to)
        context = {
            "project_name": settings.PROJECT_NAME,
            "email": email_to,
        }

        if "url" in kwargs:
            self._url = kwargs.get("url")
            message.add_header(
                "Subject", f"{settings.PROJECT_NAME} - New account for user"
            )
            context.update({"link": self._url})
        else:
            self._password = kwargs.get("password")
            message.add_header(
                "Subject", f"{settings.PROJECT_NAME} - Reset password for user"
            )
            context.update({"password": self._password})

        if not (self.get_temporary_password or self.get_verification_url):
            raise ValueError("임시 비밀번호 또는 이메일 인증 url 값이 존재하지 않습니다.")

        data = {"message": message, "context": context}
        return data

    def send_email(self, message: EmailMessage, context: dict) -> None:
        """email message를 받아 해당 정보로 발송한다.

        Args:
            message (EmailMessage): email이 발신자, 수신자, 제목 정보
            context (dict): template_name을 가진 email template을 렌더링하기 위해 전달되는 값
        """
        env = Environment(loader=FileSystemLoader(EMAIL_TEMPLATE_DIR))
        template = env.get_template(f"{self._template_name}.html")
        message.set_content(template.render(**context), subtype="html")
        with smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT) as smtp:
            smtp.starttls()
            smtp.login(settings.EMAIL_ADDRESS, settings.EMAIL_PASSWORD)
            smtp.send_message(message)

    def send_new_account_email(self, email_to: str, url: str) -> None:
        """새로운 계정 생성 이메일 메세지를 생성하여 send_email에 전달한다.

        Args:
            email_to (str): 새로 등록한 유저의 이메일
            url (str): 발송된 이메일에 첨부된 이메일 인증 url
        """
        data = self.make_massage(email_to, "new_account", url=url)
        self.send_email(**data)

    def send_reset_password_email(self, email_to: str, password: str) -> None:
        """비밀번호 초기화 이메일 메세지를 생성하여 send_email에 전달한다.

        Args:
            email_to (str): 수신자
            password (str): 임시 비밀번호
        """
        data = self.make_massage(email_to, "reset_password", password=password)
        self.send_email(**data)

    def get_verification_url(self) -> str:
        """이메일 인증 url를 얻는다.

        Returns:
            str: 이메일 인증 url
        """
        return self._url

    def get_temporary_password(self) -> str:
        """임시 비밀번호를 얻는다.

        Returns:
            str: 임시 비밀번호
        """
        return self._password


email_client = EmailClient()
