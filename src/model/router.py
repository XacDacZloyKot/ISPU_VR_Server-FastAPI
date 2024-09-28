from http import HTTPStatus

from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.base_config import staff_user, administrator_user
from src.auth.models import User
from src.database import get_async_session
from src.pages.router import templates
from src.pages.utils import (user_menu,
                             )
from src.model.crud import get_model_for_id as get_model_for_id_func, get_models, update_model, get_model_values_for_id, \
    create_model_values_or_update
from src.model.crud import (get_model_values_group_by_type, get_model_value_for_name,
                            get_model_values_for_id as get_model_values_for_id_func,
                            create_model as create_model_func, create_or_get_model_type,
                            delete_accident_for_model as delete_accident_for_model_func)
from src.sensor import Accident, model_accident_association

router = APIRouter(
    prefix='/pages/models31321',
    tags=['Model']
)


@router.get("/model/{model_id}", response_class=HTMLResponse)
async def get_model_for_id(request: Request, model_id: int, user: User = Depends(staff_user),
                           session: AsyncSession = Depends(get_async_session)):
    try:
        model = await get_model_for_id_func(model_id=model_id, session=session)
        return templates.TemplateResponse(
            "/staff/get/model/model_info.html",
            {
                'request': request,
                'user': user,
                "model": model,
                'title': f"ISPU - Модель #{model_id}!",
                'menu': user_menu,
            }
        )
    except SQLAlchemyError as e:
        print(f"SQLAlchemy ошибка при выводе модели по id: {e}")
        return templates.TemplateResponse("profile/index.html", {
            'error': "Возникла ошибка с БД при переходе на страницу с моделью.",
            'user': user,
            'menu': user_menu,
            'request': request,
        })
    except Exception as e:
        print(f"Ошибка при выводе локации по id: {e}")
        return templates.TemplateResponse("profile/index.html", {
            'error': "Возникла ошибка при переходе на страницу с моделью.",
            'user': user,
            'menu': user_menu,
            'request': request,
        })


@router.get("/create/type/", response_class=HTMLResponse)
async def get_create_model(request: Request, user: User = Depends(administrator_user),
                           session: AsyncSession = Depends(get_async_session)):
    try:
        model_type = await get_model_values_group_by_type(session=session)
        return templates.TemplateResponse(
            "/staff/create/model/choice_sensor_type.html",
            {
                'request': request,
                'user': user,
                'menu': user_menu,
                'title': "ISPU - Создание модели!",
                'model_value': model_type,
            }
        )
    except SQLAlchemyError as e:
        print(f"SQLAlchemy ошибка на странице создания модели: {e}")
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "Ошибка при создании модели.",
            'user': user,
            'menu': user_menu
        })
    except Exception as e:
        print(f"Ошибка на странице создания модели: {e}")
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "Ошибка при создании модели.",
            'user': user,
            'menu': user_menu
        })


@router.post("/create/fields/", response_class=HTMLResponse)
async def get_choice_fields_for_model(request: Request, selected_model: str = Form(None),
                                      user: User = Depends(administrator_user),
                                      session: AsyncSession = Depends(get_async_session)):
    try:
        if not selected_model:
            return templates.TemplateResponse("profile/index.html", {
                "request": request,
                "error": "Вы не выбрали тип прибора КИП.",
                'user': user,
                'menu': user_menu
            })
        values = await get_model_value_for_name(session=session, sensor_name=selected_model)
        return templates.TemplateResponse(
            "/staff/create/model/choice_fields.html",
            {
                'request': request,
                'user': user,
                'menu': user_menu,
                'title': "ISPU - Создание модели!",
                'fields_options': values,
                'model_selected': selected_model,
            }
        )
    except SQLAlchemyError as e:
        print(f"SQLAlchemy ошибка на странице выбора полей для модели: {e}")
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "Возникла ошибка при выборе типа модели или полей модели.",
            'user': user,
            'menu': user_menu
        })
    except Exception as e:
        print(f"Ошибка на странице выбора полей для модели: {e}")
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "Возникла ошибка при выборе типа модели или полей модели.",
            'user': user,
            'menu': user_menu
        })


