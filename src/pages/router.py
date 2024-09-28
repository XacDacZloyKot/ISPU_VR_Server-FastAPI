import os
from http import HTTPStatus

from fastapi import APIRouter
from fastapi import Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.base_config import current_user, staff_user, administrator_user
from src.auth.models import User, Scenario
from src.database import get_async_session
from src.pages.crud import (
    get_scenario_for_id,
    get_admission_for_id, get_model_for_id, delete_all_connection_scenario_accident, add_accidents_for_scenario,
    create_model_values_or_update,
)
from src.pages.utils import (user_menu,
                             create_json_scenario, start_app,
                             )

router = APIRouter(
    prefix='/pages',
    tags=['Pages']
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates\\")

templates = Jinja2Templates(directory=TEMPLATES_DIR)


# region StartApp
@router.get("/scenario/start/{admission_id}", response_class=HTMLResponse)
async def start_admission_app(
        request: Request,
        admission_id: int,
        user: User = Depends(current_user),
        session: AsyncSession = Depends(get_async_session)
):
    try:
        admission = await get_admission_for_id(admission_id=admission_id, session=session)
        create_json_scenario(admission_json=admission.json_id())
        start_app()
        return RedirectResponse(url=request.url_for('get_tasks'),
                                status_code=HTTPStatus.SEE_OTHER)
    except SQLAlchemyError as e:
        print(f"SQLAlchemy error occurred: {e}")
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "There is some problem with start app.",
            'user': user,
            'menu': user_menu
        })
    except IOError as e:
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": str(e),
            'user': user,
            'menu': user_menu
        })
    except Exception as e:
        print(e)
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "There is some problem with start app.",
            'user': user,
            'menu': user_menu
        })
# endregion

