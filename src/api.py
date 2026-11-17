
from typing import Annotated

from contextlib import asynccontextmanager
import threading

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src.parser import EtagiParser


parser_instance: EtagiParser | None = None
driver_lock = threading.Lock()


@asynccontextmanager
async def lifespan(app: FastAPI):
    global parser_instance

    parser_instance = EtagiParser(headless=True)

    yield

    if parser_instance:
        parser_instance.close()


app = FastAPI(
    title="Etagi Realty Search Backend",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ListingItem(BaseModel):
    id: str | None
    url: str
    title: str | None
    area_m2: float | None = None
    floor: str | None = None
    price_rub: int | None
    old_price_rub: int | None = None
    price_per_m2_rub: int | None
    address: str | None
    images: list[str]
    raw_lines: list[str]

class SearchResponse(BaseModel):
    search_url: str
    count: int
    items: list[ListingItem]


@app.get("/api/realty/search", response_model=SearchResponse)
def search_realty(
    rooms: Annotated[list[int] | None, Query(description="Number of rooms, e.g. ?rooms=2&rooms=3")] = None,
    price_min: Annotated[int | None, Query(ge=0)] = None,
    price_max: Annotated[int | None, Query(ge=0)] = None,
    square_min: Annotated[int | None, Query(gt=0)] = None,
    square_max: Annotated[int | None, Query(gt=0)] = None,
    district_ids: Annotated[list[int] | None, Query(description="District IDs, e.g. ?district_ids=38039")] = None,
    street_ids: Annotated[list[int] | None, Query()] = None,
    newcomplex_ids: Annotated[list[int] | None, Query()] = None,
    floor_min: Annotated[int | None, Query(ge=1)] = None,
    floor_max: Annotated[int | None, Query(ge=1)] = None,
    building_year_min: Annotated[int | None, Query(ge=1900)] = None,
    order: Annotated[str | None, Query(description="Sort order parameter")] = None,
    page: Annotated[int, Query(ge=1)] = 1,
):
    if parser_instance is None:
        raise HTTPException(status_code=503, detail="Parser service not initialized")

    with driver_lock:
        try:
            result = parser_instance.search(
                rooms=rooms,
                price_min=price_min,
                price_max=price_max,
                square_min=square_min,
                square_max=square_max,
                district_ids=district_ids,
                street_ids=street_ids,
                newcomplex_ids=newcomplex_ids,
                floor_min=floor_min,
                floor_max=floor_max,
                building_year_min=building_year_min,
                order=order,
                page=page,
            )
            return result
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Scraping failed: {exc}")
