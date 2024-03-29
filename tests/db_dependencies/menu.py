"""Module contains menu repository"""

from uuid import UUID

from db_dependencies.models import dish_table, menu_table, submenu_table
from sqlalchemy import Integer, cast, delete, func, insert, select, update
from sqlalchemy.exc import IntegrityError, NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.expression import Select

from tests.test_schemas import MenuSchema, OutputMenuSchema


def get_one_menu(m_id: UUID) -> Select:
    """Get complex ORM statement for getting one menu with all child counters"""
    sub_without_id = (
        select(func.count(submenu_table.c.id).label('submenus_count'), submenu_table.c.menu_id)
        .group_by(submenu_table.c.menu_id)
        .cte()
    )
    subs_with_id = (
        select(sub_without_id.c.submenus_count, sub_without_id.c.menu_id, submenu_table.c.id)
        .outerjoin(sub_without_id, sub_without_id.c.menu_id == submenu_table.c.menu_id)
        .cte()
    )
    dish_c = (
        select(func.count(dish_table.c.id).label('dishes_count'), dish_table.c.submenu_id, )
        .group_by(dish_table.c.submenu_id)
        .cte()
    )

    counters = (
        select(
            func.sum(dish_c.c.dishes_count).label('dishes_count'),
            func.count(subs_with_id.c.submenus_count).label('submenus_count'),
            subs_with_id.c.menu_id
        )
        .outerjoin(dish_c, subs_with_id.c.id == dish_c.c.submenu_id)
        .group_by(subs_with_id.c.menu_id)
        .cte()
    )

    get_one = (
        select(menu_table,
               cast(func.coalesce(counters.c.dishes_count, 0), Integer).label('dishes_count'),
               func.coalesce(counters.c.submenus_count, 0).label('submenus_count'))
        .distinct()
        .where(menu_table.c.id == m_id)
        .outerjoin_from(menu_table, counters, menu_table.c.id == counters.c.menu_id)

    )

    return get_one


def get_all_menus() -> Select:
    """Get complex ORM statement for getting all menus with all child counters"""
    sub_without_id = (
        select(func.count(submenu_table.c.id).label('submenus_count'), submenu_table.c.menu_id)
        .group_by(submenu_table.c.menu_id)
        .cte()
    )
    subs_with_id = (
        select(sub_without_id.c.submenus_count, sub_without_id.c.menu_id, submenu_table.c.id)
        .outerjoin(sub_without_id, sub_without_id.c.menu_id == submenu_table.c.menu_id)
        .cte()
    )
    dish_c = (
        select(func.count(dish_table.c.id).label('dishes_count'), dish_table.c.submenu_id, )
        .group_by(dish_table.c.submenu_id)
        .cte()
    )

    counters = (
        select(
            func.sum(dish_c.c.dishes_count).label('dishes_count'),
            func.count(subs_with_id.c.submenus_count).label('submenus_count'),
            subs_with_id.c.menu_id
        )
        .outerjoin(dish_c, subs_with_id.c.id == dish_c.c.submenu_id)
        .group_by(subs_with_id.c.menu_id)
        .cte()
    )

    get_all_menu = (
        select(menu_table,
               cast(func.coalesce(counters.c.dishes_count, 0), Integer).label('dishes_count'),
               func.coalesce(counters.c.submenus_count, 0).label('submenus_count'))
        .distinct()
        .outerjoin_from(menu_table, counters, menu_table.c.id == counters.c.menu_id)

    )

    return get_all_menu


class MenuRepository:
    """Menu repository for SQL DB"""

    def __init__(self, session: AsyncSession):
        self.s = session

    async def create_one(self, menu: MenuSchema) -> OutputMenuSchema:
        """Create one menu"""
        stmt = insert(menu_table).values(**menu.model_dump()).returning(menu_table.c.id)
        dict_id: dict = (await self.s.execute(stmt)).first()._asdict()
        result: dict = (await self.s.execute(get_one_menu(dict_id['id']))).first()._asdict()
        return OutputMenuSchema(**result)

    async def get_all(self) -> list[OutputMenuSchema]:
        """Get all menus"""
        query = get_all_menus()
        result = (await self.s.execute(query)).all()
        if len(result) > 0:
            return [OutputMenuSchema(**x._asdict()) for x in result]
        return []

    async def get_one(self, sm_id: UUID) -> OutputMenuSchema | None:
        """Get one menu"""
        query = get_one_menu(sm_id)
        try:
            result = await self.s.execute(query)
            return OutputMenuSchema(**result.one()._asdict())
        except (NoResultFound, AttributeError):
            return None

    async def delete_one(self, sm_id: UUID) -> bool | None:
        """Delete one menu"""
        stmt = delete(menu_table).filter_by(id=sm_id)
        try:
            await self.s.execute(stmt)
            return True
        except IntegrityError:
            return None

    async def update_one(self, sm_id: UUID, menu: MenuSchema) -> OutputMenuSchema | None:
        """Update one menu"""
        stmt = (update(menu_table)
                .values(**menu.model_dump())
                .where(menu_table.c.id == sm_id)
                .returning(menu_table.c.id))
        try:
            dict_id = (await self.s.execute(stmt)).first()._asdict()
            result = (await self.s.execute(get_one_menu(dict_id['id']))).first()._asdict()
            return OutputMenuSchema(**result)
        except (IntegrityError, AttributeError):
            return None
