from http import HTTPStatus

from fastapi import APIRouter, Form, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from typing_extensions import Optional

from src.auth.base_config import staff_user
from src.auth.models import Admission, AdmissionStatus
from src.auth.models import User
from src.database import get_async_session
from src.pages.router import templates
from src.pages.utils import user_menu
from src.scenario.crud import get_scenario_for_id as get_scenario_for_id_func, get_active_scenarios
from src.users.crud import get_users_without_scenario
from src.admission.crud import get_admission_for_id as get_admission_for_id_func

router = APIRouter(
    prefix='/pages/admission',
    tags=['Admission']
)


@router.get("/scenario/add/{scenario_id}", response_class=HTMLResponse)
async def get_task_assignment(request: Request, scenario_id: int, current_user: User = Depends(staff_user),
                              session: AsyncSession = Depends(get_async_session)):
    try:
        scenario = await get_scenario_for_id_func(scenario_id=scenario_id, session=session)
        users = await get_users_without_scenario(scenario_id=scenario_id, session=session)
        return templates.TemplateResponse(
            "/staff/assignment_task/add_task_user.html",
            {
                'request': request,
                'user': current_user,
                'users': users,
                'scenario': scenario,
                'title': "ISPU - Добавление задачи!",
                'menu': user_menu,
            }
        )
    except SQLAlchemyError as e:
        print(f"SQLAlchemy ошибка при открытии страницы с задачами: {e}")
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            'error': "Возникла ошибка с БД при переходе на страницу с задачами.",
            'user': current_user,
            'menu': user_menu
        })
    except Exception as e:
        print(f"Ошибка при открытии страницы с задачами: {e}")
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            'error': "Возникла ошибка при переходе на страницу с задачами.",
            'user': current_user,
            'menu': user_menu
        })


@router.post("/scenario/add/{scenario_id}", response_class=HTMLResponse)
async def post_task_assignment(request: Request, scenario_id: int, user_ids: list[int] = Form(None),
                               user: User = Depends(staff_user),
                               session: AsyncSession = Depends(get_async_session)):
    try:
        response = RedirectResponse(url=request.url_for("get_scenario"),
                                    status_code=HTTPStatus.MOVED_PERMANENTLY)
        if not user_ids:
            return response
        for user_id in user_ids:
            admission = Admission(status=AdmissionStatus.ACTIVE, user_id=user_id, rating="0", scenario_id=scenario_id)
            session.add(admission)
        await session.commit()
        return response
    except SQLAlchemyError as e:
        print(f"SQLAlchemy ошибка при создании задачи для пользователя: {e}")
        await session.rollback()
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            'error': "Возникла ошибка при создании задачи.",
            'user': user,
            'menu': user_menu
        })
    except Exception as e:
        print(f"Ошибка при создании задачи для пользователя: {e}")
        await session.rollback()
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            'error': "Возникла ошибка при создании задачи.",
            'user': user,
            'menu': user_menu
        })


@router.get("/update/{admission_id}", response_class=HTMLResponse)
async def get_update_admission(
        request: Request,
        admission_id: int,
        error: Optional[str] = None,
        user: User = Depends(staff_user),
        session: AsyncSession = Depends(get_async_session)
):
    try:
        admission = await get_admission_for_id_func(admission_id=admission_id, session=session)
        return templates.TemplateResponse(
            "/staff/update/admission/update_admission_for_user.html",
            {
                'request': request,
                'user': user,
                'admission': admission,
                'status_options': AdmissionStatus,
                'menu': user_menu,
                'title': "ISPU - Обновление задачи",
                'error': error
            }
        )
    except SQLAlchemyError as e:
        print(f"SQLAlchemy ошибка при обновлении задачи для пользователя: {e}")
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "Возникла ошибка с БД при выводе задачи пользователя.",
            'user': user,
            'menu': user_menu
        })
    except Exception as e:
        print(f"Ошибка при обновлении задачи для пользователя: {e}")
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "Возникла ошибка с при выводе задачи пользователя.",
            'user': user,
            'menu': user_menu
        })


