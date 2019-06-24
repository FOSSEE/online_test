def check_permission(course, unit, user):
    ''' Check if user has permissions for a given unit '''

    teams = list(course.team_set.all())
    user_team_count = user.team_members.filter(name__in=teams).count()

    if user_team_count:

        # Find user's role in team
        role = user.role_set.filter(team__in=teams)

        if role.exists():

            permissions = role.first().permission_set.all()

            object_perms = list(filter(
                lambda x: x.content_object == unit,
                permissions
            ))

            if len(object_perms):
                return object_perms[0]

    return None


def format_perm(permissions):
    perms = []
    for permission in permissions:
        roles = list(map(
            lambda role: role.name,
            permission.role.all()
        ))

        perms.append({
            "id": permission.id,
            "role": ",".join(roles),
            "type": permission.perm_type,
            "course": permission.course.name,
            "unit": permission.content_object
        })

    return perms
