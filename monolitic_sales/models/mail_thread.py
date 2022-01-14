from odoo import models


class MailThread(models.AbstractModel):
    _inherit = 'mail.thread'

    def _message_add_suggested_recipient(self, result, partner=None, email=None, reason=''):
        """ Called by _message_get_suggested_recipients, to add a suggested
            recipient in the result dictionary. The form is :
                partner_id, partner_name<partner_email> or partner_name, reason """
        self.ensure_one()
        if email and not partner:
            # get partner info from email
            partner_info = self._message_partner_info_from_emails([email])[0]
            if partner_info.get('partner_id'):
                partner = self.env['res.partner'].sudo().browse([partner_info['partner_id']])[0]
        if email and email in [val[1] for val in result[self.ids[0]]]:  # already existing email -> skip
            return result
        if partner:
            for p in partner:
                if p and p in self.message_partner_ids:  # recipient already in the followers -> skip
                    return result
                if p and p.id in [val[0] for val in result[self.ids[0]]]:  # already existing partner ID -> skip
                    return result
                if p and p.email:  # complete profile: id, name <email>
                    result[self.ids[0]].append((p.id, p.email_formatted, reason))
                elif p:  # incomplete profile: id, name
                    result[self.ids[0]].append((p.id, '%s' % (p.name), reason))
                else:  # unknown partner, we are probably managing an email address
                    result[self.ids[0]].append((False, email, reason))
        return result
