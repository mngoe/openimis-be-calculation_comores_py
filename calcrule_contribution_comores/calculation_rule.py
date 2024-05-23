import json

from .apps import AbsCalculationRule
from .config import CLASS_RULE_PARAM_VALIDATION, \
    DESCRIPTION_CONTRIBUTION_VALUATION, FROM_TO
from contribution_plan.models import ContributionPlanBundleDetails
from core.signals import Signal
from core import datetime
from django.contrib.contenttypes.models import ContentType
from policyholder.models import PolicyHolderInsuree


class ContributionPlanCalculationRuleComores(AbsCalculationRule):
    version = 1
    uuid = "2e999dd4-04a0-2ba6-ac47-2a91cfa5e9b7"
    calculation_rule_name = "CV: percent of income, comores"
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
        print("condition_is_valid ", condition_is_valid)
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
        print("instance.__class__.__name__  ", instance.__class__.__name__)
        return instance.__class__.__name__ == "ContractContributionPlanDetails" \
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
        print("checking class_name ", class_name)
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
        if instance.__class__.__name__ == "ContractContributionPlanDetails":
            # check type of json_ext - in case of string - json.loads
            cp_params, cd_params = instance.contribution_plan.json_ext, instance.contract_details.json_ext
            ph_insuree = PolicyHolderInsuree.objects.filter(
                insuree=instance.contract_details.insuree).first()
            phi_params = ph_insuree.json_ext
            if isinstance(cp_params, str):
                cp_params = json.loads(cp_params)
            if isinstance(cd_params, str):
                cd_params = json.loads(cd_params)
            if isinstance(phi_params, str):
                phi_params = json.loads(phi_params)
            # check if json external calculation rule in instance exists
            if cp_params:
                cp_params = cp_params["calculation_rule"] if "calculation_rule" in cp_params else None
            if cd_params:
                cd_params = cd_params["calculation_rule"] if "calculation_rule" in cd_params else None
            if phi_params:
                phi_params = phi_params["calculation_rule"] if "calculation_rule" in phi_params else None
            if "rate" in cp_params:
                rate = int(cp_params["rate"])
                if cd_params:
                    if "income" in cd_params:
                        income = float(cd_params["income"])
                    elif "income" in phi_params:
                        income = float(phi_params["income"])
                    else:
                        return False
                elif "income" in phi_params:
                    income = float(phi_params["income"])
                else:
                    return False
                value = float(income) * (rate / 100)
                return value
            else:
                return False
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