import asyncio

from sqlalchemy import select

from app.database.database import AsyncSessionLocal
from app.modules.organizations.models import (
    Permission,
    Role,
    role_permissions,
)
from app.modules.projects.models import ProjectRole

PERMISSIONS = {
    "organization.read": "View organization",
    "organization.update": "Update organization",
    "organization.delete": "Delete organization",

    "member.read": "View organization members",
    "member.invite": "Invite members",
    "member.remove": "Remove members",

    "role.read": "View roles",
    "role.manage": "Manage roles",

    "project.read": "View projects",
    "project.create": "Create projects",
    "project.update": "Update projects",
    "project.delete": "Delete projects",

    "task.read": "View tasks",
    "task.create": "Create tasks",
    "task.update": "Update tasks",
    "task.delete": "Delete tasks",
    "task.assign": "Assign tasks",

    "report.read": "View reports",
    "report.export": "Export reports",
}


ROLES = {
    "OWNER": "Owner of the organization",
    "ADMIN": "Organization administrator",
    "MEMBER": "Regular organization member",
}


ROLE_PERMISSIONS = {
    "OWNER": [
        "organization.read",
        "organization.update",
        "organization.delete",
        "member.read",
        "member.invite",
        "member.remove",
        "role.read",
        "role.manage",
        "project.read",
        "project.create",
        "project.update",
        "project.delete",
        "task.read",
        "task.create",
        "task.update",
        "task.delete",
        "task.assign",
        "report.read",
        "report.export",
    ],

    "ADMIN": [
        "organization.read",
        "organization.update",
        "member.read",
        "member.invite",
        "member.remove",
        "role.read",
        "role.manage",
        "project.read",
        "project.create",
        "project.update",
        "project.delete",
        "task.read",
        "task.create",
        "task.update",
        "task.delete",
        "task.assign",
        "report.read",
        "report.export",
    ],

    "MEMBER": [
        "organization.read",
        "project.read",
        "task.read",
        "task.update",
    ],
}


async def seed():
    async with AsyncSessionLocal() as db:

        try:

            # ---------------------------------
            # 1. Create / Get Permissions
            # ---------------------------------

            permission_objects = {}

            for permission_name, description in PERMISSIONS.items():

                result = await db.execute(
                    select(Permission).where(
                        Permission.name == permission_name
                    )
                )

                permission = result.scalar_one_or_none()

                if not permission:
                    permission = Permission(
                        name=permission_name,
                        description=description,
                    )

                    db.add(permission)

                permission_objects[permission_name] = permission

            # مهم:
            # ID تمام Permissionها را ایجاد می‌کنیم
            await db.flush()


            # ---------------------------------
            # 2. Create / Get Roles
            # ---------------------------------

            role_objects = {}

            for role_name, description in ROLES.items():

                result = await db.execute(
                    select(Role).where(
                        Role.name == role_name
                    )
                )

                role = result.scalar_one_or_none()

                if not role:
                    role = Role(
                        name=role_name,
                        description=description,
                    )

                    db.add(role)

                role_objects[role_name] = role

            # ID تمام Roleها را ایجاد می‌کنیم
            await db.flush()

            # ---------------------------------
            # 3. Create Project Roles
            # ---------------------------------

            PROJECT_ROLES = {
                "PROJECT_MANAGER": "Project manager",
                "TEAM_LEAD": "Team leader",
                "PR_MEMBER": "Project member",
            }

            project_role_objects = {}

            for role_name, description in PROJECT_ROLES.items():

                result = await db.execute(
                    select(ProjectRole).where(
                        ProjectRole.name == role_name
                    )
                )

                project_role = result.scalar_one_or_none()

                if not project_role:
                    project_role = ProjectRole(
                        name=role_name,
                        description=description,
                    )

                    db.add(project_role)

                project_role_objects[role_name] = project_role

            await db.flush()
            # ---------------------------------
            # 4. Create Role ↔ Permission
            # ---------------------------------

            for role_name, permission_names in ROLE_PERMISSIONS.items():

                role = role_objects[role_name]

                for permission_name in permission_names:

                    permission = permission_objects[permission_name]

                    result = await db.execute(
                        select(role_permissions).where(
                            role_permissions.c.role_id == role.id,
                            role_permissions.c.permission_id == permission.id,
                        )
                    )

                    existing = result.first()

                    if not existing:

                        await db.execute(
                            role_permissions.insert().values(
                                role_id=role.id,
                                permission_id=permission.id,
                            )
                        )


            # ---------------------------------
            # 5. Commit Everything
            # ---------------------------------

            await db.commit()

            print("Seed completed successfully.")


        except Exception:

            await db.rollback()

            raise


if __name__ == "__main__":
    asyncio.run(seed())