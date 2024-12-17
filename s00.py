import requests
import logging
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from threading import Thread

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# API 配置
DATA_API_URL = "https://s00reg.64t76dee9sk5.workers.dev/api"
NOTIFICATION_API_URL = "https://api.day.app/Y6wZN8swvDrno2URYa5CDZ/"

# 初始化 WebDriver 配置
def init_webdriver(user_agent):
    options = webdriver.ChromeOptions()
    options.add_argument(f"user-agent={user_agent}")
    options.add_argument("--incognito")
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    return webdriver.Chrome(options=options)

# 获取用户数据
def fetch_user_data():
    while True:
        try:
            response = requests.get(DATA_API_URL)
            response.raise_for_status()
            data = response.json()
            return data['url'], data['user'], data['userAgent']
        except Exception as e:
            logging.error(f"获取用户数据失败，重试中: {e}")
            time.sleep(2)

# 预加载下一次注册数据
def preload_user_data(preloaded_data):
    try:
        preloaded_data['data'] = fetch_user_data()
    except Exception as e:
        logging.error(f"预加载用户数据失败: {e}")

# 填写表单
def fill_form(driver, user):
    wait = WebDriverWait(driver, 10)
    try:
        wait.until(EC.presence_of_element_located((By.ID, "id_first_name"))).send_keys(user['firstName'])
        wait.until(EC.presence_of_element_located((By.ID, "id_last_name"))).send_keys(user['lastName'])
        wait.until(EC.presence_of_element_located((By.ID, "id_username"))).send_keys(user['username'])
        wait.until(EC.presence_of_element_located((By.ID, "id_email"))).send_keys(user['email'])
        wait.until(EC.presence_of_element_located((By.ID, "id_question"))).send_keys("1000")

        # 勾选服务条款
        tos_checkbox = wait.until(EC.element_to_be_clickable((By.ID, "id_tos")))
        if not tos_checkbox.is_selected():
            tos_checkbox.click()

        logging.info(f"{user['firstName']} {user['lastName']}, {user['username']}, {user['email']}, 1000, 服务条款已勾选")
    except Exception as e:
        logging.error(f"填写表单失败: {e}")
        return False
    return True

# 解决验证码
def solve_captcha(image_path):
    api_url = "https://ocrapi.gits.one/?ocr"
    headers = {'Authorization': 'Bearer fivl7VyjCAYWmUgWj1psGfxz71aqFHmOFSsdWdyEjipSWiQZUXzc0E039PQszBzu'}
    while True:
        try:
            with open(image_path, 'rb') as image_file:
                response = requests.post(api_url, headers=headers, files={'image': image_file})
                response.raise_for_status()
                result = response.json()
                if result['success']:
                    captcha_code = result['result']
                    logging.info(f"验证码识别成功: {captcha_code}")
                    return captcha_code
                else:
                    logging.warning("验证码识别失败，重试中")
        except Exception as e:
            logging.error(f"OCR API 调用失败，重试中: {e}")
        time.sleep(2)

# 等待注册结果并处理验证码
def wait_for_result(driver, attempt_number):
    start_time = time.time()
    captcha_filled = False

    while time.time() - start_time < 60:
        try:
            # 检查是否有注册成功的通知
            success_notification = driver.find_element(By.CSS_SELECTOR, ".notification.is-success")
            if success_notification.is_displayed():
                logging.info(f"第 {attempt_number} 次注册成功！")
                logging.info(success_notification.text)
                return True
        except:
            pass

        try:
            # 检查是否有注册失败的错误信息
            error_message = driver.find_element(By.CSS_SELECTOR, ".error_message")
            if error_message.is_displayed():
                logging.error(f"注册失败: {error_message.text}\n\n")
                return False
        except:
            pass

        try:
            # 检查是否有验证码
            captcha_image = driver.find_element(By.CSS_SELECTOR, ".captcha")
            if not captcha_filled and captcha_image.is_displayed():
                captcha_image_path = "/tmp/captcha_image.png"
                with open(captcha_image_path, 'wb') as file:
                    file.write(captcha_image.screenshot_as_png)
                
                captcha_code = solve_captcha(captcha_image_path)
                if captcha_code:
                    driver.find_element(By.ID, "id_captcha_1").send_keys(captcha_code)
                    driver.find_element(By.CSS_SELECTOR, ".button.is-primary").click()
                    captcha_filled = True
        except:
            pass

        time.sleep(0.5)

    logging.warning(f"第 {attempt_number} 次注册超时，未检测到成功或失败的提示")
    return False

# 发送注册成功通知
def send_success_notification(username):
    try:
        response = requests.get(f"{NOTIFICATION_API_URL}{username}@proton.me")
        response.raise_for_status()
        logging.info(f"注册成功通知发送完成: {username}@proton.me")
    except Exception as e:
        logging.error(f"发送注册成功通知失败: {e}")

# 主流程
def main():
    preloaded_data = {'data': None}
    attempt_number = 0

    # 异步预加载下一次数据
    preload_thread = Thread(target=preload_user_data, args=(preloaded_data,))
    preload_thread.start()

    driver = None
    try:
        while True:
            attempt_number += 1
            logging.info(f"开始第 {attempt_number} 次注册 Serv00")

            try:
                # 如果预加载数据已完成，使用预加载数据；否则直接获取
                if preloaded_data['data']:
                    registration_url, user, user_agent = preloaded_data['data']
                    preload_thread = Thread(target=preload_user_data, args=(preloaded_data,))
                    preload_thread.start()
                else:
                    registration_url, user, user_agent = fetch_user_data()

                # 初始化 WebDriver（只在第一次初始化）
                if not driver:
                    driver = init_webdriver(user_agent)

                # 访问注册页面
                driver.get(registration_url)

                # 填写表单
                fill_form(driver, user)

                # 验证注册结果
                if wait_for_result(driver, attempt_number):
                    logging.info(f"第 {attempt_number} 次注册成功！邮箱: {user['email']}")
                    send_success_notification(user['username'])
                

            except Exception as e:
                logging.error(f"第 {attempt_number} 次注册发生错误: {e}，重新尝试...")

    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    main()
