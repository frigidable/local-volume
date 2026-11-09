from lv_backend.data import objects as data_objects
from lv_backend.domain import derived_parameters
from lv_backend.data.storage import Storage
from lv_backend.presentation import schemas


def list_objects(storage: Storage) -> schemas.ObjectsListResponse:
    column_schema = data_objects.select_schema(storage, data_objects.SUMMARY_COLUMNS)
    rows = data_objects.select_objects(storage)
    return schemas.ObjectsListResponse(
        data=schemas.ObjectSummaryColumns(
            pgc=[row["pgc"] for row in rows],
            name=[row["name"] for row in rows],
            ra=[row["ra"] for row in rows],
            dec=[row["dec"] for row in rows],
            names=[row["names"] for row in rows],
        ),
        schema=column_schema,
    )


def get_object(storage: Storage, pgc: int) -> schemas.ObjectGetResponse | None:
    row = data_objects.select_object(storage, pgc)
    if row is None:
        return None
    column_schema = data_objects.select_schema(storage, data_objects.DETAIL_COLUMNS)
    return schemas.ObjectGetResponse(
        data=schemas.ObjectDetail(
            pgc=row["pgc"],
            name=row["name"],
            ra=row["ra"],
            e_ra=row["e_ra"],
            dec=row["dec"],
            e_dec=row["e_dec"],
            bt=row["bt"],
            e_bt=row["e_bt"],
            kt=row["kt"],
            e_kt=row["e_kt"],
            v_hel=row["v_hel"],
            e_v_hel=row["e_v_hel"],
            v_lg=row["v_lg"],
            e_v_lg=row["e_v_lg"],
            a50=row["a50"],
            e_a50=row["e_a50"],
            b50=row["b50"],
            e_b50=row["e_b50"],
            type_name=row["type_name"],
            dist=row["dist"],
            names=row["names"],
        ),
        schema=column_schema,
        derived=[
            schemas.CalculatedParameter(
                key=item.key,
                label=item.label,
                unit=item.unit,
                method=item.method,
                value=item.value,
                status=item.status,
                reason=item.reason,
            )
            for item in derived_parameters.calculate(
                distance_mpc=row["dist"], b_magnitude=row["bt"]
            )
        ],
    )
