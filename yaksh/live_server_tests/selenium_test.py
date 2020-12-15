from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import multiprocessing
import argparse


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

    def run_load_test(self, url, username, password):
        try:
            self.driver.delete_all_cookies()
            self.driver.get(self.url)
            self.login(username, password)
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
            self.driver.execute_script("scrollBy(0,-1000);")

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

    def test_python_question(self, question_label):
        # Incorrect Answer
        loop_count = 10
        answer = '\"def is_palindrome(s):\\n    return s\"'
        self.submit_answer(question_label, answer, loop_count)

        # Infinite Loop
        loop_count = 3
        answer = '\"while True:\\n    pass"'
        self.submit_answer(question_label, answer, loop_count)

        # Correct Answer
        loop_count = 1
        answer = '\"def is_palindrome(s):\\n    return s[::-1] == s\"'
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
        answer = '\"#!/bin/bash\\necho Hello, World!\"'
        self.submit_answer(question_label, answer, loop_count)

    def open_quiz(self):
        # open module link
        try:
            self.driver.find_elements_by_partial_link_text(
                'Start')[0].click()
        except IndexError:
            self.driver.find_elements_by_partial_link_text(
                'Continue')[0].click()
        try:
            self.driver.find_element_by_link_text('Start').click()
        except Exception:
            self.driver.find_element_by_link_text('Continue').click()
        # open quiz link
        self.driver.find_element_by_link_text(self.quiz_name).click()

        # Get page elements
        start_exam_elem = WebDriverWait(self.driver, 5).until(
            EC.presence_of_element_located((By.NAME, "start"))
        )
        start_exam_elem.click()

        self.test_c_question(question_label=6)
        self.test_python_question(question_label=4)
        self.test_bash_question(question_label=10)

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
