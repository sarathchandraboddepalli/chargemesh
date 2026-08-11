"""ChargeMesh — Organization API Routes"""

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.deps import CurrentOrg, CurrentUser, DB
from app.models.org import OrgMember, Organization
from app.models.user import User
from app.schemas.org import MemberInvite, MemberOut, OrgCreate, OrgOut, OrgUpdate

router = APIRouter()


@router.post("", response_model=OrgOut, status_code=status.HTTP_201_CREATED)
async def create_org(payload: OrgCreate, current_user: CurrentUser, db: DB):
    org = Organization(name=payload.name, org_type=payload.org_type)
    db.add(org)
    await db.flush()

    # Make the creator the owner
    db.add(OrgMember(org_id=org.id, user_id=current_user.id, role="owner"))
    return org


@router.get("/me", response_model=OrgOut)
async def get_my_org(current_org: CurrentOrg):
    return current_org


@router.put("/me", response_model=OrgOut)
async def update_org(payload: OrgUpdate, current_org: CurrentOrg, db: DB):
    if payload.name is not None:
        current_org.name = payload.name
    if payload.tier is not None:
        current_org.tier = payload.tier
    db.add(current_org)
    return current_org


@router.get("/me/members", response_model=list[MemberOut])
async def list_members(current_org: CurrentOrg, db: DB):
    result = await db.execute(
        select(OrgMember, User)
        .join(User, User.id == OrgMember.user_id)
        .where(OrgMember.org_id == current_org.id)
    )
    rows = result.all()
    out = []
    for member, user in rows:
        out.append(MemberOut(
            id=member.id,
            org_id=member.org_id,
            user_id=member.user_id,
            role=member.role,
            joined_at=member.joined_at,
            user_email=user.email,
            user_name=user.full_name,
        ))
    return out


@router.post("/me/members/invite", response_model=MemberOut, status_code=status.HTTP_201_CREATED)
async def invite_member(payload: MemberInvite, current_org: CurrentOrg, db: DB):
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found — they must register first")

    existing = await db.execute(
        select(OrgMember).where(OrgMember.org_id == current_org.id, OrgMember.user_id == user.id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="User is already a member")

    member = OrgMember(org_id=current_org.id, user_id=user.id, role=payload.role)
    db.add(member)
    await db.flush()
    return MemberOut(
        id=member.id,
        org_id=member.org_id,
        user_id=member.user_id,
        role=member.role,
        joined_at=member.joined_at,
        user_email=user.email,
        user_name=user.full_name,
    )


@router.delete("/me/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(user_id: str, current_org: CurrentOrg, current_user: CurrentUser, db: DB):
    import uuid
    result = await db.execute(
        select(OrgMember).where(
            OrgMember.org_id == current_org.id,
            OrgMember.user_id == uuid.UUID(user_id),
        )
    )
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    if str(member.user_id) == str(current_user.id):
        raise HTTPException(status_code=400, detail="Cannot remove yourself")
    await db.delete(member)
