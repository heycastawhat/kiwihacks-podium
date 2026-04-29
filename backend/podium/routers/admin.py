"""
Admin/organizer endpoints. All routes require the requesting user to own the event
(or be a superadmin, which bypasses the ownership check).
Organizers can view event details, attendees, votes, referrals, and the leaderboard,
and can remove attendees.
"""

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Body, Depends, Path
from pydantic import BaseModel
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy import func
from sqlalchemy.orm import selectinload, Load

from podium.db.postgres import (
    User,
    Event,
    EventPrivate,
    EventUpdate,
    Project,
    ProjectPrivate,
    Vote,
    VoteAuditLog,
    Referral,
    get_session,
    scalar_one_or_none,
    scalar_all,
)
from podium.routers.auth import get_current_user
from podium.constants import BAD_ACCESS

router = APIRouter(prefix="/events/admin", tags=["events"])


class UserAttendee(BaseModel):
    id: UUID
    email: str
    display_name: str
    first_name: str
    last_name: str


class VoteResponse(BaseModel):
    id: UUID
    voter_id: UUID
    project_id: UUID
    event_id: UUID
    created_at: datetime | None = None
    ip_address: str = ""
    user_agent: str = ""


class VoteAuditResponse(BaseModel):
    id: UUID
    event_id: UUID
    project_id: UUID
    voter_id: UUID
    actor_id: UUID
    vote_id: UUID | None = None
    action: str
    ip_address: str
    user_agent: str
    reason: str
    created_at: datetime


class VoteSuspicionResponse(BaseModel):
    kind: str
    message: str
    voter_id: UUID | None = None
    ip_address: str = ""
    count: int = 0


class ReferralResponse(BaseModel):
    id: UUID
    content: str
    user_id: UUID
    event_id: UUID


async def get_owned_event(
    event_id: UUID, user: User, session: AsyncSession, *extra_loads: Load
) -> Event:
    """Load an event by ID, asserting ownership (or superadmin).

    Pass additional selectinload() calls to load relationships in the same query,
    avoiding a second round-trip:
        event = await get_owned_event(id, user, session, selectinload(Event.attendees))
    """
    stmt = (
        select(Event)
        .where(Event.id == event_id)
        .options(selectinload(Event.projects), *extra_loads)
    )
    event = await scalar_one_or_none(session, stmt)
    if not event or (event.owner_id != user.id and not user.is_superadmin):
        raise BAD_ACCESS
    return event


