import hashlib
import hmac


SEB_CONFIG_KEY_HEADER = "HTTP_X_SAFEEXAMBROWSER_CONFIGKEYHASH"


def get_seb_settings(quiz):
    return getattr(quiz, 'seb', None)

def is_quiz_without_seb(request, quiz):
    seb = get_seb_settings(quiz)

    if seb:
        if seb.enabled:
            return False

    return True


def is_valid_seb_request(request, quiz):
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    if 'SafeExamBrowser' not in user_agent and 'SEB' not in user_agent:
        msg = ('This quiz requires Safe Exam Browser.'
              'Please launch the quiz using the provided .seb configuration file.')
        return False, msg
    seb = get_seb_settings(quiz)
    if seb:
        config_key_header = request.META.get(SEB_CONFIG_KEY_HEADER, '')
        requested_url = request.build_absolute_uri()

        if seb.config_key:
            expected_hash = hashlib.sha256(
                (requested_url + seb.config_key).encode('utf-8')).hexdigest() 
            if not hmac.compare_digest(config_key_header.lower(), expected_hash.lower()):
                msg = ('Safe Exam Browser configuration mismatch.'
                       'Please use the exact .seb file provided by your instructor.')
                return False, msg
        else:
            return False, 'No key found, contact instructor'
    else:
        return False, 'No SEB found.'
    return True, 'Vaild'


def require_seb_for_answerpaper(request, answerpaper):

    quiz = answerpaper.question_paper.quiz
    seb = get_seb_settings(quiz)
    if seb and seb.enabled:
        if not is_quiz_without_seb(request, quiz):
            valid, msg = is_valid_seb_request(request, quiz)
            if valid:
                return True, 'Valid'
            else:
                return False, 'SEB required. '
    return True, 'Not required'


def set_answerpaper_seb_verified(request, answerpaper):
    quiz = answerpaper.question_paper.quiz
    seb = get_seb_settings(quiz)
    if not seb:
        return None, 'Valid'

    if not seb.enabled:
       return None, 'Valid'

    if not is_valid_seb_request(request, quiz):
        return False, 'Please open the quiz using Safe Exam Browser'

    answerpaper.seb_verified = True
    answerpaper.seb_config_key = request.META.get(SEB_CONFIG_KEY_HEADER, '')
    answerpaper.seb_user_agent = request.META.get('HTTP_USER_AGENT', '')
    answerpaper.save(update_fields=['seb_verified', 'seb_config_key',
                                    'seb_user_agent'])
    return True, 'Valid'
