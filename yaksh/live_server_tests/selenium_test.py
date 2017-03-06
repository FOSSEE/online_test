from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException

import multiprocessing
import argparse

class SeleniumTestError(Exception):
    pass

class SeleniumTest():
    def __init__(self, url, quiz_name):
        self.driver = webdriver.Firefox()
        self.quiz_name = quiz_name
        self.url = url

    def run_load_test(self, url, username, password):
        try:
            self.driver.delete_all_cookies()
            self.driver.get(self.url)
            self.login(username, password)
            self.open_quiz()
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
        submit_login_elem = self.driver.find_element_by_css_selector('button.btn')

        # Type in the username, password and submit form
        username_elem.send_keys(username)
        password_elem.send_keys(password)
        submit_login_elem.click()

    def submit_answer(self, question_label, answer, loop_count=1):
        self.driver.implicitly_wait(2)
        for count in range(loop_count):
            self.driver.find_element_by_link_text(question_label).click()
            submit_answer_elem = self.driver.find_element_by_id("check")
            self.driver.execute_script('global_editor.editor.setValue({});'.format(answer))
            submit_answer_elem.click()

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
        answer = '\"#!/bin/bash\\ncat $1 | cut -d: -f2 | paste -d: $3 - $2\"'
        self.submit_answer(question_label, answer, loop_count)

    def open_quiz(self):
        # open quiz link
        quiz_link_elem = self.driver.find_element_by_link_text(self.quiz_name).click()
     
        # Get page elements
        start_exam_elem = WebDriverWait(self.driver, 5).until(
            EC.presence_of_element_located((By.NAME, "start"))
        )
        start_exam_elem.click()

        self.test_c_question(question_label=2)
        self.test_python_question(question_label=3)
        self.test_bash_question(question_label=1)

    def close_quiz(self):
        quit_link_elem = WebDriverWait(self.driver, 5).until(
            EC.presence_of_element_located((By.ID, "home"))
        )
        quit_link_elem.click()

    def logout(self):
        logout_link_elem = WebDriverWait(self.driver, 5).until(
            EC.presence_of_element_located((By.ID, "logout"))
        )
        logout_link_elem.click()

def user_gen(url, ids):
    return [(url, 'User%d'%x, 'User%d'%x) for x in ids]

def wrap_run_load_test(args):
    url = "http://yaksh.fossee.aero.iitb.ac.in/exam/"
    selenium_test = SeleniumTest(url=url, quiz_name=quiz_name)
    return selenium_test.run_load_test(*args)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('url', type=str, help="url of the website being tested")
    parser.add_argument('start', type=int, help="Starting user id")
    parser.add_argument("-n", "--number", type=int, default=10, help="number of users")
    opts = parser.parse_args()

    quiz_name = "Demo quiz"
    selenium_test = SeleniumTest(url=opts.url, quiz_name=quiz_name)
    pool = multiprocessing.Pool(opts.number)
    pool.map(wrap_run_load_test, user_gen(opts.url, range(opts.start, opts.start + opts.number)))
    pool.close()
    pool.join()

