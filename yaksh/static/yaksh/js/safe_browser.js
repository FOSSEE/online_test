/*
 * Safe Browser / Proctoring module
 * -----------------------------------------------------------------------
 * Extracted from question.html so proctoring logic lives in one place.
 *
 * Usage (from the template):
 *
 *   <script src="{% static 'yaksh/js/safe_browser.js' %}"></script>
 *   <script>
 *     window.addEventListener("load", function () {
 *         initSafeBrowser({
 *             safe_browser: {{ quiz.safe_browser|yesno:"true,false" }},
 *             enable_right_click: {{ quiz.enable_right_click|yesno:"true,false" }},
 *             enable_fullscreen: {{ quiz.enable_fullscreen|yesno:"true,false" }},
 *             enable_camera: {{ quiz.enable_camera|yesno:"true,false" }},
 *             enable_microphone: {{ quiz.enable_microphone|yesno:"true,false" }},
 *             enable_tab_switch: {{ quiz.enable_tab_switch|yesno:"true,false" }},
 *             enable_screenshot_detection: {{ quiz.enable_screenshot_detection|yesno:"true,false" }},
 *             paper_id: "{{ paper.id }}",
 *             attempt_number: {{ paper.attempt_number }},
 *             questionpaper_id: {{ paper.question_paper.id }},
 *             csrf_token: "{{ csrf_token }}",
 *             report_violation_url: "{% url 'yaksh:report_violation' %}",
 *             save_student_photo_url: "{% url 'yaksh:save_student_photo' %}",
 *             quit_quiz_url: "{% url 'yaksh:quit_quiz' paper.attempt_number module.id paper.question_paper.id course.id %}"
 *         });
 *     });
 *   </script>
 *
 * Nothing in this file references Django template tags - it is a plain
 * static asset and can be cached/minified normally.
 */

