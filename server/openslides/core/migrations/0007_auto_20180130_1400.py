# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2018-01-30 13:00
from __future__ import unicode_literals

from django.contrib.auth.models import Permission
from django.db import migrations


def delete_old_logo_permission(apps, schema_editor):
    """
    Deletes the old 'can_manage_logo' permission which is replaced with
    'can_manage_logos_and_fonts'. If this is a fresh database, no permission
    will be deleted, in fact the old permission does not exist. Django creates
    the permission after all migration and the old one is not generated.
    If this is an old database, the new permission will be created and the old
    one deleted. Also it will be assigned to the groups, which had the old permission.
    """
    perm = Permission.objects.filter(codename="can_manage_logos")

    if len(perm):
        perm = perm.get()
        # Save content_type for manual creation of new permissions.
        content_type = perm.content_type

        # Save groups. list() is necessary to evaluate the database query right now.
        groups = list(perm.group_set.all())

        # Delete permission
        perm.delete()

        # Create new permission
        perm = Permission.objects.create(
            codename="can_manage_logos_and_fonts",
            name="Can manage logos and fonts",
            content_type=content_type,
        )

        for group in groups:
            group.permissions.add(perm)
            group.save()


class Migration(migrations.Migration):

    dependencies = [("core", "0006_auto_20180123_0903")]

    operations = [
        migrations.AlterModelOptions(
            name="configstore",
            options={
                "default_permissions": (),
                "permissions": (
                    ("can_manage_config", "Can manage configuration"),
                    ("can_manage_logos_and_fonts", "Can manage logos and fonts"),
                ),
            },
        ),
        migrations.RunPython(delete_old_logo_permission),
    ]