@router.post("/create/{models_name}", response_class=HTMLResponse)
async def post_create_model(
        request: Request,
        models_name: str,
        fields_selected: list[int] = Form(None),
        user: User = Depends(administrator_user),
        session: AsyncSession = Depends(get_async_session)
):
    try:
        if not fields_selected:
            return templates.TemplateResponse("profile/index.html", {
                "request": request,
                "error": "Вы не выбрали параметры модели!",
                'user': user,
                'menu': user_menu
            })
        model = await create_model_func(session=session, fields_id=fields_selected, model_name=models_name)
        if not model:
            raise SQLAlchemyError("Не удалось создать модель.")
        return RedirectResponse(url=request.url_for("get_create_accident", model_id=model.id),
                                status_code=HTTPStatus.MOVED_PERMANENTLY)
    except SQLAlchemyError as e:
        print(f"SQLAlchemy ошибка при создании модели: {e}")
        await session.rollback()
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "Ошибка с БД при создании модели.",
            'user': user,
            'menu': user_menu
        })
    except Exception as e:
        print(f"Ошибка при создании модели: {e}")
        await session.rollback()
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "Ошибка при создании модели.",
            'user': user,
            'menu': user_menu
        })


@router.get("/accident/create/{model_id}", response_class=HTMLResponse)
async def get_create_accident(
        request: Request,
        model_id: int,
        user: User = Depends(staff_user),
        session: AsyncSession = Depends(get_async_session)
):
    try:
        model = await get_model_for_id_func(session=session, model_id=model_id)
        return templates.TemplateResponse(
            "/staff/create/model/add_accident.html",
            {
                'request': request,
                'user': user,
                'menu': user_menu,
                'title': "ISPU - Добавление аварии к модели!",
                'model': model,
            }
        )
    except SQLAlchemyError as e:
        print(f"SQLAlchemy ошибка на странице добавления аварии: {e}")
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "Возникла ошибка при выводе страницы с авариями",
            'user': user,
            'menu': user_menu
        })
    except Exception as e:
        print(f"Ошибка на странице добавления аварии: {e}")
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "Возникла ошибка при выводе страницы с авариями",
            'user': user,
            'menu': user_menu
        })


@router.post("/accident/create/{model_id}", response_class=HTMLResponse)
async def post_add_accident(
        request: Request,
        model_id: int,
        name: str = Form(...),
        mechanical_accident: bool = Form(default=False),
        keys: list[str] = Form(None),
        values: list[str] = Form(None),
        slug_name: list[str] = Form(None),
        measurement: list[str] = Form(None),
        user: User = Depends(staff_user),
        session: AsyncSession = Depends(get_async_session)
):
    try:
        change_value_dict = {}
        value_list = [f"{val} {mes}" for val, mes in zip(values, measurement)]
        change_value_dict = dict(zip(keys, value_list))
        param_name_slug = dict(zip(keys, slug_name))
        new_accident = Accident(
            name=name,
            mechanical_accident=mechanical_accident,
            change_value=change_value_dict,
            param_mapping_names=param_name_slug
        )
        session.add(new_accident)
        await session.commit()

        link_model = model_accident_association.insert().values(model_id=model_id, accident_id=new_accident.id)
        await session.execute(link_model)
        await session.commit()

        return RedirectResponse(request.headers.get("REFERER"),
                                status_code=HTTPStatus.MOVED_PERMANENTLY)

    except SQLAlchemyError as e:
        print(f"SQLAlchemy ошибка добавлении аварии: {e}")
        await session.rollback()
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "Ошибка при добавлении аварии.",
            'user': user,
            'menu': user_menu
        })
    except Exception as e:
        print(f"Ошибка добавлении аварии: {e}")
        await session.rollback()
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "Ошибка при добавлении аварии.",
            'user': user,
            'menu': user_menu
        })


