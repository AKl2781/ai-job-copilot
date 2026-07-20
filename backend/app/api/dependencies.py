"""Dependencies shared by versioned API routers."""

from fastapi import Depends, Header
from sqlalchemy.orm import Session

from ..application.analysis_service import ApplicationAnalysisService
from ..application.crud_service import DEFAULT_USER_EMAIL, CrudService
from ..infrastructure.database.session import get_db_session


def get_crud_service(
    session: Session = Depends(get_db_session),
    x_user_email: str = Header(
        default=DEFAULT_USER_EMAIL,
        alias="X-User-Email",
        min_length=3,
        max_length=320,
        pattern=r"^[^\s@]+@[^\s@]+$",
    ),
) -> CrudService:
    """Build a request-scoped service for the selected local user."""
    return CrudService(session, x_user_email)


def get_application_analysis_service(
    session: Session = Depends(get_db_session),
    x_user_email: str = Header(
        default=DEFAULT_USER_EMAIL,
        alias="X-User-Email",
        min_length=3,
        max_length=320,
        pattern=r"^[^\s@]+@[^\s@]+$",
    ),
) -> ApplicationAnalysisService:
    """Build the saved-job analysis workflow for the selected local user."""
    return ApplicationAnalysisService(session, x_user_email)
