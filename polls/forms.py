import logging
logger = logging.getLogger('mysite.log')
from django import forms
from django.utils.translation import ugettext_lazy as _
from polls.models import Choice


class PollForm(forms.Form):
    def __init__(self, *args, **kwargs):
        # We require an ``instance`` parameter.
        self.instance = kwargs.pop('instance')

        # We call ``super`` (without the ``instance`` param) to finish
        # off the setup.
        super(PollForm, self).__init__(*args, **kwargs)

        # We add on a ``choice`` field based on the instance we've got.
        # This has to be done here (instead of declaratively) because the
        # ``Poll`` instance will change from request to request.

        # change the 'widget' based on max_answers of the poll
        #TODO: not allowed to be zero or negetive
        #TODO: where to check for that
        if self.instance.max_answers == 1:
            #empty_labelis for None or Other field if you want
            self.fields['choice'] = forms.ModelChoiceField(
                queryset=Choice.objects.filter(poll=self.instance.pk),
                empty_label=None,
                widget=forms.RadioSelect)
            #TODO: would be nice to do this
            #self.fields['choice'] = forms.ModelMultipleChoiceField(
                #queryset=Choice.objects.filter(poll=self.instance.pk),
                #widget=forms.RadioSelect)
        else:
            self.fields['choice'] = forms.ModelMultipleChoiceField(
                queryset=Choice.objects.filter(poll=self.instance.pk),
                widget=forms.CheckboxSelectMultiple())

    def clean_choice(self):
        choices = self.cleaned_data['choice']
        logger.info(type(choices))
        logger.info(type(choices) != Choice)
        #if choices is a QuerySet
        if type(choices) != Choice:
            if choices.count() > self.instance.max_answers:
            #TODO: for 1.6 best practices
            #raise forms.ValidationError(
            #    _("Too many options selected. Max is %(value)s"),
            #    code='invalid',
            #    params={'value': choices.count()},
            #)
                raise forms.ValidationError(
                     _("Too many options selected. Max is %s" %
                         self.instance.max_answers))
        return choices

    def save(self):
        if not self.is_valid():
            raise forms.ValidationError(
                _("PollForm was not validated before calling 'save()'."))

        choices = self.cleaned_data['choice']
        # If is not a QuerySet of Choices make it a list to iterate through it
        if type(choices) == Choice:
            choices = [choices]

        for choice in choices:
            choice.record_vote()
        return choice

'''
def vote_form_class(poll):
    choices = [(i.id, _(i.choice_text)) for i in poll.choices.all()]

    class _VoteForm(forms.Form):
        vote = forms.ChoiceField(choices=choices, widget=forms.RadioSelect())

        def save(self):
            if not self.is_valid():
                raise forms.ValidationError(
                    _("Poll Form was not validated before .save()"))

            data = self.cleaned_data
            choice_id = data['vote']
            choice = Choice.objects.get(id=choice_id)
            choice.record_vote()

    return _VoteForm
'''