@router.get("/", response_class=HTMLResponse)
async def get_model_page(request: Request, user: User = Depends(staff_user),
                         session: AsyncSession = Depends(get_async_session)):
    try:
        models = await get_models(session=session)
        return templates.TemplateResponse(
            "/staff/get/model/model.html",
            {
                'request': request,
                'user': user,
                "models": models,
                'title': "ISPU - Модели",
                'menu': user_menu,
            }
        )
    except SQLAlchemyError as e:
        print(f"SQLAlchemy ошибка на странице с моделями: {e}")
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "Ошибка на странице с моделями.",
            'user': user,
            'menu': user_menu
        })
    except Exception as e:
        print(f"Ошибка на странице с моделями: {e}")
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "Ошибка на странице с моделями.",
            'user': user,
            'menu': user_menu
        })


@router.get("/update/{model_id}", response_class=HTMLResponse)
async def get_update_model(request: Request, model_id: int,
                           user: User = Depends(administrator_user),
                           session: AsyncSession = Depends(get_async_session)):
    try:
        model = await get_model_for_id_func(model_id=model_id, session=session)
        selected_fields = model.specification
        model_values = await get_model_value_for_name(sensor_name=model.model_type.name, session=session)
        return templates.TemplateResponse(
            "/staff/update/model/update_model_field.html",
            {
                "request": request,
                'user': user,
                "model": model,
                "model_values": model_values,
                'selected_fields': selected_fields,
                'title': "ISPU - Обновление полей модели!",
                'menu': user_menu,
            }
        )
    except SQLAlchemyError as e:
        print(f"SQLAlchemy ошибка в странице обновления модели: {e}")
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "Ошибка при обновлении модели.",
            'user': user,
            'menu': user_menu
        })
    except Exception as e:
        print(f"Ошибка в странице обновления модели: {e}")
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "Ошибка при обновлении модели.",
            'user': user,
            'menu': user_menu
        })


@router.post("/update/{model_id}", response_class=HTMLResponse)
async def post_update_model(request: Request, model_id: int, fields_selected: list[int] = Form(None),
                            user: User = Depends(administrator_user),
                            session: AsyncSession = Depends(get_async_session)):
    try:
        if not fields_selected:
            return templates.TemplateResponse("profile/index.html", {
                "request": request,
                "error": "Вы не выбрали параметры для модели.",
                'user': user,
                'menu': user_menu
            })
        model = await get_model_for_id_func(model_id=model_id, session=session)
        fields = await get_model_values_for_id(session=session, fields_id=fields_selected)

        fields_dict = dict()
        for field in fields:
            fields_dict[field.field] = f"{field.value} {field.measurement}"

        id: int = await create_or_get_model_type(session=session, model_type_name=model.model_type.name)

        await update_model(session=session, model=model, specification=fields_dict, model_type_id=id)

        return RedirectResponse(url=request.url_for("get_model_for_id", model_id=model.id),
                                status_code=HTTPStatus.MOVED_PERMANENTLY)

    except SQLAlchemyError as e:
        print(f"SQLAlchemy ошибка при обновления модели: {e}")
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "Ошибка при обновлении модели.",
            'user': user,
            'menu': user_menu
        })
    except Exception as e:
        print(f"Ошибка при обновления модели: {e}")
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "Ошибка при обновлении модели.",
            'user': user,
            'menu': user_menu
        })


@router.get("/model-value/", response_class=HTMLResponse)
async def get_model_value(request: Request, user: User = Depends(administrator_user),
                               session: AsyncSession = Depends(get_async_session)):
    try:
        model_value = await get_model_values_group_by_type(session=session)
        return templates.TemplateResponse(
            "/staff/get/model-value/model-value.html",
            {
                'request': request,
                'user': user,
                'menu': user_menu,
                'title': "ISPU - Создание исходной модели!",
                'model_value': model_value,
            }
        )
    except SQLAlchemyError as e:
        print(f"SQLAlchemy ошибка в странице исходных моделей: {e}")
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "Ошибка на странице исходных моделей.",
            'user': user,
            'menu': user_menu
        })
    except Exception as e:
        print(f"Ошибка в странице исходных моделей: {e}")
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "Ошибка на странице исходных моделей.",
            'user': user,
            'menu': user_menu
        })


