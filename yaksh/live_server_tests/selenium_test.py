from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC

import multiprocessing
import argparse

from time import sleep
from yaksh.models import Question, StandardTestCase

import json

from django.conf import settings
import os

TEST_DIR = os.path.join(settings.BASE_DIR, 'yaksh', 'tests')


class ElementDisplay(object):
    '''Custom expected condition '''

    def __init__(self, locator):
        self.locator = locator

    def __call__(self, driver):
        try:
            element = EC._find_element(driver, self.locator)
            return element.value_of_css_property("display") == "none"
        except Exception:
            return False


class SeleniumTestError(Exception):
    pass


class SeleniumTest():
    def __init__(self, url, quiz_name, module_name, course_name):
        self.driver = webdriver.Firefox()
        self.driver.set_window_position(0, 0)
        self.driver.set_window_size(1024, 768)
        self.quiz_name = quiz_name
        self.module_name = module_name
        self.course_name = course_name
        self.url = url

    def run_load_test(self, url):
        try:
            self.driver.delete_all_cookies()
            self.driver.get(self.url)

            # Moderator side testing
            self.login("demo_mod", "demo_mod")
            self.open_questions()
            self.open_courses()
            self.open_modules()
            self.add_course()
            self.design_course()
            self.add_lesson()
            self.switch_to_student()
            self.search_course("123")
            self.enroll()
            self.switch_to_moderator()
            self.open_course_detail()
            if(self.check_enroll("demo_mod")):
                print("Student enrolled")
            else:
                print("Student not enrolled")
            self.logout()
            self.go_to_home()

            # Student side testing
            self.login("demo_student", "demo_student")
            self.search_course("123")
            self.enroll()
            self.search_course("123")
            self.open_quiz()
            self.quit_quiz()
            self.close_quiz()
            self.logout()
            self.driver.close()
        except Exception as e:
            self.driver.close()
            msg = ("An Error occurred while running the Selenium load"
                   " test on Yaksh!\n"
                   "Error:\n{0}".format(e))

            raise SeleniumTestError(msg)

    def login(self, username, password):
        # get the username, password and submit form elements
        username_elem = self.driver.find_element_by_id("id_username")
        password_elem = self.driver.find_element_by_id("id_password")
        submit_login_elem = self.driver.find_element_by_css_selector(
            'button.btn')

        # Type in the username, password and submit form
        username_elem.send_keys(username)
        password_elem.send_keys(password)
        submit_login_elem.click()

    def quit_quiz(self):
        quit_link_elem = WebDriverWait(self.driver, 5).until(
            EC.presence_of_element_located((By.NAME, "quit"))
        )
        quit_link_elem.click()

        quit_link_elem = WebDriverWait(self.driver, 5).until(
            EC.presence_of_element_located((By.NAME, "yes"))
        )
        quit_link_elem.click()

    def close_quiz(self):
        quit_link_elem = WebDriverWait(self.driver, 5).until(
            EC.presence_of_element_located((By.ID, "Next"))
        )
        quit_link_elem.click()

    def open_quiz(self):
        # open module link
        self.driver.find_element_by_id("id_start").click()
        WebDriverWait(self.driver, 5).until(
            EC.presence_of_element_located((By.ID, "id_start"))
        ).click()
        # open quiz link
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.LINK_TEXT, self.quiz_name))
        ).click()

        # Get page elements
        start_exam_elem = WebDriverWait(self.driver, 5).until(
            EC.presence_of_element_located((By.NAME, "start"))
        )
        start_exam_elem.click()

        self.test_python_question(question_label=1)
        self.test_bash_question(question_label=2)
        self.test_c_question(question_label=3)

    def test_c_question(self, question_label):
        # Incorrect Answer
        loop_count = 10
        answer = '\"int add(int a, int b, int c)\\n{return;}\"'
        self.submit_answer(question_label, answer, loop_count)

        # Infinite Loop
        loop_count = 3
        answer = '\"int add(int a, int b, int c)\\n{while(1){}}\"'
        self.submit_answer(question_label, answer, loop_count)

        # Correct Answer
        loop_count = 1
        answer = '\"int add(int a, int b, int c)\\n{return a + b + c;}\"'
        self.submit_answer(question_label, answer, loop_count)

    def test_bash_question(self, question_label):
        # Incorrect Answer
        loop_count = 10
        answer = '\"#!/bin/bash\\nls\"'
        self.submit_answer(question_label, answer, loop_count)

        # Infinite Loop
        loop_count = 3
        answer = '\"#!/bin/bash\\nwhile [ 1 ]; do : ; done\"'
        self.submit_answer(question_label, answer, loop_count)

        # Correct Answer
        loop_count = 1
        answer = '\"#!/bin/bash\\n[[ $# -eq 2 ]] && echo $(( $1 + $2 )) \
            && exit $(( $1 + $2 ))\"'
        self.submit_answer(question_label, answer, loop_count)

    def test_python_question(self, question_label):
        # Incorrect Answer
        loop_count = 5
        answer = '\"def is_palindrome(s):\\n    return s\"'
        self.submit_answer(question_label, answer, loop_count)

        # Infinite Loop
        loop_count = 3
        answer = '\"while True:\\n    pass"'
        self.submit_answer(question_label, answer, loop_count)

        # Correct Answer
        loop_count = 1
        answer = '\"def is_palindrome(s):\\n    return s == s[::-1]\"'
        self.submit_answer(question_label, answer, loop_count)

    def submit_answer(self, question_label, answer, loop_count=1):
        self.driver.implicitly_wait(2)
        for count in range(loop_count):
            self.driver.find_element_by_link_text(question_label).click()
            submit_answer_elem = self.driver.find_element_by_id("check")
            self.driver.execute_script(
                'global_editor.editor.setValue({});'.format(answer))
            submit_answer_elem.click()
            WebDriverWait(self.driver, 90).until(ElementDisplay(
                (By.XPATH, "//*[@id='ontop']")))

    def go_to_home(self):
        # Go back to home
        WebDriverWait(self.driver, 5).until(
            EC.presence_of_element_located((By.ID, "home"))
        ).click()

    def open_questions(self):
        # Open questions page
        self.driver.find_element_by_id("id_questions").click()

        test_file = open(os.path.join(TEST_DIR, 'test_questions.json'), 'r')
        test_questions = json.loads(test_file.read())
        test_file.close()

        for (id, test_question) in enumerate(test_questions, start=1):
            question = self.get_demo_question(test_question, id)
            self.add_question(question=question)

            # Go back to questions page
            self.driver.find_element_by_name(
                "button"
            ).click()

    def add_question(self, question):
        # Click add question button
        self.driver.find_element_by_id("id_add_question").click()

        # Fill question summary
        summary = self.driver.find_element_by_id("id_summary")
        summary.send_keys(question.summary)

        # Select language
        self.drp_select("id_language", question.language)

        # Select type
        self.drp_select("id_type", question.type)

        # Set points
        points = self.driver.find_element_by_id("id_points")
        points.clear()
        points.send_keys(str(question.points))

        # Fill description
        self.set_description(question.description)

        # Fill snippet
        snippet = self.driver.find_element_by_id("id_snippet")
        snippet.send_keys(question.snippet)

        # Set Minimum Time
        min_time = self.driver.find_element_by_id("id_min_time")
        min_time.send_keys(question.min_time)

        for (id, test_case) in enumerate(question.testcase):
            # Select testcase type
            self.drp_select("case_type", test_case.type)

            # Add testcase
            summary = self.driver.find_element_by_id(
                "id_{0}_set-{1}-test_case".format(test_case.type, str(id)))
            summary.send_keys(test_case.test_case)


        # Save question
        self.driver.find_element_by_name(
            "save_question"
        ).click()

    def open_courses(self):
        # Open courses page
        self.driver.find_element_by_id("id_courses").click()
        self.open_quizzes()

    def open_quizzes(self):
        # Open all quizes page
        self.driver.find_element_by_id("id_add_quiz").click()

        # Create list of questions to add
        questions = []
        test_file = open(os.path.join(TEST_DIR, 'test_questions.json'), 'r')
        test_questions = json.loads(test_file.read())
        test_file.close()

        for (id, test_question) in enumerate(test_questions, start=1):
            question = self.get_demo_question(test_question, id)
            questions.append(question)

        self.add_quiz(questions)

    def add_quiz(self, questions):
        # Click add new quiz button
        self.driver.find_element_by_id("id_add_new_quiz").click()

        # Fill description
        self.set_description("demo_quiz")

        # Click submit button
        self.submit()

        # Click add button to add questions to the quiz
        self.driver.find_element_by_id("id_add_paper").click()

        for question in questions:
            # Select question type
            self.drp_select("id_question_type", question.type)

            # Select marks
            self.drp_select("id_marks", str(question.points))

            # Check the selected question
            link = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//input[@value='{}']".format(question.id))))
            link.click()

            # Add the selected questions
            self.driver.find_element_by_id("add-fixed").click()

        # Click next
        self.driver.find_element_by_id("fixed-next").click()

        # Click random next
        self.driver.find_element_by_id("random-next").click()

        # Save question paper
        self.driver.find_element_by_id("save").click()

    def open_modules(self):
        # Open all modules page
        self.driver.find_element_by_id("id_add_module").click()
        self.add_module()

    def add_module(self):
        # Click add new module button
        self.driver.find_element_by_id("id_add_new_module").click()

        # Fill name
        self.set_name("demo_module")

        # Fill description
        self.set_description("demo_description")

        # Save
        self.submit()

        # Add quizzes to module
        self.driver.find_element_by_partial_link_text(
            "Add Quizzes/Lessons for").click()
        quiz_check_box = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH,
                 "//*[@id='fixed-available']/ul/li[last()]/label/input")
            )
        )
        quiz_check_box.click()
        self.submit()

        # Get back to modules page
        self.driver.find_element_by_id(
            "id_back_to_modules").click()

    def add_course(self):
        # Open add new course page
        self.driver.find_element_by_id("id_add_course").click()

        # Fill name
        self.set_name(self.course_name)

        # Select enrollment type
        self.drp_select("id_enrollment", "open")

        # Enter code
        code = self.driver.find_element_by_id("id_code")
        code.send_keys("123")

        # Select grading system
        self.drp_select("id_grading_system", "1")

        # Save course
        self.submit()

    def design_course(self):
        # Open design course section
        self.driver.find_element_by_id("id_design_course").click()

        # Select module to add to the course
        module_check_box = WebDriverWait(
            self.driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH,
                 "//*[@id='course-details']/tbody/tr[last()]/td[1]/input")))
        module_check_box.click()

        # Add the selected module to the course
        self.driver.find_element_by_id("Add").click()

        # Get back to the courses page
        self.driver.find_element_by_id("id_back_to_courses").click()

    def add_lesson(self):
        # Open lessons page
        self.driver.find_element_by_id("id_add_lesson").click()

        # Click add new lesson button
        self.driver.find_element_by_id("id_add_new_lesson").click()

        # Fill name
        self.set_name("demo_lesson")

        # Fill description
        self.set_description("demo_description")

        # Save
        self.submit()

        # Open all courses page
        self.driver.find_element_by_id("id_view_courses").click()

        # Open design learning module page
        self.driver.find_element_by_partial_link_text(
            "Add Quizzes/Lessons for").click()

        # Add lesson to module
        lesson_check_box = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH,
                 "//*[@id='fixed-available']/ul/li[last()]/label/input")
            )
        )
        lesson_check_box.click()
        self.submit()

        # Get back to courses page
        self.driver.find_element_by_id(
            "id_back_to_modules").click()

    def switch_to_student(self):
        # Switch to student
        self.driver.find_element_by_id("user_dropdown").click()
        self.driver.find_element_by_id("switch_to_student").click()

    def search_course(self, course_code):
        # Search the course
        search_box = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.NAME, "course_code"))
        )
        search_box.send_keys(course_code)
        self.driver.find_element_by_id("id_search").click()

    def enroll(self):
        # Click enroll
        self.driver.find_element_by_id("id_enroll").click()

    def switch_to_moderator(self):
        # Switch to moderator
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, "user_dropdown"))
        ).click()
        self.driver.find_element_by_id("switch_to_moderator").click()

    def open_course_detail(self):
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.LINK_TEXT, self.course_name))
        ).click()

    def check_enroll(self, username):
        # Check whether the student is enrolled or not
        user = WebDriverWait(
            self.driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, "//*[@id='enrolled_table']/tbody/tr/td[3]")))
        return (user.text.lower().strip() == username)

    def submit(self):
        self.driver.find_element_by_id("submit").click()

    def set_name(self, name):
        drp_name = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, "id_name"))
        )
        drp_name.send_keys(name)

    def set_description(self, description):
        drp_description = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, "id_description"))
        )
        drp_description.send_keys(description)

    def drp_select(self, id, value):
        drp_grading_system = Select(self.driver.find_element_by_id(id))
        drp_grading_system.select_by_value(value)

    def get_demo_question(self, test_question, id):
        testcases = []
        for testcase in test_question["testcase"]:
            testcases.append(
                StandardTestCase(
                    test_case=testcase["test_case"],
                    type=test_question["test_case_type"]))
        question = Question(
            id=id,
            summary=test_question["summary"],
            description=test_question["description"],
            points=test_question["points"],
            language=test_question["language"],
            type=test_question["type"],
            snippet=test_question["snippet"],
            testcase=testcases,
            min_time=2,
        )
        return question

    def logout(self):
        logout_link_menu = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, "user_dropdown"))
        )
        logout_link_menu.click()
        logout_link_elem = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, "user_logout"))
        )
        logout_link_elem.click()


def user_gen(url, ids):
    return [(url, 'User%d' % x, 'User%d' % x) for x in ids]


def wrap_run_load_test(args):
    url = "http://yaksh.fossee.aero.iitb.ac.in/exam/"
    selenium_test = SeleniumTest(url=url, quiz_name=quiz_name)
    return selenium_test.run_load_test(*args)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'url', type=str, help="url of the website being tested"
    )
    parser.add_argument('start', type=int, help="Starting user id")
    parser.add_argument(
        "-n", "--number", type=int, default=10, help="number of users"
    )
    opts = parser.parse_args()

    quiz_name = "Demo quiz"
    module_name = "Demo Module"
    course_name = "Yaksh Demo course"
    selenium_test = SeleniumTest(url=opts.url, quiz_name=quiz_name,
                                 module_name=module_name,
                                 course_name=course_name)
    pool = multiprocessing.Pool(opts.number)
    pool.map(
        wrap_run_load_test,
        user_gen(opts.url, range(opts.start, opts.start + opts.number))
    )
    pool.close()
    pool.join()
