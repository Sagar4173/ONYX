"""Shared dependencies for report route modules."""
from typing import List

from models.project import Project


async def get_user_project_ids(user_id: str) -> List[str]:
    """Get list of project IDs accessible to the user"""
    from beanie.operators import Or
    projects = await Project.find(
        Or(
            Project.owner_id == user_id,
            Project.team_members.user_id == user_id,
        )
    ).to_list()
    return [str(p.id) for p in projects]