@router.post("/accident/delete/{accident_id}/{model_id}")
async def delete_accident_for_model(accident_id: int, model_id: int,
                                         session: AsyncSession = Depends(get_async_session),
                                         user: User = Depends(administrator_user)):
    try:
        await delete_accident_for_model_func(session=session, model_id=model_id, accident_id=accident_id)
        return {"detail": "Accident deleted successfully"}
    except SQLAlchemyError as e:
        print(f"SQLAlchemy ошибка при удалении аварии из модели: {e}")
        await session.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")
    except Exception as e:
        print(e)
        await session.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/accident/add/{model_id}", response_class=HTMLResponse)
async def get_add_accident_model(
        request: Request,
        model_id: int,
        user: User = Depends(administrator_user),
        session: AsyncSession = Depends(get_async_session)
):
    try:
        model = await get_model_for_id_func(session=session, model_id=model_id)
        return templates.TemplateResponse(
            "/staff/update/accident/add_accident_model.html",
            {
                'request': request,
                'user': user,
                'menu': user_menu,
                'title': "ISPU - Добавление аварии!",
                'model': model,
            }
        )
    except SQLAlchemyError as e:
        print(f"SQLAlchemy ошибка в странице добавление аварии в модель: {e}")
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "Возникла ошибка при добавлении аварии.",
            'user': user,
            'menu': user_menu
        })
    except Exception as e:
        print(f"Ошибка в странице добавление аварии в модель: {e}")
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "Возникла ошибка при добавлении аварии.",
            'user': user,
            'menu': user_menu
        })


@router.get("/model-value/create/", response_class=HTMLResponse)
async def get_create_model_value(request: Request, user: User = Depends(administrator_user)):
    try:
        return templates.TemplateResponse(
            "/staff/create/model-value/create_model-value.html",
            {
                'request': request,
                'user': user,
                'menu': user_menu,
                'title': "ISPU - Создание значения для модели!",
            }
        )
    except SQLAlchemyError as e:
        print(f"SQLAlchemy ошибка в странице создания значения для модели: {e}")
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "Возникла ошибка при добавлении значения в БД.",
            'user': user,
            'menu': user_menu
        })
    except Exception as e:
        print(f"Ошибка в странице создания значения для модели: {e}")
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "Возникла ошибка при добавлении значения в БД.",
            'user': user,
            'menu': user_menu
        })


@router.post("/model-value/create/", response_class=HTMLResponse)
async def post_create_model_value(
        request: Request,
        name: str = Form(...),
        keys: list[str] = Form(None),
        values: list[str] = Form(None),
        slug_name: list[str] = Form(None),
        measurement: list[str] = Form(None),
        user: User = Depends(administrator_user),
        session: AsyncSession = Depends(get_async_session)
):
    try:
        await create_model_values_or_update(name=name, keys=keys, values=values, measurements=measurement,
                                            name_eng_params=slug_name, session=session)
        return RedirectResponse(url=request.url_for("get_model_value"), status_code=HTTPStatus.MOVED_PERMANENTLY)
    except SQLAlchemyError as e:
        print(f"SQLAlchemy при добавлении\обновлении параметра модели: {e}")
        await session.rollback()
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "Ошибка при занесении значения модели.",
            'user': user,
            'menu': user_menu
        })
    except Exception as e:
        print(f"SQLAlchemy при добавлении\обновлении параметра модели: {e}")
        await session.rollback()
        return templates.TemplateResponse("profile/index.html", {
            "request": request,
            "error": "Ошибка при занесении значения модели.",
            'user': user,
            'menu': user_menu
        })