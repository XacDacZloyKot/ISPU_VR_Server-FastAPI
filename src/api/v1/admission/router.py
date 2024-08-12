from fastapi import APIRouter, Body, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from src.pages.crud import get_admission_for_id
from api.v1.admission.crud import update_admission_result as update_admission_result_crud
from src.database import get_async_session

router = APIRouter(
    prefix='/api/v1',
    tags=['API']
)


@router.post("/admission-result/update/")
async def update_admission_result(rating=Body(embed=True),
                                  admission_id=Body(embed=True),
                                  status=Body(embed=True),
                                  session: AsyncSession = Depends(get_async_session)):
    try:
        print("Updating admission result")
        admission = await get_admission_for_id(admission_id=admission_id, session=session)
        await update_admission_result_crud(session=session, rating=rating, admission=admission, status=status)
        return Response(status_code=201, content=str(admission), media_type="text/plain")
    except Exception as e:
        print(e)
        return Response(status_code=500, content=str(e))