@router.post("/update/{admission_id}/", response_class=HTMLResponse)
async def put_admission(
        request: Request,
        admission_id: int,
        rating: str = Form(...),
        status: AdmissionStatus = Form(...),
        user: User = Depends(staff_user),
        session: AsyncSession = Depends(get_async_session)
):
    try:
        admission: Admission = await get_admission_for_id_func(admission_id=admission_id, session=session)
        Admission.set_rating(admission, rating)
        admission.status = status
        session.add(admission)
        await session.commit()

        return RedirectResponse(url=request.url_for("get_users_page"), status_code=HTTPStatus.MOVED_PERMANENTLY)
    except SQLAlchemyError as e:
        print(f"SQLAlchemy ошибка при обновлении задачи для пользователя: {e}")
        await session.rollback()
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "Возникла ошибка с обновлении задачи пользователя.",
            'user': user,
            'menu': user_menu
        })
    except ValidationError as e:
        print(f"ValidationError ошибка при обновлении задачи для пользователя: {e}")
        return templates.TemplateResponse("/staff/update/admission/update_admission_for_user.html", {
            "request": request,
            "error": "Возникла ошибка с обновлении задачи пользователя.",
            'user': user,
            'menu': user_menu
        })
    except Exception as e:
        print(f"Ошибка при обновлении задачи для пользователя: {e}")
        await session.rollback()
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "Возникла ошибка с обновлении задачи пользователя.",
            'user': user,
            'menu': user_menu
        })


@router.delete("/delete/{admission_id}", name="delete_admission")
async def delete_admission(admission_id: int, session: AsyncSession = Depends(get_async_session),
                           user: User = Depends(staff_user)):
    try:
        result = await session.execute(select(Admission).filter_by(id=admission_id))
        admission = result.scalars().first()

        if admission is None:
            raise HTTPException(status_code=404, detail="Admission not found")

        await session.delete(admission)
        await session.commit()

        return {"detail": "Admission deleted successfully"}

    except SQLAlchemyError as e:
        print(f"SQLAlchemy возникла ошибка при удалении задачи: {e}")
        await session.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")
    except Exception as e:
        print(f"Возникла ошибка при удалении задачи {e}")
        await session.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")



@router.get("/add_user/{user_id}", response_class=HTMLResponse)
async def get_task_assignment_for_user(request: Request, user_id: int, user: User = Depends(staff_user),
                                            session: AsyncSession = Depends(get_async_session)):
    try:
        scenarios = await get_active_scenarios(session=session)
        return templates.TemplateResponse(
            "/staff/assignment_task/task_for_curr_user.html",
            {
                'request': request,
                'user_id': user_id,
                'user': user,
                'scenarios': scenarios,
                'title': "ISPU - Добавление задачи для пользователя!",
                'menu': user_menu,
            }
        )
    except SQLAlchemyError as e:
        print(f"SQLAlchemy ошибка в странице добавления задачи: {e}")
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "Ошибка при добавлении задачи пользователю.",
            'user': user,
            'menu': user_menu
        })
    except Exception as e:
        print(f"Ошибка в странице добавления задачи: {e}")
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "Ошибка при добавлении задачи пользователю.",
            'user': user,
            'menu': user_menu
        })


@router.post("/add_user/{user_id}", response_class=HTMLResponse)
async def post_task_assignment_for_user(request: Request, user_id: int, tasks_ids: list[int] = Form(...),
                                        current_user: User = Depends(staff_user),
                                        session: AsyncSession = Depends(get_async_session)):
    try:
        for task_id in tasks_ids:
            admission = Admission(status=AdmissionStatus.ACTIVE, user_id=user_id, rating="0", scenario_id=task_id)
            session.add(admission)
        await session.commit()
        response = RedirectResponse(url=request.url_for("get_profile_for_id", user_id=user_id),
                                    status_code=HTTPStatus.MOVED_PERMANENTLY)
        return response
    except SQLAlchemyError as e:
        print(f"SQLAlchemy ошибка при добавлении задачи пользователю: {e}")
        await session.rollback()
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "Ошибка при добавлении задачи пользователю.",
            'user': current_user,
            'menu': user_menu
        })
    except Exception as e:
        print(f"Ошибка при добавлении задачи пользователю: {e}")
        await session.rollback()
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "Ошибка при добавлении задачи пользователю.",
            'user': current_user,
            'menu': user_menu
        })