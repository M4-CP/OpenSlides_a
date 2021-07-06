from django.conf import settings

from ..utils.auth import get_group_model
from ..utils.rest_api import (
    CharField,
    DecimalField,
    IdPrimaryKeyRelatedField,
    JSONField,
    ModelSerializer,
    SerializerMethodField,
    ValidationError,
)
from .models import BasePoll


BASE_VOTE_FIELDS = (
    "id",
    "weight",
    "value",
    "user",
    "delegated_user",
    "user_token",
    "option",
    "pollstate",
)


class BaseVoteSerializer(ModelSerializer):
    pollstate = SerializerMethodField()

    def get_pollstate(self, vote):
        return vote.option.poll.state


BASE_OPTION_FIELDS = ("id", "yes", "no", "abstain", "poll_id", "pollstate")


class BaseOptionSerializer(ModelSerializer):
    yes = DecimalField(max_digits=15, decimal_places=6, min_value=-2, read_only=True)
    no = DecimalField(max_digits=15, decimal_places=6, min_value=-2, read_only=True)
    abstain = DecimalField(
        max_digits=15, decimal_places=6, min_value=-2, read_only=True
    )

    pollstate = SerializerMethodField()

    def get_pollstate(self, option):
        return option.poll.state


BASE_POLL_FIELDS = (
    "state",
    "type",
    "title",
    "groups",
    "votesvalid",
    "votesinvalid",
    "votescast",
    "options",
    "id",
    "onehundred_percent_base",
    "majority_method",
    "is_pseudoanonymized",
    "voted",
    "entitled_users_at_stop",
)


class BasePollSerializer(ModelSerializer):
    title = CharField(allow_blank=False, required=True)
    groups = IdPrimaryKeyRelatedField(
        many=True, required=False, queryset=get_group_model().objects.all()
    )
    options = IdPrimaryKeyRelatedField(many=True, read_only=True)
    voted = IdPrimaryKeyRelatedField(many=True, read_only=True)
    entitled_users_at_stop = JSONField(required=False)

    def create(self, validated_data):
        """
        Match the 100 percent base to the pollmethod and type. Change the base, if it does not
        fit to the pollmethod or type.
        Set is_pseudoanonymized if type is pseudoanonymous.
        """
        new_100_percent_base = self.norm_100_percent_base(
            validated_data["onehundred_percent_base"],
            validated_data["pollmethod"],
            validated_data["type"],
        )
        if new_100_percent_base is not None:
            validated_data["onehundred_percent_base"] = new_100_percent_base
        if validated_data["type"] == BasePoll.TYPE_PSEUDOANONYMOUS:
            validated_data["is_pseudoanonymized"] = True
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """
        Adjusts the 100%-base to the pollmethod and type. This might be needed,
        if at least one of them was changed. Wrong combinations should be
        also handled by the client, but here we make it sure aswell!

        E.g. the pollmethod is YN, but the 100%-base is YNA, this might not be
        possible (see implementing serializers to see forbidden combinations)

        Also updates is_pseudoanonymized, if needed.
        """
        old_100_percent_base = instance.onehundred_percent_base
        if "type" in validated_data:
            if validated_data["type"] == BasePoll.TYPE_PSEUDOANONYMOUS:
                validated_data["is_pseudoanonymized"] = True
            else:
                validated_data["is_pseudoanonymized"] = False
        instance = super().update(instance, validated_data)

        new_100_percent_base = self.norm_100_percent_base(
            instance.onehundred_percent_base,
            instance.pollmethod,
            instance.type,
            old_100_percent_base,
        )
        if new_100_percent_base is not None:
            instance.onehundred_percent_base = new_100_percent_base
            instance.save()

        return instance

    def validate(self, data):
        """
        Check that the given polltype is allowed.
        """
        # has to be called in function instead of globally to enable tests to change the setting
        ENABLE_ELECTRONIC_VOTING = getattr(settings, "ENABLE_ELECTRONIC_VOTING", False)
        if (
            "type" in data
            and data["type"] != BasePoll.TYPE_ANALOG
            and not ENABLE_ELECTRONIC_VOTING
        ):
            raise ValidationError(
                {
                    "detail": "Electronic voting is disabled. Only analog polls are allowed."
                }
            )
        return data

    def norm_100_percent_base(
        self, onehundred_percent_base, pollmethod, polltype, old_100_percent_base=None
    ):
        if (
            polltype == BasePoll.TYPE_ANALOG
            and onehundred_percent_base == BasePoll.PERCENT_BASE_ENTITLED
        ):
            if (
                old_100_percent_base
                and old_100_percent_base != BasePoll.PERCENT_BASE_ENTITLED
            ):
                return old_100_percent_base
            return BasePoll.PERCENT_BASE_CAST
        return None
