from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.comments.models import Comment


class CommentRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_comment(
        self,
        task_id: int,
        user_id: int,
        content: str,
    ) -> Comment:

        comment = Comment(
            task_id=task_id,
            user_id=user_id,
            content=content,
        )

        self.db.add(comment)

        await self.db.flush()
        await self.db.commit()
        await self.db.refresh(comment)

        return comment

    async def get_comment(
        self,
        comment_id: int,
        task_id: int,
    ) -> Comment | None:

        result = await self.db.execute(
            select(Comment).where(
                Comment.id == comment_id,
                Comment.task_id == task_id,
            )
        )

        return result.scalar_one_or_none()

    async def get_task_comments(
        self,
        task_id: int,
    ) -> list[Comment]:

        result = await self.db.execute(
            select(Comment)
            .where(
                Comment.task_id == task_id,
            )
            .order_by(
                Comment.created_at.asc(),
            )
        )

        return list(result.scalars().all())

    async def update_comment(
        self,
        comment: Comment,
        content: str,
    ) -> Comment:

        comment.content = content

        await self.db.flush()
        await self.db.commit()
        await self.db.refresh(comment)

        return comment

    async def delete_comment(
        self,
        comment: Comment,
    ) -> None:

        await self.db.delete(comment)

        await self.db.flush()
        await self.db.commit()