@router.get("/{event_id}")
async def get_event_admin(
    event_id: Annotated[UUID, Path(title="Event ID")],
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> EventPrivate:
    event = await get_owned_event(event_id, user, session)
    return EventPrivate.model_validate(event)


@router.patch("/{event_id}")
async def update_event_admin(
    event_id: Annotated[UUID, Path(title="Event ID")],
    update: EventUpdate,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> EventPrivate:
    """Update an event you own. Only fields provided in the body are changed."""
    event = await get_owned_event(event_id, user, session)

    for field, value in update.model_dump(exclude_unset=True).items():
        setattr(event, field, value)

    await session.commit()
    await session.refresh(event)
    return EventPrivate.model_validate(event)


@router.get("/{event_id}/attendees")
async def get_event_attendees(
    event_id: Annotated[UUID, Path(title="Event ID")],
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[UserAttendee]:
    """Get attendees of an event."""
    event = await get_owned_event(event_id, user, session, selectinload(Event.attendees))
    return [
        UserAttendee(
            id=a.id,
            email=a.email,
            display_name=a.display_name,
            first_name=a.first_name,
            last_name=a.last_name,
        )
        for a in event.attendees
    ]


@router.post("/{event_id}/remove-attendee")
async def remove_attendee(
    event_id: Annotated[UUID, Path(title="Event ID")],
    user_id: Annotated[UUID, Body(embed=True)],
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Remove an attendee from an event."""
    event = await get_owned_event(event_id, user, session, selectinload(Event.attendees))
    event.attendees = [a for a in event.attendees if a.id != user_id]
    await session.commit()
    return {"message": "Attendee removed"}


@router.get("/{event_id}/leaderboard", response_model=list[ProjectPrivate])
async def get_event_leaderboard(
    event_id: Annotated[UUID, Path(title="Event ID")],
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[ProjectPrivate]:
    """Get leaderboard for an event (admin only)."""
    await get_owned_event(event_id, user, session)

    projects = await scalar_all(
        session,
        select(Project)
        .where(Project.event_id == event_id)
        .options(
            selectinload(Project.votes),
            selectinload(Project.owner),
            selectinload(Project.collaborators),
        ),
    )
    projects.sort(key=lambda p: p.points, reverse=True)
    return [ProjectPrivate.model_validate(p) for p in projects]


@router.get("/{event_id}/votes")
async def get_event_votes(
    event_id: Annotated[UUID, Path(title="Event ID")],
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[VoteResponse]:
    """Get all votes for an event (admin only)."""
    await get_owned_event(event_id, user, session)
    votes = await scalar_all(session, select(Vote).where(Vote.event_id == event_id))
    return [
        VoteResponse(
            id=v.id,
            voter_id=v.voter_id,
            project_id=v.project_id,
            event_id=v.event_id,
            created_at=v.created_at,
            ip_address=v.ip_address,
            user_agent=v.user_agent,
        )
        for v in votes
    ]


@router.get("/{event_id}/vote-audit")
async def get_event_vote_audit(
    event_id: Annotated[UUID, Path(title="Event ID")],
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[VoteAuditResponse]:
    """Get vote audit log entries for an event (admin only)."""
    await get_owned_event(event_id, user, session)
    logs = await scalar_all(
        session,
        select(VoteAuditLog)
        .where(VoteAuditLog.event_id == event_id)
        .order_by(VoteAuditLog.created_at.desc()),
    )
    return [
        VoteAuditResponse(
            id=log.id,
            event_id=log.event_id,
            project_id=log.project_id,
            voter_id=log.voter_id,
            actor_id=log.actor_id,
            vote_id=log.vote_id,
            action=log.action,
            ip_address=log.ip_address,
            user_agent=log.user_agent,
            reason=log.reason,
            created_at=log.created_at,
        )
        for log in logs
    ]


@router.get("/{event_id}/vote-suspicion")
async def get_event_vote_suspicion(
    event_id: Annotated[UUID, Path(title="Event ID")],
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[VoteSuspicionResponse]:
    """Return lightweight anti-abuse signals for admin review."""
    event = await get_owned_event(event_id, user, session)
    findings: list[VoteSuspicionResponse] = []

    over_limit_rows = (
        await session.exec(
            select(Vote.voter_id, func.count(Vote.id))
            .where(Vote.event_id == event_id)
            .group_by(Vote.voter_id)
            .having(func.count(Vote.id) > event.max_votes_per_user)
        )
    ).all()
    for voter_id, count in over_limit_rows:
        findings.append(
            VoteSuspicionResponse(
                kind="over_limit",
                voter_id=voter_id,
                count=count,
                message=f"Voter has {count} votes; event allows {event.max_votes_per_user}.",
            )
        )

    shared_ip_rows = (
        await session.exec(
            select(Vote.ip_address, func.count(func.distinct(Vote.voter_id)))
            .where(Vote.event_id == event_id, Vote.ip_address != "")
            .group_by(Vote.ip_address)
            .having(func.count(func.distinct(Vote.voter_id)) >= 4)
        )
    ).all()
    for ip_address, count in shared_ip_rows:
        findings.append(
            VoteSuspicionResponse(
                kind="shared_ip",
                ip_address=ip_address,
                count=count,
                message=f"{count} voters used this IP address.",
            )
        )

    burst_rows = (
        await session.exec(
            select(Vote.voter_id, func.count(Vote.id))
            .where(Vote.event_id == event_id)
            .group_by(Vote.voter_id, func.date_trunc("minute", Vote.created_at))
            .having(func.count(Vote.id) >= 3)
        )
    ).all()
    for voter_id, count in burst_rows:
        findings.append(
            VoteSuspicionResponse(
                kind="vote_burst",
                voter_id=voter_id,
                count=count,
                message=f"Voter cast {count} votes in one minute.",
            )
        )

    return findings


@router.get("/{event_id}/referrals")
async def get_event_referrals(
    event_id: Annotated[UUID, Path(title="Event ID")],
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[ReferralResponse]:
    """Get all referrals for an event (admin only)."""
    await get_owned_event(event_id, user, session)
    referrals = await scalar_all(
        session, select(Referral).where(Referral.event_id == event_id)
    )
    return [
        ReferralResponse(id=r.id, content=r.content, user_id=r.user_id, event_id=r.event_id)
        for r in referrals
    ]
