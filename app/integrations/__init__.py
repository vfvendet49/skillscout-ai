"""TheirStack job search integration"""
from typing import List
from ..schemas import Job, UserProfile, UserPreferences


async def search_jobs(
    user_profile: UserProfile,
    user_preferences: UserPreferences,
    limit: int = 50
) -> List[Job]:
    """Search jobs using TheirStack API"""
    # TODO: Implement actual TheirStack API integration
    return []
