from datetime import timedelta

from django import forms
from django.utils.timezone import now


class ChartSettingsForm(forms.Form):
    def __init__(self, stats, user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for ch_filter in stats.criteriatostatsm2m_set.filter(use_as="chart_filter").order_by(
            "order"
        ):
            dy_map = ch_filter.get_dynamic_choices(user=user)
            if dy_map:
                self.fields[f"select_box_dynamic_{ch_filter.id}"] = forms.ChoiceField(
                    choices=[("", "-------")] + list(dy_map.values()),
                    label=ch_filter.criteria.criteria_name,
                    initial=ch_filter.default_option,
                )
                self.fields[f"select_box_dynamic_{ch_filter.id}"].widget.attrs[
                    "class"
                ] = "chart-input"

        self.fields["graph_key"] = forms.CharField(
            initial=stats.graph_key,
            widget=forms.HiddenInput(attrs={"class": "hidden_graph_key"}),
        )

        multiple_series = stats.criteriatostatsm2m_set.filter(use_as="multiple_series")
        if multiple_series.exists():
            choices = (
                multiple_series.select_related("stats__default_multiseries_criteria", "criteria")
                .order_by("order")
                .values_list("id", "criteria__criteria_name")
            )
            self.fields["select_box_multiple_series"] = forms.ChoiceField(
                label="Divide",
                choices=[("", "-------")] + list(choices),
                initial=stats.default_multiseries_criteria.id
                if stats.default_multiseries_criteria
                else None,
            )
            self.fields["select_box_multiple_series"].widget.attrs[
                "class"
            ] = "chart-input select_box_multiple_series"

        if len(stats.allowed_type_operation_field_name) > 1:
            self.fields["select_box_operation"] = forms.ChoiceField(
                choices=stats.allowed_type_operation_field_name_choices(),
                label="Operation",
                initial=stats.type_operation_field_name,
            )
            self.fields["select_box_operation"].widget.attrs["class"] = "chart-input"

        operations_list = stats.get_operations_list()
        if operations_list and len(operations_list) > 1:
            self.fields["select_box_operation_field"] = forms.ChoiceField(
                choices=[("", "(divide all)")] + [(o, o) for o in operations_list],
                label="Field",
                initial=operations_list[0],
            )
            self.fields["select_box_operation_field"].widget.attrs["class"] = "chart-input"

        if len(stats.allowed_time_scales) > 1:
            self.fields["select_box_interval"] = forms.ChoiceField(
                choices=stats.allowed_time_scales_choices(),
                label="Scale",
                initial=stats.default_time_scale,
            )
            self.fields["select_box_interval"].widget.attrs["class"] = "chart-input"

        if len(stats.allowed_chart_types) > 1:
            self.fields["select_box_chart_type"] = forms.ChoiceField(
                choices=stats.allowed_chart_types_choices(),
                label="Chart",
                initial=stats.default_chart_type,
            )
            self.fields["select_box_chart_type"].widget.attrs[
                "class"
            ] = "chart-input select_box_chart_type"

        self.fields["time_since"] = forms.DateField(
            label="Since",
            initial=(now() - timedelta(days=stats.default_time_period)).strftime("%Y-%m-%d"),
            widget=forms.TextInput(
                attrs={"type": "date", "class": "chart-input select_box_date_since"}
            ),
        )
        self.fields["time_until"] = forms.DateField(
            label="Until",
            initial=now().strftime("%Y-%m-%d"),
            widget=forms.TextInput(
                attrs={"type": "date", "class": "chart-input select_box_date_until"}
            ),
        )