(function (window, document) {
    "use strict";

    var violationCount = 0;
    var MAX_VIOLATIONS = 3;
    var config = null;

    function showNotification(message, type) {
        type = type || "warning";
        var box = document.getElementById("examNotification");
        if (!box) {
            return;
        }
        box.className = "alert alert-" + type + " shadow";
        box.innerHTML = message;
        box.style.display = "block";

        setTimeout(function () {
            box.style.display = "none";
        }, 3000);
    }

    function addViolation(reason) {
        violationCount++;

        showNotification(
            reason + "<br><strong>Violation " +
            violationCount + " of " +
            MAX_VIOLATIONS + "</strong>",
            "danger"
        );

        fetch(config.report_violation_url, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": config.csrf_token
            },
            body: JSON.stringify({
                attempt_number: config.attempt_number,
                questionpaper_id: config.questionpaper_id,
                reason: reason
            })
        })
        .then(function (response) { return response.json(); })
        .then(function (data) {
            if (data.terminated) {
                showNotification(
                    "Maximum violations reached. Ending exam...",
                    "danger"
                );

                setTimeout(function () {
                    window.location.href = config.quit_quiz_url;
                }, 1500);
            }
        });
    }

    function setupRightClickBlock() {
        if (!config.enable_right_click) {
            return;
        }
        document.addEventListener("contextmenu", function (e) {
            e.preventDefault();
        });
    }

    function setupFullscreenWatch() {
        if (!config.enable_fullscreen) {
            return;
        }
        document.addEventListener("fullscreenchange", function () {
            if (!document.fullscreenElement) {
                addViolation("Fullscreen Exited");
            }
        });
    }

    function setupShortcutLock() {
        // Locks browser shortcuts silently while fullscreen is active.
        document.addEventListener("keydown", function (e) {
            if (!document.fullscreenElement) {
                return;
            }

            var key = e.key.toLowerCase();
            var commandKey = e.ctrlKey || e.metaKey;

            var blockedShiftKeys = ["i", "j", "c", "t", "n"];
            if (commandKey && e.shiftKey && blockedShiftKeys.indexOf(key) !== -1) {
                e.preventDefault();
                e.stopPropagation();
                e.stopImmediatePropagation();
                return false;
            }

            var blockedCtrlKeys = [
                "t", "n", "w", "l", "r", "p", "s", "u", "f", "h", "j", "o"
            ];
            if (commandKey && blockedCtrlKeys.indexOf(key) !== -1) {
                e.preventDefault();
                e.stopPropagation();
                e.stopImmediatePropagation();
                return false;
            }

            var blockedFunctionKeys = ["F5", "F11", "F12"];
            if (blockedFunctionKeys.indexOf(e.key) !== -1) {
                e.preventDefault();
                e.stopPropagation();
                e.stopImmediatePropagation();
                return false;
            }

            if (e.altKey && (key === "arrowleft" || key === "arrowright" || key === "home")) {
                e.preventDefault();
                e.stopPropagation();
                e.stopImmediatePropagation();
                return false;
            }
        }, true);
    }

    function setupCameraAndMic() {
        if (!config.enable_camera && !config.enable_microphone) {
            return;
        }

        navigator.mediaDevices.getUserMedia({
            video: config.enable_camera,
            audio: config.enable_microphone
        })
        .then(function (stream) {
            var video = document.getElementById("cameraPreview");
            if (!video) {
                return;
            }
            video.srcObject = stream;

            video.onloadedmetadata = function () {
                video.play();

                var canvas = document.createElement("canvas");
                canvas.width = video.videoWidth;
                canvas.height = video.videoHeight;

                var ctx = canvas.getContext("2d");
                ctx.drawImage(video, 0, 0);

                var image = canvas.toDataURL("image/png");

                var formData = new FormData();
                formData.append("paper_id", config.paper_id);
                formData.append("image", image);
                formData.append("csrfmiddlewaretoken", config.csrf_token);

                fetch(config.save_student_photo_url, {
                    method: "POST",
                    body: formData
                })
                .then(function (res) { return res.json(); })
                .then(function (data) { console.log("Photo Saved:", data); })
                .catch(function (err) { console.error(err); });
            };
        })
        .catch(function () {
            showNotification("Please allow Camera and Microphone.");
        });
    }

    function setupTabSwitchWatch() {
        if (!config.enable_tab_switch) {
            return;
        }
        document.addEventListener("visibilitychange", function () {
            if (document.hidden) {
                addViolation("Tab Switching Detected");
            }
        });

        window.addEventListener("blur", function () {
            addViolation("Window Focus Lost");
        });
    }

    function setupScreenshotDetection() {
        if (!config.enable_screenshot_detection) {
            return;
        }
        document.addEventListener("keydown", function (e) {
            if (e.key === "PrintScreen") {
                addViolation("Screenshot Attempt Detected");
            }
        });
    }

    function requestFullscreen() {
        if (document.fullscreenElement) {
            return Promise.resolve();
        }
        return document.documentElement.requestFullscreen().catch(function () {
            showNotification(
                "Unable to enter fullscreen. Please allow fullscreen and restart the exam.",
                "danger"
            );
            return Promise.reject();
        });
    }

    /**
     * Entry point. Call this once, on window load, with the config object
     * built from Django context in the template.
     *
     * NOTE: this no longer auto-requests fullscreen here, because browsers
     * only grant requestFullscreen() inside a real user gesture (a click).
     * A call made from "load" is silently ignored/rejected by the browser.
     * Use enterFullscreenOnClick() (below) from the Start Quiz button instead.
     */
    function initSafeBrowser(cfg) {
        config = cfg;

        if (!config || !config.safe_browser) {
            return;
        }

        setupRightClickBlock();
        setupFullscreenWatch();
        setupShortcutLock();
        setupTabSwitchWatch();
        setupScreenshotDetection();
        setupCameraAndMic();
    }

    /**
     * Call this directly from the onclick handler of the "Start Quiz"
     * button/link. Because it runs inside the click's call stack, the
     * browser treats it as a genuine user gesture and grants fullscreen.
     *
     * @param {Function} proceedCallback - called after fullscreen is
     *        entered (or immediately, if fullscreen isn't required) so you
     *        can navigate to the quiz / submit the start form.
     */
    function enterFullscreenOnClick(proceedCallback) {
        if (!config || !config.enable_fullscreen) {
            proceedCallback();
            return;
        }

        requestFullscreen()
            .then(proceedCallback)
            .catch(function () {
                // Fullscreen was denied/blocked - still let the user proceed
                // rather than trapping them, since we already warned them.
                proceedCallback();
            });
    }

    // For pages that only need the fullscreen trigger (e.g. the
    // instructions/start page) without wiring up full proctoring.
    function prepareFullscreen(cfg) {
        config = cfg;
    }

    // Expose to global scope for the template to call.
    window.initSafeBrowser = initSafeBrowser;
    window.enterFullscreenOnClick = enterFullscreenOnClick;
    window.prepareFullscreen = prepareFullscreen;

})(window, document);