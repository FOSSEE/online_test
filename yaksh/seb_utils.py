import hashlib
import plistlib
from django.urls import reverse

def check_seb_access(request, quiz, module_id, course_id):
    """
    Checks if the current request satisfies Safe Exam Browser requirements for the given quiz.
    Returns (True, None) if successful, (False, error_message) if it fails.
    """
    if not quiz.is_seb_required:
        return True, None

    user_agent = request.META.get('HTTP_USER_AGENT', '')
    if 'SEB' not in user_agent:
        return False, 'This quiz requires Safe Exam Browser. Please launch the quiz using the provided .seb configuration file.'

    seb_hash_header = request.META.get('HTTP_X_SAFEEXAMBROWSER_CONFIGKEYHASH')
    if not seb_hash_header:
        return False, 'This quiz requires Safe Exam Browser. Please launch the quiz using the provided .seb configuration file.'

    requested_url = request.build_absolute_uri()
    
    if quiz.seb_settings:
        # Dynamic SEB Config validation
        questionpaper = quiz.questionpaper_set.first()
        if not questionpaper:
            # Cannot validate dynamic hash without a question paper to form startURL
            return True, None
            
        start_url = request.build_absolute_uri(
            reverse('yaksh:start_quiz', args=[questionpaper.id, module_id, course_id])
        )
        settings = quiz.seb_settings
        config = {
            'startURL': start_url,
            'sebMode': 0, 
            'browserViewMode': 1 if settings.get('seb_use_fullscreen') else 0,
            'enableZoomPage': bool(settings.get('seb_enable_zoom')),
            'enableZoomText': bool(settings.get('seb_enable_zoom')),
            'showReloadButton': bool(settings.get('seb_show_reload')),
            'showTime': bool(settings.get('seb_show_time')),
            'showKeyboardLayout': bool(settings.get('seb_show_keyboard')),
        }
        plist_bytes = plistlib.dumps(config, fmt=plistlib.FMT_XML)
        config_key = hashlib.sha256(plist_bytes).hexdigest()
        expected_hash = hashlib.sha256((requested_url + config_key).encode('utf-8')).hexdigest()
    elif quiz.seb_config_key:
        # Static SEB Config validation
        expected_hash = hashlib.sha256((requested_url + quiz.seb_config_key).encode('utf-8')).hexdigest()
    else:
        # If SEB is required but no settings or key provided, we can't validate hash
        # But we still enforce SEB User-Agent, which is already checked
        return True, None

    if seb_hash_header.lower() != expected_hash.lower():
        return False, 'Safe Exam Browser configuration mismatch. Please use the exact .seb file provided by your instructor.'

    return True, None
