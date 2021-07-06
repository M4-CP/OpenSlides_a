# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2016-11-14 11:16
from __future__ import unicode_literals

from django.db import migrations, models


def migrate_groups_and_user_permissions(apps, schema_editor):
    """
    This function migrates the database to the new groups logic:
    - Rename group 'Anonymous' (pk=1) to 'Default'
    - Rename group 'Registered users' (pk=2) to 'Previous group Registered'
    - Add all users who are not in any group to this group (pk=2)
    - Add all permissions of 'Previous group Registered' to all other groups (except 'Default')

    But only run this migration if:
    - there are groups in the database,
    - the name of the first group is 'Guests',
    - the name of the second group is 'Registered users'.
    """
    User = apps.get_model("users", "User")
    Group = apps.get_model("auth", "Group")

    try:
        group_default = Group.objects.get(pk=1)
        group_registered = Group.objects.get(pk=2)
    except Group.DoesNotExist:
        # One of the groups does not exist. Just do nothing.
        pass
    else:
        if (
            group_default.name == "Guests"
            and group_registered.name == "Registered users"
        ):
            # Rename groups pk 1 and 2.
            group_default.name = "Default"
            group_default.save()
            group_registered.name = "Previous group Registered"
            group_registered.save()

            # Move users without groups to group pk 2.
            users = User.objects.all()
            for user in users:
                if not user.groups.exists():
                    user.groups.add(group_registered)

            # Copy permissions of group pk 2 to all other groups except pk 1.
            groups = Group.objects.filter(pk__gt=2)
            for group in groups:
                for permission in group_registered.permissions.all():
                    group.permissions.add(permission)


class Migration(migrations.Migration):

    dependencies = [
        ("auth", "0008_alter_user_username_max_length"),
        ("users", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="is_committee",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="user",
            name="number",
            field=models.CharField(blank=True, default="", max_length=50),
        ),
        migrations.RunPython(migrate_groups_and_user_permissions),
    ]
