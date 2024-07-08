import json

from .apps import AbsCalculationRule
from .config import CLASS_RULE_PARAM_VALIDATION, \
    DESCRIPTION_CONTRIBUTION_VALUATION, FROM_TO
from contribution_plan.models import ContributionPlanBundleDetails
from core.signals import Signal
from core import datetime
from django.contrib.contenttypes.models import ContentType
from insuree.models import Insuree

class ContributionPlanCalculationRuleComores(AbsCalculationRule):
    version = 1
    uuid = "2e999dd4-04a0-2ba6-ac47-2a91cfa5e9b7"
    calculation_rule_name = "Contribution paamg"
    description = DESCRIPTION_CONTRIBUTION_VALUATION
    impacted_class_parameter = CLASS_RULE_PARAM_VALIDATION
    date_valid_from = datetime.datetime(2000, 1, 1)
    date_valid_to = None
    status = "active"
    from_to = FROM_TO
    type = "account_receivable"
    sub_type = "contribution"

    signal_get_rule_name = Signal([])
    signal_get_rule_details = Signal([])
    signal_get_param = Signal([])
    signal_get_linked_class = Signal([])
    signal_calculate_event = Signal([])
    signal_convert_from_to = Signal([])

    @classmethod
    def ready(cls):
        now = datetime.datetime.now()
        condition_is_valid = (now >= cls.date_valid_from and now <= cls.date_valid_to) \
            if cls.date_valid_to else (now >= cls.date_valid_from and cls.date_valid_to is None)
        if condition_is_valid:
            if cls.status == "active":
                # register signals getParameter to getParameter signal and getLinkedClass ot getLinkedClass signal
                cls.signal_get_rule_name.connect(cls.get_rule_name, dispatch_uid="on_get_rule_name_signal")
                cls.signal_get_rule_details.connect(cls.get_rule_details, dispatch_uid="on_get_rule_details_signal")
                cls.signal_get_param.connect(cls.get_parameters, dispatch_uid="on_get_param_signal")
                cls.signal_get_linked_class.connect(cls.get_linked_class, dispatch_uid="on_get_linked_class_signal")
                cls.signal_calculate_event.connect(cls.run_calculation_rules, dispatch_uid="on_calculate_event_signal")

    @classmethod
    def active_for_object(cls, instance, context, type='account_receivable', sub_type='contribution'):
        return instance.__class__.__name__ == "ContributionPlan" \
               and context in ["create", "update"] \
               and cls.check_calculation(instance)

    @classmethod
    def check_calculation(cls, instance):
        match = False
        class_name = instance.__class__.__name__
        list_class_name = [
            "PolicyHolder", "ContributionPlan",
            "PolicyHolderInsuree", "ContractDetails",
            "ContractContributionPlanDetails", "ContributionPlanBundle"
        ]
        if class_name == "ABCMeta":
            match = str(cls.uuid) == str(instance.uuid)
        elif class_name == "ContributionPlan":
            match = str(cls.uuid) == str(instance.calculation)
        elif class_name == "ContributionPlanBundle":
            list_cpbd = list(ContributionPlanBundleDetails.objects.filter(
                contribution_plan_bundle=instance
            ))
            for cpbd in list_cpbd:
                if match is False:
                    if cls.check_calculation(cpbd.contribution_plan):
                        match = True
        else:
            related_fields = [
                f.name for f in instance.__class__._meta.fields
                if f.get_internal_type() == 'ForeignKey' and f.remote_field.model.__name__ in list_class_name
            ]
            for rf in related_fields:
                match = cls.check_calculation(getattr(instance, rf))
        return match

    @classmethod
    def calculate(cls, instance, **kwargs):
        family = kwargs.get('family', None)
        if instance.__class__.__name__ == "ContributionPlan":
            # check type of json_ext - in case of string - json.loads
            cp_params = instance.json_ext
            if isinstance(cp_params, str):
                cp_params = json.loads(cp_params)
            lumpsum = 0
            childsum = 0
            adultmalesum = 0
            adultfemalesum = 0
            if cp_params:
                cp_params = cp_params["calculation_rule"] if "calculation_rule" in cp_params else None
                if cp_params:
                    if "lumpsum" in cp_params:
                        lumpsum = int(cp_params["lumpsum"])
                    if "childsum" in cp_params:
                        childsum = int(cp_params["childsum"])
                    if "adultmalesum" in cp_params:
                        adultmalesum = int(cp_params["adultmalesum"])
                    if "adultfemalesum" in cp_params:
                        adultfemalesum = int(cp_params["adultfemalesum"])
            amount = lumpsum
            if family:
                members = Insuree.objects.filter(
                    family_id=family.id, validity_to__isnull=True
                )
                for membre in members:
                    if membre.relationship:
                        if str(membre.relationship.relation).lower() not in ["spouse", "époux", "son/daughter", "fils/fille"]:
                            # The member is not a son or daughter nor spouse. So hes a stranger
                            date_format = "%Y-%m-%d"
                            today = datetime.datetime.strptime(str(datetime.datetime.now().date()), date_format)
                            insuree_dob = datetime.datetime.strptime(str(membre.dob), date_format)
                            delta = today - insuree_dob
                            age = int(round(delta.days / 365.0))
                            if age < 21:
                                # add amount for stranger child
                                amount += childsum
                            else:
                                # its an adult
                                if membre.gender:
                                    if membre.gender.code in ["F", " F"]:
                                        amount += adultfemalesum
                                    else:
                                        amount += adultmalesum
            return amount
        else:
            return False

    @classmethod
    def get_linked_class(cls, sender, class_name, **kwargs):
        list_class = []
        if class_name != None:
            model_class = ContentType.objects.filter(model__iexact=class_name).first()
            if model_class:
                model_class = model_class.model_class()
                list_class = list_class + \
                             [f.remote_field.model.__name__ for f in model_class._meta.fields
                              if f.get_internal_type() == 'ForeignKey' and f.remote_field.model.__name__ != "User"]
        else:
            list_class.append("Calculation")
        # because we have calculation in ContributionPlan
        #  as uuid - we have to consider this case
        if class_name == "ContributionPlan":
            list_class.append("Calculation")
        # because we have no direct relation in ContributionPlanBundle
        #  to ContributionPlan we have to consider this case
        if class_name == "ContributionPlanBundle":
            list_class.append("ContributionPlan")
        return list_class